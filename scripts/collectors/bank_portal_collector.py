"""
Bank Portal Collector
Scrapes public bank promotions and card discount directories (HBL, Meezan, Bank Alfalah).
Extracts participating merchant names, card requirements, and discount percentages.
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class BankPortalCollector:
    def __init__(self, bank_id: str, directory_url: str):
        self.bank_id = bank_id
        self.directory_url = directory_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 DealsSiteVerification/1.0"
        }

    def scrape_bank_offers(self) -> List[Dict[str, Any]]:
        offers = []
        try:
            with httpx.Client(timeout=20.0, headers=self.headers, follow_redirects=True) as client:
                res = client.get(self.directory_url)
                if res.status_code != 200:
                    print(f"[{self.bank_id}] HTTP error {res.status_code}")
                    return []
                
                soup = BeautifulSoup(res.text, "html.parser")
                # Look for common promotion card patterns in bank portals
                cards = soup.select(".card, .discount-item, .offer-box, .promotion-item")
                
                for card in cards[:20]: # Parse top items
                    text = card.get_text(" ", strip=True)
                    if any(term in text.lower() for term in ["discount", "% off", "cashback", "save"]):
                        offers.append({
                            "bank_id": self.bank_id,
                            "raw_text": text[:500],
                            "source_url": self.directory_url
                        })
        except Exception as e:
            print(f"Error parsing bank portal for {self.bank_id}: {e}")
            
        return offers

if __name__ == "__main__":
    collector = BankPortalCollector("hbl", "https://www.hbl.com/personal/cards/discounts-and-promotions")
    items = collector.scrape_bank_offers()
    print(f"Parsed {len(items)} raw promotional items for HBL.")
