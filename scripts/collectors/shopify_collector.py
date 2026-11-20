"""
Shopify Public Products JSON Price Drop Collector
Monitors public /products.json endpoints on brand stores.
Detects items where compare_at_price > price and computes discount percentages.
"""

import httpx
from typing import List, Dict, Any

class ShopifyCollector:
    def __init__(self, brand_domain: str, brand_id: str, country: str = "PK"):
        self.brand_domain = brand_domain.rstrip('/')
        self.brand_id = brand_id
        self.country = country
        self.endpoint = f"{self.brand_domain}/products.json?limit=50"
        self.headers = {
            "User-Agent": "DealsSiteBot/1.0 (+https://dealssite.com/bot; verified-deals-aggregator)"
        }

    def fetch_price_drops(self, min_discount_percent: float = 20.0) -> List[Dict[str, Any]]:
        deals = []
        try:
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                res = client.get(self.endpoint)
                if res.status_code != 200:
                    print(f"[{self.brand_id}] Non-200 status code: {res.status_code}")
                    return []
                
                data = res.json()
                products = data.get("products", [])
                
                for prod in products:
                    title = prod.get("title", "")
                    handle = prod.get("handle", "")
                    variants = prod.get("variants", [])
                    images = prod.get("images", [])
                    img_url = images[0].get("src", "") if images else ""

                    for v in variants:
                        price = float(v.get("price") or 0)
                        compare_price = float(v.get("compare_at_price") or 0)
                        
                        if compare_price > price and compare_price > 0:
                            discount_pct = round(((compare_price - price) / compare_price) * 100)
                            if discount_pct >= min_discount_percent:
                                deals.append({
                                    "title": f"{self.brand_id.title()}: {discount_pct}% Off {title}",
                                    "raw_description": f"Price cut on {title}. Reduced from {compare_price} to {price}.",
                                    "brand_id": self.brand_id,
                                    "discount_percent": discount_pct,
                                    "product_url": f"{self.brand_domain}/products/{handle}",
                                    "image_url": img_url,
                                    "country": self.country,
                                    "source": "shopify_feed"
                                })
                                break # One variant per product is sufficient
        except Exception as e:
            print(f"Error fetching Shopify deals for {self.brand_id}: {e}")
            
        return deals

if __name__ == "__main__":
    collector = ShopifyCollector("https://pk.khaadi.com", "khaadi", "PK")
    deals = collector.fetch_price_drops(min_discount_percent=30)
    print(f"Discovered {len(deals)} qualifying price drops.")
