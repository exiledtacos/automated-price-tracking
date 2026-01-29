"""
Simple test to verify Gemini scraper works with a real URL.
This is a manual test - run it when you have a GEMINI_API_KEY set.
"""
import asyncio
from dotenv import load_dotenv
from src.services.gemini_scraper import GeminiScraper

load_dotenv()

async def test_scrape():
    scraper = GeminiScraper()
    test_url = "https://barnerbrand.com/products/holly-glossy"
    
    # Test scrape the URL
    data = await scraper.scrape_url(test_url)
    if data:
        print(f"Successfully scraped: {data['name']}")
        print(f"Price: {data['price']} {data['currency']}")
    else:
        print("Failed to scrape")

if __name__ == "__main__":
    asyncio.run(test_scrape())

