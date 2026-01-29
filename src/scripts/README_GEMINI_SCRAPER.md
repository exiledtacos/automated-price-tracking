# Gemini Bulk Scraper

A bulk web scraping tool that uses Google's Gemini API to extract product information from multiple URLs concurrently.

## Why Gemini?

- **Direct URL Fetching**: Gemini can directly fetch and parse web pages - no need for separate HTTP requests
- **Bulk Processing**: Scrapes multiple URLs concurrently for faster processing
- **Free Tier**: Gemini API offers a generous free tier perfect for personal projects
- **Smart Extraction**: AI-powered extraction understands product page structure automatically
- **No Extra Dependencies**: No need for additional scraping libraries

## Setup

1. **Get a Gemini API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key

2. **Add to Environment Variables**:
   ```bash
   # Add to your .env file
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

### Command Line

```bash
# Run the bulk scraper
python -m src.scripts.gemini_bulk_scraper
```

### Programmatic Usage

```python
import asyncio
from src.scripts.gemini_bulk_scraper import GeminiBulkScraper

async def scrape_products():
    scraper = GeminiBulkScraper()
    
    urls = [
        "https://www.amazon.com/dp/B08N5WRWNW",
        "https://www.bestbuy.com/site/example-product/1234567.p",
    ]
    
    # Scrape and save to database
    saved_count = await scraper.scrape_and_save(urls)
    print(f"Saved {saved_count} products")

asyncio.run(scrape_products())
```

### Just Scraping (No Database)

```python
import asyncio
from src.scripts.gemini_bulk_scraper import GeminiBulkScraper

async def scrape_only():
    scraper = GeminiBulkScraper()
    
    urls = ["https://www.amazon.com/dp/B08N5WRWNW"]
    
    # Just get the data, don't save
    products = await scraper.scrape_bulk(urls)
    
    for product in products:
        print(f"{product.name}: ${product.price} {product.currency}")

asyncio.run(scrape_only())
```

## Features

- **Concurrent Scraping**: Processes multiple URLs simultaneously
- **Error Handling**: Continues processing even if some URLs fail
- **Database Integration**: Automatically saves products and price history
- **Duplicate Detection**: Updates existing products instead of creating duplicates
- **Price History Tracking**: Records price changes over time

## Data Extracted

The scraper extracts the following information from each product page:

- Product name/title
- Current price (numeric value)
- Currency code (USD, EUR, GBP, etc.)
- Main product image URL

## Limitations

- **HTML Content Length**: Truncates HTML to 8000 characters to avoid token limits
- **API Rate Limits**: Subject to Gemini API rate limits
- **Accuracy**: Depends on Gemini's ability to interpret HTML structure
- **Website Structure**: May not work well with JavaScript-heavy single-page applications

## Troubleshooting

### "GEMINI_API_KEY not found"

Make sure you've added the key to your `.env` file:
```bash
GEMINI_API_KEY=your_actual_key_here
```

### "Failed to parse JSON response"

The Gemini API might return text instead of JSON. This can happen if:
- The HTML content is too complex
- The product page structure is unusual
- The API is having issues

Try reducing the number of URLs or simplifying the prompt.

### "Failed to fetch URL: HTTP 403"

Some websites block automated scrapers. You may need to:
- Try different product pages from the same site
- Use simpler product pages instead of JavaScript-heavy single-page applications
- Note: Gemini fetches pages directly, so traditional anti-bot measures may still work

## How It Works

1. **URL Submission**: You provide product URLs to the scraper
2. **Direct Fetch**: Gemini API fetches the page content directly (no separate HTTP request needed)
3. **AI Extraction**: Gemini's AI parses the HTML and extracts structured product data
4. **Validation**: The scraper validates the extracted data has all required fields
5. **Storage**: Products and prices are saved to the database with change tracking

## Example Output

```
Starting bulk scrape of 3 products...
Added new product: Sony WH-1000XM4 Headphones - $348.00
Price changed for Apple AirPods Pro: $249.00 -> $229.00
Added new product: Bose QuietComfort 45 - $329.00

Completed! Successfully processed 3/3 products.
```
