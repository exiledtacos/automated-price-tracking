"""
Example script showing how to use the Gemini Bulk Scraper.

This script demonstrates:
1. How to initialize the scraper
2. How to scrape a single URL
3. How to scrape multiple URLs in bulk
4. How to save scraped data to the database

Before running:
- Make sure GEMINI_API_KEY is set in your .env file
- Add actual product URLs to test with
"""

import asyncio
import os
from src.scripts.gemini_bulk_scraper import GeminiBulkScraper


async def example_single_scrape():
    """Example: Scrape a single URL"""
    print("\n=== Example 1: Single URL Scraping ===")
    
    scraper = GeminiBulkScraper()
    
    # Replace with a real product URL
    url = "https://www.example.com/product/123"
    
    print(f"Scraping: {url}")
    result = await scraper.scrape_url(url)
    
    if result:
        print(f"✓ Success!")
        print(f"  Name: {result['name']}")
        print(f"  Price: {result['price']} {result['currency']}")
        print(f"  Image: {result['main_image_url']}")
    else:
        print("✗ Failed to scrape")


async def example_bulk_scrape():
    """Example: Scrape multiple URLs without saving to database"""
    print("\n=== Example 2: Bulk Scraping (No Database) ===")
    
    scraper = GeminiBulkScraper()
    
    # Replace with real product URLs
    urls = [
        "https://www.example.com/product/123",
        "https://www.example.com/product/456",
        "https://www.example.com/product/789",
    ]
    
    print(f"Scraping {len(urls)} URLs...")
    products = await scraper.scrape_bulk(urls)
    
    print(f"\n✓ Successfully scraped {len(products)}/{len(urls)} products:")
    for product in products:
        print(f"  - {product.name}: ${product.price:.2f} {product.currency}")


async def example_scrape_and_save():
    """Example: Scrape and save to database"""
    print("\n=== Example 3: Scrape and Save to Database ===")
    
    scraper = GeminiBulkScraper()
    
    # Replace with real product URLs
    urls = [
        "https://www.amazon.com/dp/B08N5WRWNW",  # Example Amazon product
        "https://www.bestbuy.com/site/example/1234567.p",  # Example Best Buy product
    ]
    
    print(f"Scraping and saving {len(urls)} products...")
    saved_count = await scraper.scrape_and_save(urls)
    
    print(f"\n✓ Saved {saved_count} products to database")


async def main():
    """Run all examples"""
    
    # Check if API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("\nPlease add it to your .env file:")
        print("  GEMINI_API_KEY=your_api_key_here")
        print("\nGet your API key at: https://makersuite.google.com/app/apikey")
        return
    
    print("Gemini Bulk Scraper - Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    
    # await example_single_scrape()
    # await example_bulk_scrape()
    # await example_scrape_and_save()
    
    print("\n⚠ No examples are currently enabled.")
    print("\nTo run these examples:")
    print("1. Uncomment the example function calls in main()")
    print("2. Replace example URLs with real product URLs")
    print("3. Run: python src/scripts/example_gemini_scraper.py")


if __name__ == "__main__":
    asyncio.run(main())
