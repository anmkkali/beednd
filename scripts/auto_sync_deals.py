import argparse
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

FOCUS_COUNTRIES = [
    "PK", "US", "GB", "IN", "AE", "SA", "TR", "NL",
    "DE", "JP", "CN", "BD", "ZA", "NG", "KE", "SG", "GLOBAL",
]

SALE_RE = re.compile(
    r"(?:flat\s+\d{1,2}%\s*(?:off|discount)?|up\s+to\s+\d{1,2}%\s*(?:off|discount)?|save\s+(?:up\s+to\s+)?\d{1,2}%|\d{1,2}%\s*(?:off|discount)|black\s+friday|white\s+friday|blessed\s+friday|cyber\s+monday|winter\s+sale|summer\s+sale|mega\s+sale|flash\s+sale|end\s+of\s+season\s+sale|clearance\s+sale|free\s+trial|promo\s+code)",
    re.IGNORECASE,
)
PCT_RE = re.compile(r"(?:(?:flat|up\s+to|save)\s+(\d{1,2})\s*%|\b(\d{1,2})\s*%\s*(?:off|discount))", re.IGNORECASE)

SPECIFIC_OFFER_PATTERNS = [
    (r"\bkurta\b", "Kurta & Waistcoats", ["men", "kurta"]),
    (r"\bunstitched\b", "Unstitched Collection", ["women", "unstitched"]),
    (r"\bpret\b|\bready\s+to\s+wear\b", "Ready-to-Wear Pret", ["women", "pret"]),
    (r"\bwinter\b|\bjacket|\bsweater|\bhoodie", "Winter Wear", ["winter"]),
    (r"\bfootwear\b|\bshoes?\b|\bsneakers?\b|\bsandals?\b", "Footwear", ["footwear"]),
    (r"\bnewborn\b|\binfant\b", "Newborn Essentials", ["baby-newborn", "newborn", "baby"]),
    (r"\btoys?\b|\bgames?\b", "Toys & Games", ["baby-newborn", "toys"]),
    (r"\bschool\b|\buniform|\bbackpack", "School Wear & Bags", ["kids-shoes-school", "school"]),
    (r"\bboys?\b", "Boys Apparel", ["kids-clothing", "boys"]),
    (r"\bgirls?\b", "Girls Apparel", ["kids-clothing", "girls"]),
    (r"\bbaby\b|\bstroller|\bdiaper", "Baby Care & Apparel", ["baby-newborn", "baby", "baby-care"]),
    (r"\bt-?shirts?\b|\bshirts?\b", "Shirts & Tops", ["men", "shirts"]),
    (r"\btrousers?\b|\bjeans\b|\bdenim\b", "Trousers & Denim", ["men", "women", "trousers"]),
]

COUNTRY_CITIES = {
    "PK": ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan"],
    "US": ["New York", "Los Angeles", "Chicago", "Houston", "Dallas"],
    "GB": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow"],
    "IN": ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Pune"],
    "AE": ["Dubai", "Abu Dhabi", "Sharjah"],
    "SA": ["Riyadh", "Jeddah", "Dammam"],
    "TR": ["Istanbul", "Ankara", "Izmir"],
    "NL": ["Amsterdam", "Rotterdam", "Utrecht"],
    "DE": ["Berlin", "Munich", "Hamburg", "Frankfurt"],
    "JP": ["Tokyo", "Osaka", "Kyoto"],
    "CN": ["Shanghai", "Beijing", "Shenzhen"],
    "BD": ["Dhaka", "Chattogram", "Sylhet"],
    "ZA": ["Johannesburg", "Cape Town", "Durban"],
    "NG": ["Lagos", "Abuja"],
    "KE": ["Nairobi", "Mombasa"],
    "SG": ["Singapore"],
}


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


