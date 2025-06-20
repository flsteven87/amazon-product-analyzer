"""Product data models and parsing utilities."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse


@dataclass
class ProductData:
    """Standardized product data structure."""

    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    features: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    seller: Optional[str] = None
    category: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "rating": self.rating,
            "review_count": self.review_count,
            "availability": self.availability,
            "features": self.features,
            "images": self.images,
            "seller": self.seller,
            "category": self.category,
            "raw_data": self.raw_data,
        }

    def is_valid(self) -> bool:
        """Check if product data has minimum required fields."""
        return bool(self.url and self.title)
    
    def get_quality_score(self) -> float:
        """Calculate data quality score (0.0-1.0) based on completeness and validity."""
        score = 0.0
        
        # Basic requirements (0.4 points)
        if self.url and self.title:
            score += 0.4
        
        # Pricing information (0.2 points)
        if self.price is not None and self.price > 0:
            score += 0.15
        if self.currency:
            score += 0.05
            
        # Rating and reviews (0.2 points)
        if self.rating is not None and 0 <= self.rating <= 5:
            score += 0.1
        if self.review_count is not None and self.review_count > 0:
            score += 0.1
            
        # Additional details (0.2 points)
        if self.availability:
            score += 0.05
        if self.seller:
            score += 0.05
        if self.category:
            score += 0.05
        if self.features and len(self.features) > 0:
            score += 0.05
            
        return min(score, 1.0)
    
    def get_validation_issues(self) -> List[str]:
        """Get list of validation issues with the product data."""
        issues = []
        
        # Critical issues
        if not self.url:
            issues.append("Missing product URL")
        if not self.title:
            issues.append("Missing product title")
            
        # Quality issues
        if self.price is None:
            issues.append("Missing price information")
        elif self.price <= 0:
            issues.append("Invalid price (must be positive)")
            
        if self.rating is not None and (self.rating < 0 or self.rating > 5):
            issues.append("Invalid rating (must be 0-5)")
            
        if self.review_count is not None and self.review_count < 0:
            issues.append("Invalid review count (must be non-negative)")
            
        # Completeness warnings
        if not self.currency and self.price is not None:
            issues.append("Price provided but currency missing")
        if not self.availability:
            issues.append("Availability status missing")
        if not self.seller:
            issues.append("Seller information missing")
        if not self.category:
            issues.append("Product category missing")
        if not self.features or len(self.features) == 0:
            issues.append("Product features missing")
            
        return issues

    def get_summary(self) -> str:
        """Get a human-readable summary of the product."""
        summary_parts = []

        if self.title:
            summary_parts.append(f"Title: {self.title}")

        if self.price is not None and self.currency:
            summary_parts.append(f"Price: {self.currency}{self.price:.2f}")
        elif self.price is not None:
            summary_parts.append(f"Price: ${self.price:.2f}")

        if self.rating is not None:
            rating_str = f"Rating: {self.rating:.1f}/5"
            if self.review_count:
                rating_str += f" ({self.review_count:,} reviews)"
            summary_parts.append(rating_str)

        if self.availability:
            summary_parts.append(f"Availability: {self.availability}")

        if self.seller:
            summary_parts.append(f"Seller: {self.seller}")

        if self.category:
            summary_parts.append(f"Category: {self.category}")

        if self.features:
            features_preview = self.features[:3]  # Show first 3 features
            if len(self.features) > 3:
                features_preview.append(f"... and {len(self.features) - 3} more")
            summary_parts.append(f"Key Features: {', '.join(features_preview)}")

        return "\n".join(summary_parts)


class TextProcessor:
    """Utility class for processing and cleaning scraped text."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Remove extra whitespace and normalize
        text = re.sub(r"\s+", " ", text.strip())

        # Remove common unwanted characters
        text = text.replace("\u00a0", " ")  # Non-breaking space
        text = text.replace("\u200b", "")  # Zero-width space

        return text

    @staticmethod
    def extract_price(text: str) -> Optional[float]:
        """Extract price from text with Amazon-specific improvements."""
        if not text:
            return None

        # Handle Amazon price ranges (e.g., "$43.95 - $89.99")
        if "-" in text and "$" in text:
            prices = text.split("-")
            if len(prices) >= 2:
                # Extract the first price from a range
                first_price_text = prices[0].strip()
                cleaned = re.sub(r"[^\d.,]", "", first_price_text)
                try:
                    return float(cleaned.replace(",", ""))
                except (ValueError, TypeError):
                    pass

        # Remove currency symbols and spaces
        cleaned = re.sub(r"[^\d.,]", "", text)

        # Handle different decimal separators
        if "," in cleaned and "." in cleaned:
            # Both comma and dot - assume comma is thousands separator
            cleaned = cleaned.replace(",", "")
        elif "," in cleaned and cleaned.count(",") == 1:
            # Single comma might be decimal separator (European format)
            if len(cleaned.split(",")[1]) == 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def extract_rating(text: str) -> Optional[float]:
        """Extract rating from text with improved Amazon patterns."""
        if not text:
            return None

        # Look for patterns like "4.5 out of 5" or "4.5 stars"
        patterns = [
            r"(\d+\.?\d*)\s*out\s*of\s*5\s*stars?",  # "4.5 out of 5 stars"
            r"(\d+\.?\d*)\s*out\s*of\s*5",  # "4.5 out of 5"
            r"(\d+\.?\d*)\s*stars?",  # "4.5 stars"
            r"(\d+\.?\d*)\s*/\s*5",  # "4.5/5"
            r"(\d+\.?\d*)",  # Just a number (fallback)
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    rating = float(match.group(1))
                    if 0 <= rating <= 5:
                        return rating
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def extract_review_count(text: str) -> Optional[int]:
        """Extract review count from text with Amazon-specific patterns."""
        if not text:
            return None

        # Look for patterns like "5,003 ratings" or "1,234 Reviews"
        patterns = [
            r"([\d,]+)\s*ratings?",
            r"([\d,]+)\s*reviews?",
            r"([\d,]+)\s*customer\s*reviews?",
            r"([\d,]+)",  # Just numbers with commas
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                # Remove commas and convert to int
                cleaned = match.group(1).replace(",", "")
                try:
                    count = int(cleaned)
                    return count if count > 0 else None
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def extract_currency(text: str) -> Optional[str]:
        """Extract currency symbol from price text."""
        if not text:
            return None

        currency_symbols = {
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
            "¥": "JPY",
            "₹": "INR",
        }

        for symbol, code in currency_symbols.items():
            if symbol in text:
                return code

        # Look for currency codes
        currency_match = re.search(r"\b(USD|EUR|GBP|JPY|INR|CAD|AUD)\b", text.upper())
        if currency_match:
            return currency_match.group(1)

        return None

    @staticmethod
    def detect_platform(url: str) -> str:
        """Detect the e-commerce platform from URL."""
        domain = urlparse(url).netloc.lower()

        if "amazon" in domain:
            return "amazon"
        elif "ebay" in domain:
            return "ebay"
        elif "walmart" in domain:
            return "walmart"
        elif "target" in domain:
            return "target"
        else:
            return "unknown"
