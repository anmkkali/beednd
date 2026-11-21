"""
Master Pipeline Orchestrator
Runs collectors, enriches with Gemini AI, and outputs JSON files to src/content/deals/
"""

import os
import json
import uuid
from datetime import datetime, timezone
from collectors.shopify_collector import ShopifyCollector
from collectors.bank_portal_collector import BankPortalCollector
from collectors import shopify_sales

DEALS_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "content", "deals")

def run_pipeline():
    os.makedirs(DEALS_DIR, exist_ok=True)
    print("Starting automated DealsSite ingestion pipeline...")
    
    # 1. Scrape Shopify brands (e.g. Khaadi)
    print("Collecting brand price drops...")
    shopify_sources = [
        ("https://pk.khaadi.com", "khaadi", "PK")
    ]
    
    for url, brand_id, country in shopify_sources:
        collector = ShopifyCollector(url, brand_id, country)
        drops = collector.fetch_price_drops(min_discount_percent=30)
        print(f"[{brand_id}] Collected {len(drops)} qualifying price drops.")

    # 2. Real store markdowns (compare_at_price vs price) written straight to src/content/deals/
    print("Collecting store sale deals...")
    shopify_sales.main()

    print("Pipeline run completed successfully.")

if __name__ == "__main__":
    run_pipeline()