def infer_tags(name, cat, signal_text=""):
    t = f"{name} {signal_text}".lower()
    tags = []
    for pat, _, p_tags in SPECIFIC_OFFER_PATTERNS:
        if re.search(pat, t, re.I):
            for pt in p_tags:
                if pt not in tags:
                    tags.append(pt)
    if cat == "footwear":
        return ["mens-footwear", "womens-footwear", "sports-athletic", "sneakers", "formal", "sandals", "heels", "flats", "running"]
    if cat == "kids-baby":
        for base in ("kids-clothing", "baby-newborn", "kids-shoes-school", "boys", "girls", "baby"):
            if base not in tags:
                tags.append(base)
        return tags[:10]
    if cat == "clothing-fashion":
        if any(w in t for w in ("shoe", "footwear", "bata", "stylo", "hush puppies", "ecs", "insignia", "mocciani", "borjan", "metro", "sputnik", "sneaker", "crocs")):
            for tg in ("men", "women", "footwear"):
                if tg not in tags:
                    tags.append(tg)
        elif any(w in t for w in ("cambridge", "charcoal", "uniworth", "diners", "monark")):
            for tg in ("men", "shirts", "trousers", "kurta"):
                if tg not in tags:
                    tags.append(tg)
        elif any(w in t for w in ("sana safinaz", "maria b", "alkaram", "gul ahmed", "beechtree", "khaadi", "nishat", "limelight", "cross stitch", "zeen", "so kamal", "rang jah", "ethnic")):
            for tg in ("women", "unstitched", "pret", "winter"):
                if tg not in tags:
                    tags.append(tg)
        elif not any(g in tags for g in ("men", "women")):
            tags.extend(["men", "women"])
        return tags[:10]
    return tags or ["all-items"]


def detect_focus_label(name, signal_text=""):
    t = f"{name} {signal_text}".lower()
    for pat, label, _ in SPECIFIC_OFFER_PATTERNS:
        if re.search(pat, t, re.I):
            return label
    return ""


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
            if "COMING SOON" in (deal.get("discount_value") or "").upper():
                pct = deal.get("numeric_discount_percent") or 0
                deal["discount_value"] = f"UP TO {pct}% OFF" if pct else "SALE LIVE"
                deal["badge_text"] = f"Up to {pct}% Off" if pct else "Sale Live"
            if (deal.get("short_description") or "").startswith("Upcoming "):
                deal["short_description"] = "Live " + deal["short_description"][9:]
            changed = True
            activated_count += 1

        if deal.get("status") == "active":
            active_brand_ids.add(deal.get("brand_id"))

        if changed:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(deal, f, indent=2)

    print(f"[lifecycle] expired={expired_count}, coming_soon_activated={activated_count}, active_brands={len(active_brand_ids)}")
    return active_brand_ids


def fetch_html(url):
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
            return resp.status, ""
        html = resp.read(160_000).decode("utf-8", errors="ignore")
        html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
        return 200, text


def check_url(item):
    url = item.get("url") or ""
    if not url.startswith("http"):
        return None
    urls_to_try = [url]
    parsed = urlparse(url)
    if parsed.path in ("", "/"):
        base = f"{parsed.scheme}://{parsed.netloc}"
        urls_to_try.append(f"{base}/collections/sale")
        urls_to_try.append(f"{base}/sale")

    last_200 = False
    for target in urls_to_try:
        try:
            code, text = fetch_html(target)
            if code in (404, 410):
                continue
            if code == 200:
                last_200 = True
                matches = SALE_RE.findall(text)
                if not matches:
                    continue
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
                    "context": top_text[:600],
                    "pct": best_pct,
                    "is_flat": is_flat,
                    "matched_url": target,
                }
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                continue
        except Exception:
            continue

    return {"item": item, "state": "ended"} if last_200 else None


def format_offer_copy(name, cat, pct, is_flat, focus_label=""):
    is_ai = cat == "ai-tools"
    if is_ai:
        return (
            f"{name}: Free Trial & Plan Discounts",
            "FREE TRIAL",
            "Free Trial",
            pct or 0,
            "trial",
        )
    on_suffix = f" on {focus_label}" if focus_label else " Sale"
    if pct:
        prefix = "Flat" if is_flat else "Up to"
        return (
            f"{name}: {prefix} {pct}% Off{on_suffix}",
            f"{prefix.upper()} {pct}% OFF",
            f"{prefix} {pct}% Off",
            pct,
            "discount",
        )
    return (
        f"{name}: Seasonal Offers{on_suffix}",
        "SEASONAL SALE",
        "Sale Live",
        0,
        "discount",
    )


def reverify_live_offers(country_filter=None):
    live_items = []
    for fn in os.listdir(DEALS_DIR):
        if not fn.endswith("-live-offer.json"):
            continue
        fp = os.path.join(DEALS_DIR, fn)
        with open(fp, "r", encoding="utf-8") as f:
            deal = json.load(f)
        if deal.get("status") != "active" or deal.get("is_trending") or not deal.get("source_url"):
            continue
        if country_filter and deal.get("country") != country_filter:
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
                    bname = deal.get("title", "").split(":")[0] or deal.get("brand_id", "")
                    focus = detect_focus_label(bname, res.get("context", ""))
                    title, disc_val, badge, num_pct, kind = format_offer_copy(
                        bname,
                        deal.get("category", "clothing-fashion"),
                        res["pct"],
                        res.get("is_flat", False),
                        focus,
                    )
                    deal["title"] = title
                    deal["discount_value"] = disc_val
                    deal["badge_text"] = badge
                    deal["numeric_discount_percent"] = num_pct
                    deal["offer_kind"] = kind
                refreshed += 1
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(deal, f, indent=2)

    tag = f"[{country_filter}]" if country_filter else "[all]"
    print(f"[reverify]{tag} checked={min(len(live_items), 250)}, refreshed={refreshed}, ended_expired={expired_now}")


