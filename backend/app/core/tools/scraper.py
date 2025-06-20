"""Core scraper functionality for product data collection."""

import asyncio
import time
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import logging

import httpx
from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser

from .product_parser import ProductData, TextProcessor
from .competitor_extractor import AmazonCompetitorExtractor, CompetitorCandidate
from .scraper_config import get_scraper_config, get_platform_config, get_rate_limit_config


logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Custom exception for scraping errors."""

    pass


class RateLimiter:
    """Simple rate limiter to avoid overwhelming servers."""

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute
        self.last_request_time = 0

    async def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()


class ProductScraper:
    """Main scraper class for product data extraction."""

    def __init__(self):
        self.config = get_scraper_config()
        self.rate_limit_config = get_rate_limit_config()
        self.rate_limiter = RateLimiter(self.rate_limit_config["requests_per_minute"])
        self.text_processor = TextProcessor()
        self.competitor_extractor = AmazonCompetitorExtractor()

        # Create HTTP client with configuration
        self.client = httpx.AsyncClient(
            timeout=self.config["timeout"],
            headers=self.config["headers"],
            follow_redirects=True,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    def is_supported(self, url: str) -> bool:
        """Check if the URL is from a supported platform."""
        platform = self.text_processor.detect_platform(url)
        return platform in ["amazon"]  # Currently only Amazon is supported

    async def scrape(self, url: str) -> ProductData:
        """Scrape product data from the given URL.

        Args:
            url: Product URL to scrape

        Returns:
            ProductData: Extracted product information

        Raises:
            ScrapingError: If scraping fails or URL is not supported
        """
        if not self.is_supported(url):
            raise ScrapingError(f"Unsupported platform for URL: {url}")

        platform = self.text_processor.detect_platform(url)
        logger.info(f"Scraping {platform} product: {url}")

        # Apply rate limiting
        await self.rate_limiter.wait_if_needed()

        # Attempt scraping with retries
        for attempt in range(self.config["max_retries"]):
            try:
                html_content = await self._fetch_html(url)
                product_data = await self._parse_product_data(url, html_content, platform)

                if product_data.is_valid():
                    logger.info(f"Successfully scraped product: {product_data.title}")
                    return product_data
                else:
                    raise ScrapingError("Extracted product data is incomplete")

            except Exception as e:
                logger.warning(f"Scraping attempt {attempt + 1} failed: {str(e)}")

                if attempt == self.config["max_retries"] - 1:
                    raise ScrapingError(f"Failed to scrape after {self.config['max_retries']} attempts: {str(e)}")

                # Wait before retry
                await asyncio.sleep(self.config["retry_delay"] * (attempt + 1))

        raise ScrapingError("Unexpected error in scraping loop")

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # Check if we got blocked
            if "blocked" in response.text.lower() or response.status_code == 503:
                raise ScrapingError("Request was blocked by the server")

            return response.text

        except httpx.HTTPStatusError as e:
            raise ScrapingError(f"HTTP error {e.response.status_code}: {e.response.text[:200]}")
        except httpx.RequestError as e:
            raise ScrapingError(f"Request error: {str(e)}")

    async def _parse_product_data(self, url: str, html: str, platform: str) -> ProductData:
        """Parse product data from HTML content."""
        platform_config = get_platform_config(platform)
        selectors = platform_config.get("selectors", {})

        # Use selectolax for faster parsing
        tree = HTMLParser(html)

        # Also create BeautifulSoup instance for fallback
        soup = BeautifulSoup(html, "lxml")

        product_data = ProductData(url=url)

        # Extract each field
        product_data.title = self._extract_text_field(tree, soup, selectors.get("title", []))

        price_text = self._extract_text_field(tree, soup, selectors.get("price", []))
        product_data.price = self.text_processor.extract_price(price_text)
        product_data.currency = self.text_processor.extract_currency(price_text)

        rating_text = self._extract_text_field(tree, soup, selectors.get("rating", []))
        product_data.rating = self.text_processor.extract_rating(rating_text)

        review_text = self._extract_text_field(tree, soup, selectors.get("review_count", []))
        product_data.review_count = self.text_processor.extract_review_count(review_text)

        product_data.availability = self._extract_text_field(tree, soup, selectors.get("availability", []))
        product_data.seller = self._extract_text_field(tree, soup, selectors.get("seller", []))
        product_data.category = self._extract_text_field(tree, soup, selectors.get("category", []))

        # Extract features (multiple elements)
        product_data.features = self._extract_list_field(tree, soup, selectors.get("features", []))

        # Extract images
        product_data.images = self._extract_image_urls(tree, soup, selectors.get("images", []))

        # Store raw extracted data for debugging
        product_data.raw_data = {
            "price_text": price_text,
            "rating_text": rating_text,
            "review_text": review_text,
            "selectors_used": selectors,
        }

        return product_data

    async def scrape_with_competitors(self, url: str) -> Dict[str, Any]:
        """Scrape product data and discover competitors from Amazon recommendations.

        Args:
            url: Product URL to scrape

        Returns:
            Dict containing main product data and competitor candidates
        """
        if not self.is_supported(url):
            raise ScrapingError(f"Unsupported platform for URL: {url}")

        logger.info(f"Scraping product with competitor discovery: {url}")

        # Apply rate limiting
        await self.rate_limiter.wait_if_needed()

        try:
            # Get the HTML content
            response = await self.client.get(url)
            response.raise_for_status()
            html_content = response.text

            # Extract main product data
            platform = self.text_processor.detect_platform(url)
            main_product = await self._parse_product_data(url, html_content, platform)

            # Extract ASIN from URL for competitor filtering
            main_asin = self._extract_asin_from_url(url)

            # Extract competitor candidates from recommendation sections
            competitors = []
            if main_asin:
                try:
                    competitors = await self.competitor_extractor.extract_competitors(html_content, main_asin)
                    logger.info(f"Found {len(competitors)} competitor candidates")
                except Exception as e:
                    logger.warning(f"Competitor extraction failed: {str(e)}")

            return {
                "main_product": main_product,
                "competitor_candidates": competitors,
                "main_asin": main_asin,
                "extraction_success": True,
            }

        except Exception as e:
            logger.error(f"Failed to scrape with competitors: {str(e)}")
            raise ScrapingError(f"Scraping failed: {str(e)}")

    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon product URL."""
        import re

        # Common Amazon URL patterns for ASIN extraction
        patterns = [
            r"/dp/([A-Z0-9]{10})",  # /dp/B08N5WRWNW
            r"/gp/product/([A-Z0-9]{10})",  # /gp/product/B08N5WRWNW
            r"/product/([A-Z0-9]{10})",  # /product/B08N5WRWNW
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                asin = match.group(1).upper()
                # Validate ASIN format (10 characters, alphanumeric)
                if len(asin) == 10 and asin.isalnum():
                    return asin

        return None

    def _extract_text_field(self, tree: HTMLParser, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text from the first matching selector."""
        for selector in selectors:
            try:
                # Try selectolax first (faster)
                element = tree.css_first(selector)
                if element and element.text():
                    return self.text_processor.clean_text(element.text())

                # Fallback to BeautifulSoup
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return self.text_processor.clean_text(text)

            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {str(e)}")
                continue

        return None

    def _extract_list_field(self, tree: HTMLParser, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract text from all matching elements."""
        results = []

        for selector in selectors:
            try:
                # Try selectolax first
                elements = tree.css(selector)
                for element in elements:
                    if element.text():
                        text = self.text_processor.clean_text(element.text())
                        if text and text not in results:
                            results.append(text)

                # If we got results, don't try other selectors
                if results:
                    break

                # Fallback to BeautifulSoup
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text:
                        text = self.text_processor.clean_text(text)
                        if text and text not in results:
                            results.append(text)

                # If we got results, don't try other selectors
                if results:
                    break

            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {str(e)}")
                continue

        return results[:10]  # Limit to avoid too many features

    def _extract_image_urls(self, tree: HTMLParser, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract image URLs from matching elements."""
        urls = []

        for selector in selectors:
            try:
                # Try selectolax first
                elements = tree.css(selector)
                for element in elements:
                    src = element.attributes.get("src") or element.attributes.get("data-src")
                    if src and self._is_valid_image_url(src):
                        if src not in urls:
                            urls.append(src)

                # If we got results, don't try other selectors
                if urls:
                    break

                # Fallback to BeautifulSoup
                elements = soup.select(selector)
                for element in elements:
                    src = element.get("src") or element.get("data-src")
                    if src and self._is_valid_image_url(src):
                        if src not in urls:
                            urls.append(src)

                # If we got results, don't try other selectors
                if urls:
                    break

            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {str(e)}")
                continue

        return urls[:5]  # Limit to avoid too many images

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL appears to be a valid image URL."""
        if not url:
            return False

        # Skip placeholder and invalid URLs
        if any(skip in url.lower() for skip in ["placeholder", "spacer", "pixel", "blank"]):
            return False

        # Must be HTTP/HTTPS
        if not url.startswith(("http://", "https://", "//")):
            return False

        return True
