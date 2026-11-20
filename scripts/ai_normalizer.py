"""
Gemini 2.5 Flash Structured Ingestion Normalizer
Uses official Google GenAI SDK to normalize unstructured deal data into validated Zod-ready JSON.
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

class NormalizedDeal(BaseModel):
    id: str = Field(description="URL safe unique slug, e.g. 'khaadi-summer-sale-50-off'")
    title: str = Field(description="Clear SEO headline, max 100 characters")
    short_description: str = Field(description="Concise description of the deal")
    brand_id: str = Field(description="Normalized brand id, e.g. 'khaadi', 'bluehost'")
    category: str = Field(description="clothing-fashion | tech-electronics | hosting-software | food-dining | beauty-wellness | travel-lifestyle")
    deal_type: str = Field(description="online | in-store | bank-card | promo-code | store-sale")
    discount_value: str = Field(description="e.g. '50% OFF', '$15 OFF'")
    numeric_discount_percent: Optional[int] = Field(default=None)
    promo_code: Optional[str] = Field(default=None)
    terms: List[str] = Field(default_factory=list)
    confidence_score: float = Field(description="0.0 to 1.0 confidence in deal validity")

class AINormalizer:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not set in environment.")
            self.client = None
        elif genai:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def normalize(self, raw_input: str) -> Optional[NormalizedDeal]:
        if not self.client:
            # Fallback simple generator if API key not provided during local testing
            return None
        
        prompt = f"""
        Extract and structure this discount into clean JSON.
        Normalize all claims into standard categories. Remove clickbait.
        Raw text:
        {raw_input}
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=NormalizedDeal,
                    temperature=0.1
                )
            )
            return NormalizedDeal.model_validate_json(response.text)
        except Exception as e:
            print(f"Gemini API normalization error: {e}")
            return None
