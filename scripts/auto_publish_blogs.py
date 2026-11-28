import datetime as dt
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEALS_DIR = os.path.join(ROOT, "src", "content", "deals")
BRANDS_DIR = os.path.join(ROOT, "src", "content", "brands")
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")

TODAY = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

COUNTRY_NAMES = {
    "US": "USA", "GB": "UK", "AE": "UAE", "SA": "Saudi Arabia",
    "IN": "India", "PK": "Pakistan", "DE": "Germany", "NL": "Netherlands",
    "TR": "Turkey", "CA": "Canada", "AU": "Australia", "SG": "Singapore",
    "GLOBAL": "Worldwide",
}

TOPIC_IMAGES = {
    "clothing-fashion": "/images/blog/uk-fashion.jpg",
    "footwear": "/images/blog/us-shopping.jpg",
    "kids-baby": "/images/blog/kids-winter.jpg",
    "ai-tools": "/images/blog/ai-tools.jpg",
    "pets": "/images/blog/pets-care.jpg",
    "travel-lifestyle": "/images/blog/travel-deals.jpg",
    "groceries-essentials": "/images/blog/groceries.jpg",
    "beauty-wellness": "/images/blog/uk-fashion.jpg",
    "food-dining": "/images/blog/groceries.jpg",
    "tech-electronics": "/images/blog/ai-tools.jpg",
    "bank": "/images/blog/bank-cards.jpg",
}

PRIORITY_TRACKS = [
    ("US", "clothing-fashion", "Best US Clothing & Winter Clearance Sales This Week"),
    ("GB", "footwear", "UK Footwear & Winter Boot Deals: Clarks, Skechers & More"),
    ("US", "kids-baby", "Top US Kids & Baby Clothing Markdowns: Carter's, OshKosh & Gap Kids"),
    ("GB", "kids-baby", "UK Kids & Baby Sale Guide: Mothercare, Mamas & Papas & Next"),
    ("US", "ai-tools", "Best AI Tools Free Trials & Creator Credits for US Teams"),
    ("AE", "clothing-fashion", "Dubai & UAE Seasonal Fashion Discounts and Promo Codes"),
    ("SA", "kids-baby", "Saudi Arabia Kids & Baby Offers: Babyshop, Mumzworld & FirstCry"),
    ("IN", "beauty-wellness", "India Skincare & Beauty Offers: Nykaa, The Ordinary & Cashback"),
    ("PK", "footwear", "Pakistan Footwear Sales Guide: Bata, Stylo, Hush Puppies & Borjan"),
    ("DE", "tech-electronics", "Germany Tech & Appliance Deals: Verified Seasonal Savings"),
    ("NL", "groceries-essentials", "Netherlands Grocery & Household Weekly Offers Guide"),
    ("GLOBAL", "ai-tools", "How to Compare AI Video, Coding & Writing Free Trials"),
]


def load_active_deals():
    deals = []
    for fp in glob.glob(os.path.join(DEALS_DIR, "*.json")):
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("status") == "active" and not d.get("is_coming_soon"):
            deals.append(d)
    return deals


def load_brands():
    brands = {}
    for fp in glob.glob(os.path.join(BRANDS_DIR, "*.json")):
        with open(fp, "r", encoding="utf-8") as f:
            b = json.load(f)
        brands[b["id"]] = b
    return brands


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    existing_files = set(os.listdir(BLOG_DIR))
    deals = load_active_deals()
    brands = load_brands()

    for country, cat, headline in PRIORITY_TRACKS:
        slug = f"{slugify(headline)}.md"
        if slug in existing_files:
            continue

        matching = [
            d for d in deals
            if d.get("category") == cat and (country == "GLOBAL" or d.get("country") in (country, "GLOBAL"))
        ]
        if len(matching) < 2:
            continue

        matching.sort(key=lambda d: (-(d.get("numeric_discount_percent") or 0), d.get("id", "")))
        top_deals = matching[:6]
        brand_names = []
        bullets = []
        for d in top_deals:
            bname = brands.get(d["brand_id"], {}).get("name", d["brand_id"])
            if bname not in brand_names:
                brand_names.append(bname)
            badge = d.get("badge_text") or d.get("discount_value") or "Sale Live"
            bullets.append(f"- **{bname} ({badge}):** {d.get('short_description', d.get('title'))}")

        c_label = COUNTRY_NAMES.get(country, country)
        cat_label = cat.replace("-", " ").title()
        hero_img = TOPIC_IMAGES.get(cat, "/images/blog/us-shopping.jpg")
        desc = (
            f"Verified {c_label} {cat_label.lower()} deals and seasonal discounts across "
            f"{', '.join(brand_names[:4])}. Updated {TODAY} on BeeDND."
        )

        md = f"""---
title: "{headline}"
description: "{desc}"
published_date: "{TODAY}"
author: "BeeDND Editorial"
hero_image: "{hero_img}"
target_country: "{country}"
is_published: true
tags:
  - {c_label.lower()} deals
  - {cat}
  - verified discounts
---

Shoppers in **{c_label}** looking for genuine **{cat_label.lower()}** markdowns can save significantly this week by focusing on verified storewide promos instead of expired coupon lists. Below are the strongest live offers currently tracked on BeeDND.

## Verified {c_label} {cat_label} Offers Live Now

{chr(10).join(bullets)}

## Tips to Maximize Your Checkout Savings

1. **Check Official Sale Links First:** Every brand page on BeeDND links directly to the store's active promotion page so discounts apply cleanly in-cart.
2. **Stack Payment Offers:** Whenever shopping with a rewards credit or debit card in {c_label}, check bank portal cashback offers before finalizing checkout.
"""
        out_path = os.path.join(BLOG_DIR, slug)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[blog-bot] published {slug} (country={country}, category={cat}, deals={len(top_deals)})")
        return

    print("[blog-bot] all priority tracks already published.")


if __name__ == "__main__":
    main()
