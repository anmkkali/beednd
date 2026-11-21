"""
Real-markdown collector for Shopify storefronts.

For each configured store it reads the public /products.json feed, counts the products whose
compare_at_price is higher than price, and writes one deal per store to src/content/deals/.
Every number in a generated deal comes from the live feed. Nothing is invented.

Run:  python scripts/collectors/shopify_sales.py            (all stores)
      python scripts/collectors/shopify_sales.py gulahmed   (one store id)
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DEALS_DIR = os.path.join(ROOT, "src", "content", "deals")
BRANDS_DIR = os.path.join(ROOT, "src", "content", "brands")
UA = "Mozilla/5.0 (compatible; DealsSiteBot/1.0; +https://dealssite.com/bot)"
MIN_PERCENT = 10      # ignore tiny markdowns
MAX_PERCENT = 90      # ignore implausible compare-at prices
MIN_ITEMS = 3         # only publish a deal when at least this many items are marked down
DELAY_SECONDS = 5     # pause between stores, be polite to the sites

CLOTHING, BEAUTY = "clothing-fashion", "beauty-wellness"

# domain, brand id, display name, country (ISO-2), category, one-line factual bio
SOURCES = [
    ("gulahmedshop.com", "gulahmed", "Gul Ahmed", "PK", CLOTHING, "Pakistani textile and fashion brand."),
    ("alkaramstudio.com", "alkaram", "Alkaram Studio", "PK", CLOTHING, "Pakistani clothing brand."),
    ("limelight.pk", "limelight", "Limelight", "PK", CLOTHING, "Pakistani fashion brand."),
    ("outfitters.com.pk", "outfitters", "Outfitters", "PK", CLOTHING, "Pakistani fashion retailer."),
    ("bonanzasatrangi.com", "bonanza-satrangi", "Bonanza Satrangi", "PK", CLOTHING, "Pakistani clothing brand."),
    ("www.nishatlinen.com", "nishat-linen", "Nishat Linen", "PK", CLOTHING, "Pakistani clothing and home textile brand."),
    ("www.beechtree.pk", "beechtree", "Beechtree", "PK", CLOTHING, "Pakistani women's fashion brand."),
    ("www.engine.com.pk", "engine", "Engine", "PK", CLOTHING, "Pakistani clothing brand."),
    ("www.diners.com.pk", "diners", "Diners", "PK", CLOTHING, "Pakistani fashion brand."),
    ("www.edenrobe.com", "edenrobe", "Edenrobe", "PK", CLOTHING, "Pakistani fashion brand."),
    ("www.mariab.pk", "maria-b", "Maria B", "PK", CLOTHING, "Pakistani designer fashion brand."),
    ("junaidjamshed.com", "jdot", "J. Junaid Jamshed", "PK", CLOTHING, "Pakistani clothing and fragrance brand."),
    ("www.allbirds.com", "allbirds", "Allbirds", "US", CLOTHING, "Footwear and apparel brand."),
    ("tentree.com", "tentree", "Tentree", "US", CLOTHING, "Apparel brand."),
    ("www.taylorstitch.com", "taylor-stitch", "Taylor Stitch", "US", CLOTHING, "Menswear brand."),
    ("www.outdoorvoices.com", "outdoor-voices", "Outdoor Voices", "US", CLOTHING, "Activewear brand."),
    ("www.kyliecosmetics.com", "kylie-cosmetics", "Kylie Cosmetics", "US", BEAUTY, "Cosmetics brand."),
    ("www.glossier.com", "glossier", "Glossier", "US", BEAUTY, "Skincare and makeup brand."),
    ("fentybeauty.com", "fenty-beauty", "Fenty Beauty", "US", BEAUTY, "Makeup and skincare brand."),
    ("www.jeffreestarcosmetics.com", "jeffree-star", "Jeffree Star Cosmetics", "US", BEAUTY, "Cosmetics brand."),
    ("www.finisterre.com", "finisterre", "Finisterre", "GB", CLOTHING, "Outdoor clothing brand."),
    ("www.wearethought.com", "thought", "Thought", "GB", CLOTHING, "Sustainable clothing brand."),
    ("www.vollebak.com", "vollebak", "Vollebak", "GB", CLOTHING, "Clothing brand."),
]

# Words that map a discounted product to a sidebar filter group or sub-filter
KEYWORDS = {
    "women": r"\b(women|woman|womens|ladies|lady|female)\b",
    "men": r"\b(men|mens|man|gents|male)\b",
    "kids": r"\b(kids|kid|boys|boy|girls|girl|baby|infant|toddler|junior)\b",
    "unstitched": r"\bunstitched\b",
    "stitched": r"(?<!un)\bstitched\b",
    "pret": r"\b(pret|ready to wear|ready-to-wear|rtw)\b",
    "footwear": r"\b(shoe|shoes|footwear|sneaker|sneakers|sandal|sandals|slides|boots|heels|khussa|loafers)\b",
    "accessories": r"\b(bag|bags|belt|belts|wallet|scarf|scarves|cap|hat|socks|jewellery|jewelry|sunglasses|watch)\b",
    "skincare": r"\b(skincare|serum|moisturi[sz]er|cleanser|sunscreen|cream|toner|mask)\b",
    "makeup": r"\b(makeup|lipstick|lip|foundation|mascara|eyeshadow|palette|blush|concealer|gloss)\b",
    "fragrance": r"\b(fragrance|perfume|eau de|cologne|attar|body mist)\b",
    "hair": r"\b(hair|shampoo|conditioner)\b",
}


class RateLimited(Exception):
    """Raised when a store keeps answering 429 so the run can stop instead of hammering it."""


def fetch_products(domain):
    url = f"https://{domain}/products.json?limit=250"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8", "ignore")).get("products", [])
        except urllib.error.HTTPError as err:
            if err.code == 429:
                if attempt < 2:
                    wait = int(err.headers.get("Retry-After", "0") or 0) or 15 * (attempt + 1)
                    print(f"  rate limited, waiting {min(wait, 60)}s")
                    time.sleep(min(wait, 60))
                    continue
                raise RateLimited(domain)
            print(f"  HTTP {err.code}")
            return None
        except Exception as err:  # network error or invalid JSON
            print(f"  failed: {err}")
            return None
    return None


def analyse(products):
    marked_down, best_overall, tags = 0, 0, set()
    for product in products:
        best = 0
        for variant in product.get("variants", []):
            try:
                price = float(variant.get("price") or 0)
                compare = float(variant.get("compare_at_price") or 0)
            except ValueError:
                continue
            if compare > price > 0:
                pct = round((compare - price) / compare * 100)
                if MIN_PERCENT <= pct <= MAX_PERCENT:
                    best = max(best, pct)
        if not best:
            continue
        marked_down += 1
        best_overall = max(best_overall, best)
        raw = product.get("tags", [])
        if isinstance(raw, str):
            raw = raw.split(",")
        text = f"{product.get('title', '')} {product.get('product_type', '')} {' '.join(raw)}".lower()
        for tag, pattern in KEYWORDS.items():
            if re.search(pattern, text):
                tags.add(tag)
    return marked_down, best_overall, sorted(tags)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def build(domain, brand_id, name, country, category, bio):
    print(f"[{brand_id}] {domain}")
    products = fetch_products(domain)
    if products is None:
        return False
    marked_down, best, tags = analyse(products)
    print(f"  {len(products)} products checked, {marked_down} marked down, up to {best}%")

    deal_path = os.path.join(DEALS_DIR, f"{brand_id}-store-sale.json")
    if marked_down < MIN_ITEMS:
        if os.path.exists(deal_path):
            os.remove(deal_path)  # sale is over
        return True

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    today = now[:10]
    favicon = f"https://www.google.com/s2/favicons?domain={domain.removeprefix('www.')}&sz=128"
    brand_path = os.path.join(BRANDS_DIR, f"{brand_id}.json")
    if not os.path.exists(brand_path):
        write_json(brand_path, {
            "id": brand_id, "name": name, "slug": brand_id, "logo_url": favicon,
            "website_url": f"https://{domain}", "country": country,
            "categories": [category], "short_bio": bio,
        })

    write_json(deal_path, {
        "id": f"{brand_id}-store-sale", "slug": f"{brand_id}-store-sale",
        "title": f"{name} Sale: Up to {best}% Off on {marked_down} Marked-Down Items",
        "short_description": (
            f"Of {len(products)} products checked on {name}'s online store, {marked_down} were marked down "
            f"by up to {best}%. Prices and stock change often, so confirm on the store."
        ),
        "brand_id": brand_id, "country": country, "cities": [], "areas": [], "branch_info": [],
        "category": category, "deal_type": "store-sale",
        "discount_type": "percentage", "discount_value": f"Up to {best}% OFF",
        "badge_text": f"Up to {best}% off on {marked_down} items",
        "numeric_discount_percent": best,
        "terms_and_conditions": [
            f"Based on prices published on {name}'s online store on {today}.",
            "Discounts apply to selected items only and can end at any time.",
            "Confirm the final price at checkout.",
        ],
        "start_date": now, "end_date": None,
        "source_url": f"https://{domain}", "affiliate_url": f"https://{domain}",
        "last_verified_at": now, "status": "active",
        "is_trending": marked_down >= 40 and best >= 50,
        "offer_kind": "discount",
        "image": {"src": favicon, "alt": name},
        "tags": tags,
    })
    return True


def main(only=None):
    os.makedirs(DEALS_DIR, exist_ok=True)
    os.makedirs(BRANDS_DIR, exist_ok=True)
    limited_in_a_row = 0
    for domain, brand_id, name, country, category, bio in SOURCES:
        if only and brand_id != only:
            continue
        try:
            build(domain, brand_id, name, country, category, bio)
            limited_in_a_row = 0
        except RateLimited:
            limited_in_a_row += 1
            print("  skipped, still rate limited")
            if limited_in_a_row >= 2:
                print("Stopping: stores keep rate limiting this IP. Try again later.")
                return
        time.sleep(DELAY_SECONDS)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
