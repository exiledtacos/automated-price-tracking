"""
Bulk scraper using Google Gemini API to extract product data from URLs.
This script pulls product information (name, price, currency, image URL) from
multiple product URLs and stores them in the database.
"""
import asyncio
import os
from typing import List, Dict, Optional
from datetime import datetime, timezone
import aiohttp
import json

from src.domain.models import ProductCreate, PriceHistoryCreate
from src.infrastructure.database import get_session
from src.infrastructure.repositories.product_repository import ProductRepository


class GeminiBulkScraper:
    """Bulk scraper using Google Gemini API for extracting product data"""

    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 5):
        """
        Initialize the Gemini bulk scraper.
        
        Args:
            api_key: Google Gemini API key. If not provided, reads from GEMINI_API_KEY env var
            max_concurrent: Maximum number of concurrent requests (default: 5)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in environment or pass it to constructor."
            )
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def scrape_url(self, url: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """
        Scrape a single URL using Gemini API to extract product information.
        Gemini will fetch the URL directly and extract the data.
        
        Args:
            url: Product URL to scrape
            session: Shared aiohttp session for making requests
            
        Returns:
            Dictionary with product data or None if scraping fails
        """
        async with self.semaphore:  # Limit concurrent requests
            try:
                # Let Gemini fetch and extract product information directly from the URL
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
                
                # Call Gemini API (API key in URL is standard for this API)
                gemini_url = f"{self.base_url}?key={self.api_key}"
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": extraction_prompt
                        }]
                    }]
                }
                
                async with session.post(
                    gemini_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as gemini_response:
                    if gemini_response.status != 200:
                        error_text = await gemini_response.text()
                        print(f"Gemini API error: {error_text}")
                        return None
                    
                    result = await gemini_response.json()
                    
                    # Safely extract the generated text
                    try:
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
                            
                    except (KeyError, IndexError, AttributeError) as e:
                        print(f"Error parsing Gemini response structure for {url}: {e}")
                        return None
                            
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response for {url}: {e}")
                return None
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                return None
    
    async def scrape_bulk(self, urls: List[str]) -> List[ProductCreate]:
        """
        Scrape multiple URLs concurrently using a shared session.
        
        Args:
            urls: List of product URLs to scrape
            
        Returns:
            List of ProductCreate objects with scraped data
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.scrape_url(url, session) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        products = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                print(f"Exception scraping {url}: {result}")
                continue
            
            if result is not None:
                try:
                    # Create ProductCreate object
                    product = ProductCreate(
                        url=url,
                        name=result["name"],
                        price=float(result["price"]),
                        currency=result["currency"],
                        main_image_url=result["main_image_url"],
                        check_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    )
                    products.append(product)
                except Exception as e:
                    print(f"Error creating product from data for {url}: {e}")
                    continue
        
        return products
    
    async def scrape_and_save(self, urls: List[str]) -> int:
        """
        Scrape multiple URLs and save them to the database.
        
        Args:
            urls: List of product URLs to scrape
            
        Returns:
            Number of products successfully saved
        """
        products = await self.scrape_bulk(urls)
        
        session = next(get_session())
        repository = ProductRepository(session)
        saved_count = 0
        
        try:
            for product in products:
                try:
                    # Check if product already exists
                    existing = repository.get(product.url)
                    if existing:
                        # Only update if price has changed
                        if existing.price != product.price:
                            print(f"Price changed for {product.name}: ${existing.price:.2f} -> ${product.price:.2f}")
                            
                            # Add price history entry
                            price_history = PriceHistoryCreate(
                                product_url=product.url,
                                price=product.price,
                                product_name=product.name
                            )
                            repository.add_price_history(price_history)
                            
                            # Update product price
                            existing.price = product.price
                            existing.check_date = product.check_date
                            repository.update(existing)
                            saved_count += 1
                        else:
                            print(f"Product price unchanged: {product.name} (${product.price:.2f})")
                    else:
                        # Add new product
                        saved_product = repository.add(product)
                        
                        # Add initial price history
                        price_history = PriceHistoryCreate(
                            product_url=saved_product.url,
                            price=saved_product.price,
                            product_name=saved_product.name
                        )
                        repository.add_price_history(price_history)
                        
                        print(f"Added new product: {saved_product.name} - ${saved_product.price:.2f}")
                        saved_count += 1
                        
                except Exception as e:
                    print(f"Error saving product {product.name}: {e}")
                    continue
        finally:
            session.close()
        
        return saved_count


async def main():
    """Main function to demonstrate bulk scraping"""
    # Example usage - replace with actual product URLs
    urls = [
        # Add your product URLs here
        # "https://www.amazon.com/dp/B08N5WRWNW",
        # "https://www.bestbuy.com/site/example-product/1234567.p",
    ]
    
    if not urls:
        print("No URLs provided. Please add product URLs to the 'urls' list in the main() function.")
        print("\nUsage:")
        print("1. Set GEMINI_API_KEY environment variable")
        print("2. Add product URLs to the 'urls' list")
        print("3. Run: python -m src.scripts.gemini_bulk_scraper")
        return
    
    scraper = GeminiBulkScraper()
    
    print(f"Starting bulk scrape of {len(urls)} products...")
    saved_count = await scraper.scrape_and_save(urls)
    print(f"\nCompleted! Successfully processed {saved_count}/{len(urls)} products.")


if __name__ == "__main__":
    asyncio.run(main())