def scan_country(watchlist, active_brand_ids, country_code, limit=120):
    candidates = [
        b for b in watchlist
        if b["id"] not in active_brand_ids and b.get("url") and b.get("country") == country_code
    ]
    if not candidates:
        return 0
    batch = candidates[:limit]
    discovered = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for res in pool.map(check_url, batch):
            if not res or res.get("state") != "live":
                continue
            b = res["item"]
            bid = b["id"]
            country = b.get("country", "GLOBAL")
            cat = b.get("category", "clothing-fashion")
            url = res.get("matched_url") or b["url"]
            dom = get_domain(url)
            pct = res["pct"]
            is_flat = res.get("is_flat", False)
            ctx = res.get("context", "")
            focus = detect_focus_label(b["name"], ctx)

            bpath = os.path.join(BRANDS_DIR, f"{bid}.json")
            if not os.path.exists(bpath):
                new_brand = {
                    "id": bid,
                    "name": b["name"],
                    "slug": bid,
                    "logo_url": f"https://www.google.com/s2/favicons?domain={dom}&sz=128",
                    "website_url": b["url"],
                    "country": country,
                    "categories": [cat],
                    "short_bio": "",
                    "known_for": [],
                }
                try:
                    from enrich_brand_bios import build_original_bio, fetch_meta
                    _, m_title, m_desc = fetch_meta(new_brand)
                    short_bio, about, known = build_original_bio(new_brand, m_title, m_desc)
                    new_brand["short_bio"] = short_bio
                    new_brand["about"] = about
                    new_brand["known_for"] = known
                except Exception:
                    new_brand["short_bio"] = f"{b['name']} is a retail brand in {country} tracked on BeeDND for verified seasonal sales and online offers."
                    new_brand["known_for"] = ["Seasonal sales", "Online offers"]
                with open(bpath, "w", encoding="utf-8") as bf:
                    json.dump(new_brand, bf, indent=2)

            deal_id = f"{bid}-live-offer"
            dpath = os.path.join(DEALS_DIR, f"{deal_id}.json")
            if os.path.exists(dpath):
                continue

            end_iso = (NOW + dt.timedelta(days=3)).strftime("%Y-%m-%dT23:59:00Z")
            title, disc_val, badge, num_pct, offer_kind = format_offer_copy(b["name"], cat, pct, is_flat, focus)
            cities = COUNTRY_CITIES.get(country, [])[:4] if cat in ("clothing-fashion", "footwear", "kids-baby", "groceries-essentials", "food-dining") else []

            with open(dpath, "w", encoding="utf-8") as df:
                json.dump({
                    "id": deal_id,
                    "slug": deal_id,
                    "title": title,
                    "short_description": f"Verified active promotion detected on {b['name']}'s official store ({res['signal']}). Confirm exclusions at checkout.",
                    "brand_id": bid,
                    "country": country,
                    "cities": cities,
                    "areas": [],
                    "branch_info": [],
                    "category": cat,
                    "deal_type": "store-sale" if cities else "online",
                    "channels": ["online", "in-store"] if cities else ["online"],
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
                    "tags": infer_tags(b["name"], cat, ctx),
                }, df, indent=2)
            discovered += 1
            active_brand_ids.add(bid)

    print(f"[bot:{country_code}] scanned={len(batch)}, discovered={discovered}")
    return discovered


def scan_watchlist(active_brand_ids, target_country=None):
    if not os.path.exists(WATCHLIST_PATH):
        return 0
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        watchlist = json.load(f)

    if target_country:
        return scan_country(watchlist, active_brand_ids, target_country, limit=250)

    total = 0
    for code in FOCUS_COUNTRIES:
        total += scan_country(watchlist, active_brand_ids, code, limit=80)
    print(f"[scanner] total discovered across country bots: {total}")
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BeeDND per-country deal scanner and lifecycle sync")
    parser.add_argument("--country", default="", help="Optional 2-letter country code (e.g. PK, US, GB, AE) or empty for all focus countries")
    args = parser.parse_args()
    c_arg = args.country.strip().upper() or None

    reverify_live_offers(c_arg)
    active_ids = lifecycle_sync()
    scan_watchlist(active_ids, c_arg)
