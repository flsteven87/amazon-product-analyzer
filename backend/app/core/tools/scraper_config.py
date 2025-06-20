"""Configuration for the scraper and agents."""

import os
from typing import Dict, Any

# Scraper configuration
SCRAPER_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1.0,
    "headers": {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
}

# Platform specific configurations
PLATFORM_CONFIGS = {
    "amazon": {
        "domains": ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.it", "amazon.es"],
        "selectors": {
            "title": [
                "#productTitle",
                ".product-title",
                "h1[data-automation-id='product-title']",
            ],
            "price": [
                ".apexPriceToPay .a-offscreen",
                ".a-price-range .a-offscreen",
                ".a-price .a-offscreen",
                "span[data-a-color='price'] .a-offscreen",
                "[data-a-price]",
                ".a-price-whole",  # Fallback
            ],
            "rating": [
                "#averageCustomerReviews .a-icon-star .a-icon-alt",
                "i[class*='a-star-'] .a-icon-alt",
                ".reviewCountTextLinkedHistogram .a-icon-alt",
                "[title*='out of 5 stars']",
                ".a-icon-alt",  # Fallback
            ],
            "review_count": [
                "#acrCustomerReviewText",
                "span[aria-label*='ratings']",
                "span[aria-label*='Reviews']",
                ".a-size-base[aria-label*='Reviews']",
                "[data-hook='total-review-count']",
                ".reviewCountTextLinkedHistogram .a-size-base",
            ],
            "availability": [
                "#availability span",
                "[data-feature-name='availability'] span",
                ".a-color-success",
                ".a-color-state",
            ],
            "features": [
                "#feature-bullets ul li",
                ".a-unordered-list .a-list-item",
                "[data-feature-name='featurebullets'] ul li",
            ],
            "images": [
                "#landingImage",
                ".a-dynamic-image",
                "[data-action='main-image-click'] img",
            ],
            "seller": [
                "#sellerProfileTriggerId",
                "[data-feature-name='bylineInfo'] .a-link-normal",
                ".po-brand .a-link-normal",
            ],
            "category": [
                "#wayfinding-breadcrumbs_feature_div ul li",
                ".a-breadcrumb .a-list-item",
                "[data-feature-name='breadcrumbs'] ul li",
            ],
        },
    }
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 10,
    "delay_between_requests": 6.0,  # seconds
}


def get_scraper_config() -> Dict[str, Any]:
    """Get scraper configuration."""
    return SCRAPER_CONFIG.copy()


def get_platform_config(platform: str) -> Dict[str, Any]:
    """Get platform-specific configuration."""
    return PLATFORM_CONFIGS.get(platform, {})


def get_rate_limit_config() -> Dict[str, Any]:
    """Get rate limiting configuration."""
    return RATE_LIMIT_CONFIG.copy()
