"""
Gemini-based scraper for extracting product information from URLs.
This module provides a simple interface for scraping product data using Google's Gemini API.
"""
import os
import json
import aiohttp
from typing import Optional, Dict
from datetime import datetime, timezone

from src.domain.models import ProductCreate


class GeminiScraper:
    """Simple Gemini API scraper for product data extraction"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini scraper.
        
        Args:
            api_key: Google Gemini API key. If not provided, reads from GEMINI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in environment or pass it to constructor."
            )
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    async def scrape_url(self, url: str) -> Optional[Dict]:
        """
        Scrape a single URL using Gemini API.
        Gemini will fetch the URL directly and extract product information.
        
        Args:
            url: Product URL to scrape
            
        Returns:
            Dictionary with product data or None if scraping fails
        """
        try:
            extraction_prompt = f"""
            Visit this product page URL and extract the current product information: {url}
            
            Extract the following information from the page:
            - Product name/title
            - Current price (as a number, without currency symbols like $ or €)
            - Currency code (e.g., USD, EUR, GBP)
            - Main product image URL (full URL starting with http/https)
            
            Return ONLY a valid JSON object with these exact keys: name, price, currency, main_image_url
            Do not include any markdown formatting, code blocks, or explanations. Just the raw JSON.
            
            Example format:
            {{"name": "Product Name", "price": 99.99, "currency": "USD", "main_image_url": "https://example.com/image.jpg"}}
            """
            
            # Call Gemini API
            gemini_url = f"{self.base_url}?key={self.api_key}"
            payload = {
                "contents": [{
                    "parts": [{
                        "text": extraction_prompt
                    }]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    gemini_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Gemini API error: {error_text}")
                        return None
                    
                    result = await response.json()
            
            # Safely extract the generated text
            candidates = result.get("candidates", [])
            if not candidates:
                print(f"No candidates in Gemini response for {url}")
                return None
            
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text:
                print(f"Empty text in Gemini response for {url}")
                return None
            
            # Remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            product_data = json.loads(text)
            
            # Validate required fields
            required_fields = ["name", "price", "currency", "main_image_url"]
            if all(field in product_data for field in required_fields):
                return product_data
            else:
                print(f"Missing required fields in response for {url}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response for {url}: {e}")
            return None
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    async def scrape_product(self, url: str) -> Optional[ProductCreate]:
        """
        Scrape a URL and return a ProductCreate object.
        
        Args:
            url: Product URL to scrape
            
        Returns:
            ProductCreate object or None if scraping fails
        """
        data = await self.scrape_url(url)
        if data:
            try:
                return ProductCreate(
                    url=url,
                    name=data["name"],
                    price=float(data["price"]),
                    currency=data["currency"],
                    main_image_url=data["main_image_url"],
                    check_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                )
            except Exception as e:
                print(f"Error creating ProductCreate from data for {url}: {e}")
                return None
        return None
