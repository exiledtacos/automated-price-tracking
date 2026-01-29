from typing import Tuple
from urllib.parse import urlparse

from src.domain.models import ProductCreate, PriceHistoryCreate
from src.infrastructure.repositories.product_repository import ProductRepository
from src.services.gemini_scraper import GeminiScraper


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.repository = product_repository
        self.gemini_scraper = GeminiScraper()

    async def add_product(self, url: str) -> Tuple[bool, str]:
        """Add a new product to track"""
        if not self._validate_url(url):
            return False, "Please enter a valid URL"

        try:
            # Check if product exists
            existing_product = self.repository.get(url)
            if existing_product:
                return False, "Product already being tracked!"

            # Scrape product using Gemini
            scraped_product = await self.gemini_scraper.scrape_product(url)
            
            if not scraped_product:
                return False, "Failed to scrape product data. Please check the URL."

            # Create product
            product = self.repository.add(scraped_product)

            # Add initial price history
            price_history = PriceHistoryCreate(
                product_url=product.url, price=product.price, product_name=product.name
            )
            self.repository.add_price_history(price_history)

            return (
                True,
                f"Added and checked initial price for: {product.name} - ${product.price:.2f}",
            )

        except Exception as e:
            print(f"Error: {str(e)}")
            return False, f"Error adding product: {str(e)}"

    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def remove_product(self, url: str) -> None:
        """Remove a product and its price history"""
        product = self.repository.get(url)
        if product:
            self.repository.delete(url)
