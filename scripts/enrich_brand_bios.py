import concurrent.futures
import html as html_lib
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDS_DIR = os.path.join(ROOT, "src", "content", "brands")

COUNTRY_NAMES = {
    "PK": "Pakistan", "US": "the United States", "GB": "the United Kingdom", "IN": "India",
    "AE": "the UAE", "SA": "Saudi Arabia", "TR": "Turkey", "NL": "the Netherlands",
    "DE": "Germany", "JP": "Japan", "CN": "China", "BD": "Bangladesh",
    "ZA": "South Africa", "NG": "Nigeria", "KE": "Kenya", "SG": "Singapore",
    "MY": "Malaysia", "CA": "Canada", "AU": "Australia", "GLOBAL": "worldwide",
}

CAT_CONTEXT = {
    "clothing-fashion": ("apparel, footwear, and seasonal collections", ["Apparel & fashion", "Seasonal collections", "Online & store deals"]),
    "tech-electronics": ("consumer electronics, gadgets, and smart devices", ["Electronics & tech", "Gadgets & accessories", "Seasonal markdowns"]),
    "ai-tools": ("AI productivity tools, software plans, and cloud subscriptions", ["AI software", "Free trials", "Pro plan discounts"]),
    "food-dining": ("fresh meals, restaurant dining, and food delivery", ["Dining & delivery", "Meal combos", "App vouchers"]),
    "beauty-wellness": ("skincare, makeup, fragrances, and personal care", ["Skincare & beauty", "Cosmetics", "Bundle offers"]),
    "travel-lifestyle": ("flights, hotel stays, and travel bookings", ["Flights & hotels", "Travel packages", "Seasonal fares"]),
    "groceries-essentials": ("daily groceries, household staples, and pantry essentials", ["Daily groceries", "Household essentials", "Weekly savings"]),
    "pets": ("pet food, treats, toys, and veterinary essentials", ["Pet food & care", "Pet accessories", "Bundle savings"]),
}

PRODUCT_KEYWORDS = [
    ("footwear", "footwear"), ("shoes", "footwear"), ("sneakers", "sneakers"),
    ("unstitched", "unstitched fabrics"), ("pret", "ready-to-wear"), ("kurta", "ethnic wear"),
    ("lawn", "seasonal lawn"), ("denim", "denim"), ("kids", "kids' apparel"),
    ("skincare", "skincare"), ("makeup", "makeup"), ("fragrance", "fragrances"),
    ("perfume", "fragrances"), ("laptop", "laptops"), ("phone", "smartphones"),
    ("audio", "audio gear"), ("appliance", "home appliances"), ("hotel", "hotel stays"),
    ("flight", "flight bookings"), ("pizza", "pizza & combos"), ("burger", "fast food"),
    ("grocery", "groceries"), ("organic", "organic staples"), ("pet", "pet supplies"),
    ("dog", "dog food & gear"), ("cat", "cat food & litter"), ("home", "home textiles"),
    ("watch", "watches"), ("jewel", "jewelry"), ("bag", "bags & accessories"),
]


def fetch_meta(brand):
    url = brand.get("website_url") or ""
    if not url.startswith("http"):
        return brand, "", ""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status != 200:
                return brand, "", ""
            raw = resp.read(60_000).decode("utf-8", errors="ignore")
            t_m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
            d_m = re.search(
                r'<meta[^>]+(?:name=["\']description["\']|property=["\']og:description["\'])[^>]+content=["\'](.*?)["\']',
                raw,
                re.S | re.I,
            ) or re.search(
                r'<meta[^>]+content=["\'](.*?)["\'][^>]+(?:name=["\']description["\']|property=["\']og:description["\'])',
                raw,
                re.S | re.I,
            )
            title = html_lib.unescape(re.sub(r"\s+", " ", t_m.group(1))).strip() if t_m else ""
            desc = html_lib.unescape(re.sub(r"\s+", " ", d_m.group(1))).strip() if d_m else ""
            return brand, title, desc
    except Exception:
        return brand, "", ""


def build_original_bio(brand, title, desc):
    name = brand["name"]
    country = brand.get("country", "GLOBAL")
    c_name = COUNTRY_NAMES.get(country, country)
    cat = (brand.get("categories") or ["clothing-fashion"])[0]
    cat_phrase, default_known = CAT_CONTEXT.get(cat, CAT_CONTEXT["clothing-fashion"])

    combined = f"{name} {title} {desc}".lower()
    detected_items = []
    for kw, label in PRODUCT_KEYWORDS:
        if kw in combined and label not in detected_items:
            detected_items.append(label)
        if len(detected_items) >= 3:
            break

    if detected_items:
        focus = ", ".join(detected_items[:-1]) + (" and " + detected_items[-1] if len(detected_items) > 1 else detected_items[0])
        known = [x.capitalize() for x in detected_items] + [default_known[-1]]
    else:
        focus = cat_phrase
        known = default_known

    loc_phrase = "available worldwide" if country == "GLOBAL" else f"popular with shoppers across {c_name}"
    short_bio = (
        f"{name} is a retail brand {loc_phrase}, known for {focus}. "
        f"Shoppers follow {name} on BeeDND for verified seasonal markdowns, promo codes, and official store offers."
    )
    about = (
        f"{name} offers {focus} tailored for customers {('worldwide' if country == 'GLOBAL' else f'in {c_name}')}. "
        f"Whenever {name} launches a seasonal sale, clearance event, or verified promo code, BeeDND lists the active offer details and official store link here."
    )
    return short_bio, about, known[:4]


def main():
    targets = []
    for fn in sorted(os.listdir(BRANDS_DIR)):
        if not fn.endswith(".json"):
            continue
        fp = os.path.join(BRANDS_DIR, fn)
        with open(fp, "r", encoding="utf-8") as f:
            b = json.load(f)
        bio = b.get("short_bio", "")
        if "brand offering seasonal sales and online discounts" in bio or len(bio) < 65:
            b["_fp"] = fp
            targets.append(b)

    print(f"Enriching {len(targets)} generic brand bios...")
    updated = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
        for b, title, desc in pool.map(fetch_meta, targets):
            fp = b.pop("_fp")
            short_bio, about, known = build_original_bio(b, title, desc)
            b["short_bio"] = short_bio
            b["about"] = about
            b["known_for"] = known
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(b, f, indent=2)
            updated += 1
    print(f"Updated {updated} brand files.")


if __name__ == "__main__":
    main()
