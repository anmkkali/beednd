import concurrent.futures
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDS_DIR = os.path.join(ROOT, "src", "content", "brands")
DEALS_DIR = os.path.join(ROOT, "src", "content", "deals")
WATCHLIST_PATH = os.path.join(ROOT, "src", "data", "brandsWatchlist.json")

NOW = dt.datetime.now(dt.timezone.utc)
NOW_ISO = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")

SALE_RE = re.compile(
    r"(?:flat\s+\d{1,2}%\s*(?:off|discount)?|up\s+to\s+\d{1,2}%\s*(?:off|discount)?|save\s+(?:up\s+to\s+)?\d{1,2}%|\d{1,2}%\s*(?:off|discount)|black\s+friday|white\s+friday|blessed\s+friday|cyber\s+monday|winter\s+sale|summer\s+sale|mega\s+sale|flash\s+sale|end\s+of\s+season\s+sale|clearance\s+sale|free\s+trial|promo\s+code)",
    re.IGNORECASE,
)
PCT_RE = re.compile(r"(?:(?:flat|up\s+to|save)\s+(\d{1,2})\s*%|\b(\d{1,2})\s*%\s*(?:off|discount))", re.IGNORECASE)


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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=7) as resp:
            if resp.status != 200:
                return {"item": item, "state": "ended"} if resp.status in (404, 410) else None
            html = resp.read(160_000).decode("utf-8", errors="ignore")
            html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
            matches = SALE_RE.findall(text)
            if not matches:
                return {"item": item, "state": "ended"}
            top_text = text[:4000]
            pcts = [int(p or q) for p, q in PCT_RE.findall(top_text) if 5 <= int(p or q) <= 85]
            if not pcts:
                pcts = [int(p or q) for p, q in PCT_RE.findall(text) if 5 <= int(p or q) <= 85]
            best_pct = max(pcts) if pcts else None
            sig = re.sub(r"\s+", " ", matches[0]).strip()
            is_flat = bool(re.search(r"\bflat\b", top_text, re.I))
            return {
                "item": item,
                "state": "live",
                "signal": sig,
                "pct": best_pct,
                "is_flat": is_flat,
            }
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return {"item": item, "state": "ended"}
        return None
    except Exception:
        return None


def format_offer_copy(name, cat, pct, is_flat):
    is_ai = cat == "ai-tools"
    if is_ai:
        return (
            f"{name}: Free Trial & Plan Discounts",
            "FREE TRIAL",
            "Free Trial",
            pct or 0,
            "trial",
        )
    if pct:
        prefix = "Flat" if is_flat else "Up to"
        return (
            f"{name}: {prefix} {pct}% Off Sale",
            f"{prefix.upper()} {pct}% OFF",
            f"{prefix} {pct}% Off",
            pct,
            "discount",
        )
    return (
        f"{name}: Seasonal Sale & Offers",
        "SEASONAL SALE",
        "Sale Live",
        0,
        "discount",
    )


def reverify_live_offers():
    live_items = []
    for fn in os.listdir(DEALS_DIR):
        if not fn.endswith("-live-offer.json"):
            continue
        fp = os.path.join(DEALS_DIR, fn)
        with open(fp, "r", encoding="utf-8") as f:
            deal = json.load(f)
        if deal.get("status") != "active" or not deal.get("source_url"):
            continue
        live_items.append({"fp": fp, "deal": deal, "url": deal["source_url"]})

    if not live_items:
        return

    expired_now = 0
    refreshed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        for res in pool.map(check_url, live_items[:250]):
            if not res:
                continue
            entry = res["item"]
            fp = entry["fp"]
            deal = entry["deal"]
            if res["state"] == "ended":
                deal["status"] = "expired"
                deal["end_date"] = NOW_ISO
                expired_now += 1
            elif res["state"] == "live":
                deal["last_verified_at"] = NOW_ISO
                deal["end_date"] = (NOW + dt.timedelta(days=3)).strftime("%Y-%m-%dT23:59:00Z")
                if res["pct"] is not None:
                    title, disc_val, badge, num_pct, kind = format_offer_copy(
                        deal.get("title", "").split(":")[0] or deal.get("brand_id", ""),
                        deal.get("category", "clothing-fashion"),
                        res["pct"],
                        res.get("is_flat", False),
                    )
                    deal["title"] = title
                    deal["discount_value"] = disc_val
                    deal["badge_text"] = badge
                    deal["numeric_discount_percent"] = num_pct
                    deal["offer_kind"] = kind
                refreshed += 1
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(deal, f, indent=2)

    print(f"[reverify] checked={min(len(live_items), 250)}, refreshed={refreshed}, ended_expired={expired_now}")


def scan_watchlist(active_brand_ids):
    if not os.path.exists(WATCHLIST_PATH):
        return 0

    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        watchlist = json.load(f)

    # Prioritize focus markets in every 12h cycle
    FOCUS_COUNTRIES = {"PK", "US", "GB", "IN", "AE", "SA", "TR", "NL", "DE", "JP", "CN", "BD", "ZA", "NG", "KE", "SG", "MY", "GLOBAL"}
    candidates = [b for b in watchlist if b["id"] not in active_brand_ids and b.get("url")]
    candidates.sort(key=lambda b: (0 if b.get("country") in FOCUS_COUNTRIES else 1, b.get("country", "")))
    slot = int(NOW.timestamp() // (12 * 3600)) % max(1, (len(candidates) // 400) + 1)
    batch = candidates[slot * 400 : (slot + 1) * 400]
    if not batch and candidates:
        batch = candidates[:400]

    print(f"[scanner] checking {len(batch)} brands from watchlist (total candidates={len(candidates)})...")
    discovered = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
        for res in pool.map(check_url, batch):
            if not res or res.get("state") != "live":
                continue
            b = res["item"]
            bid = b["id"]
            country = b.get("country", "GLOBAL")
            cat = b.get("category", "clothing-fashion")
            url = b["url"]
            dom = get_domain(url)
            pct = res["pct"]
            is_flat = res.get("is_flat", False)

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

            end_iso = (NOW + dt.timedelta(days=3)).strftime("%Y-%m-%dT23:59:00Z")
            title, disc_val, badge, num_pct, offer_kind = format_offer_copy(b["name"], cat, pct, is_flat)
            with open(dpath, "w", encoding="utf-8") as df:
                json.dump({
                    "id": deal_id,
                    "slug": deal_id,
                    "title": title,
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
                    "discount_value": disc_val,
                    "badge_text": badge,
                    "numeric_discount_percent": num_pct,
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
                    "offer_kind": offer_kind,
                    "image": {"src": f"https://www.google.com/s2/favicons?domain={dom}&sz=128", "alt": b["name"]},
                    "tags": ["all-items"],
                }, df, indent=2)
            discovered += 1

    print(f"[scanner] discovered {discovered} new deals")
    return discovered


if __name__ == "__main__":
    reverify_live_offers()
    active_ids = lifecycle_sync()
    scan_watchlist(active_ids)
