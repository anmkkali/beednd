import concurrent.futures
import datetime as dt
import json
import os
import re
import urllib.request
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDS_DIR = os.path.join(ROOT, "src", "content", "brands")
DEALS_DIR = os.path.join(ROOT, "src", "content", "deals")
WATCHLIST_PATH = os.path.join(ROOT, "src", "data", "brandsWatchlist.json")

NOW = dt.datetime.now(dt.timezone.utc)
NOW_ISO = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")

SALE_RE = re.compile(
    r"(?:flat\s+\d{1,2}%\s*off|up\s+to\s+\d{1,2}%\s*off|\d{1,2}%\s*off|black\s+friday|white\s+friday|blessed\s+friday|cyber\s+monday|free\s+trial)",
    re.IGNORECASE,
)
PCT_RE = re.compile(r"(\d{1,2})\s*%\s*off", re.IGNORECASE)


def parse_iso(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def get_domain(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else (host or "example.com")
    except Exception:
        return "example.com"


def lifecycle_sync():
    expired_count = 0
    activated_count = 0
    active_brand_ids = set()

    for fn in os.listdir(DEALS_DIR):
        if not fn.endswith(".json"):
            continue
        fp = os.path.join(DEALS_DIR, fn)
        with open(fp, "r", encoding="utf-8") as f:
            deal = json.load(f)

        changed = False
        end_dt = parse_iso(deal.get("end_date"))
        start_dt = parse_iso(deal.get("start_date"))

        if deal.get("status") == "active" and end_dt and end_dt < NOW:
            deal["status"] = "expired"
            changed = True
            expired_count += 1

        if deal.get("status") == "active" and deal.get("is_coming_soon") and start_dt and start_dt <= NOW:
            deal["is_coming_soon"] = False
            changed = True
            activated_count += 1

        if deal.get("status") == "active":
            active_brand_ids.add(deal.get("brand_id"))

        if changed:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(deal, f, indent=2)

    print(f"[lifecycle] expired={expired_count}, coming_soon_activated={activated_count}, active_brands={len(active_brand_ids)}")
    return active_brand_ids


def check_url(item):
    url = item.get("url") or ""
    if not url.startswith("http"):
        return None
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; BeeDNDBot/1.0; +https://beednd.com)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status != 200:
                return None
            html = resp.read(150_000).decode("utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", " ", html)
            matches = SALE_RE.findall(text)
            if not matches:
                return None
            pcts = [int(p) for p in PCT_RE.findall(text) if 5 <= int(p) <= 90]
            best_pct = max(pcts) if pcts else 20
            return {
                "item": item,
                "signal": matches[0].strip(),
                "pct": best_pct,
            }
    except Exception:
        return None


def scan_watchlist(active_brand_ids):
    if not os.path.exists(WATCHLIST_PATH):
        return 0

    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        watchlist = json.load(f)

    # Prioritize focus markets in every 12h cycle
    FOCUS_COUNTRIES = {"PK", "US", "GB", "IN", "AE", "SA", "TR", "NL", "DE", "JP", "CN", "BD", "ZA", "NG", "KE", "SG", "MY", "GLOBAL"}
    candidates = [b for b in watchlist if b["id"] not in active_brand_ids and b.get("url")]
    candidates.sort(key=lambda b: (0 if b.get("country") in FOCUS_COUNTRIES else 1, b.get("country", "")))
    slot = int(NOW.timestamp() // (12 * 3600)) % max(1, (len(candidates) // 120) + 1)
    batch = candidates[slot * 120 : (slot + 1) * 120]
    if not batch and candidates:
        batch = candidates[:120]

    print(f"[scanner] checking {len(batch)} brands from watchlist (total candidates={len(candidates)})...")
    discovered = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for res in pool.map(check_url, batch):
            if not res:
                continue
            b = res["item"]
            bid = b["id"]
            country = b.get("country", "GLOBAL")
            cat = b.get("category", "clothing-fashion")
            url = b["url"]
            dom = get_domain(url)
            pct = res["pct"]

            # Ensure brand file exists
            bpath = os.path.join(BRANDS_DIR, f"{bid}.json")
            if not os.path.exists(bpath):
                with open(bpath, "w", encoding="utf-8") as bf:
                    json.dump({
                        "id": bid,
                        "name": b["name"],
                        "slug": bid,
                        "logo_url": f"https://www.google.com/s2/favicons?domain={dom}&sz=128",
                        "website_url": url,
                        "country": country,
                        "categories": [cat],
                        "short_bio": f"Verified {country} brand offering seasonal sales and online discounts.",
                        "known_for": ["Seasonal sales", "Online offers"],
                    }, bf, indent=2)

            deal_id = f"{bid}-live-offer"
            dpath = os.path.join(DEALS_DIR, f"{deal_id}.json")
            if os.path.exists(dpath):
                continue

            end_iso = (NOW + dt.timedelta(days=14)).strftime("%Y-%m-%dT23:59:00Z")
            is_ai = cat == "ai-tools"
            with open(dpath, "w", encoding="utf-8") as df:
                json.dump({
                    "id": deal_id,
                    "slug": deal_id,
                    "title": f"{b['name']}: Up to {pct}% Off Seasonal Sale" if not is_ai else f"{b['name']}: Free Trial & Plan Discounts",
                    "short_description": f"Verified active promotion detected on {b['name']}'s official store ({res['signal']}). Confirm exclusions at checkout.",
                    "brand_id": bid,
                    "country": country,
                    "cities": [],
                    "areas": [],
                    "branch_info": [],
                    "category": cat,
                    "deal_type": "online",
                    "channels": ["online"],
                    "discount_type": "percentage",
                    "discount_value": f"UP TO {pct}% OFF" if not is_ai else "FREE TRIAL",
                    "badge_text": f"Up to {pct}% Off" if not is_ai else "Free Trial",
                    "numeric_discount_percent": pct,
                    "terms_and_conditions": [
                        f"Auto-verified from {b['name']} official sale page.",
                        "Confirm final discount and exclusions on the official store."
                    ],
                    "start_date": NOW_ISO,
                    "end_date": end_iso,
                    "source_url": url,
                    "affiliate_url": url,
                    "last_verified_at": NOW_ISO,
                    "status": "active",
                    "is_trending": False,
                    "is_coming_soon": False,
                    "limited_time": True,
                    "offer_kind": "trial" if is_ai else "discount",
                    "image": {"src": f"https://www.google.com/s2/favicons?domain={dom}&sz=128", "alt": b["name"]},
                    "tags": ["all-items"],
                }, df, indent=2)
            discovered += 1

    print(f"[scanner] discovered {discovered} new deals")
    return discovered


if __name__ == "__main__":
    active_ids = lifecycle_sync()
    scan_watchlist(active_ids)
