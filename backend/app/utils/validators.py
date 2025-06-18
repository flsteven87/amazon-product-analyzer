"""
Validation utilities for Amazon Product Analyzer.

This module provides validation functions for Amazon URLs, ASINs,
and other input data validation.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


def validate_amazon_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the URL is a valid Amazon product URL.
    
    Args:
        url (str): URL to validate.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        parsed_url = urlparse(url)
        
        # Check if domain is Amazon
        amazon_domains = [
            'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr',
            'amazon.it', 'amazon.es', 'amazon.ca', 'amazon.com.au',
            'amazon.co.jp', 'amazon.in', 'amazon.com.br', 'amazon.com.mx'
        ]
        
        domain = parsed_url.netloc.lower()
        if not any(amazon_domain in domain for amazon_domain in amazon_domains):
            return False, "URL must be from an Amazon domain"
        
        # Check if URL contains product identifier patterns
        path = parsed_url.path.lower()
        product_patterns = ['/dp/', '/product/', '/gp/product/']
        
        if not any(pattern in path for pattern in product_patterns):
            return False, "URL must be a valid Amazon product page"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_asin(asin: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Amazon Standard Identification Number (ASIN).
    
    Args:
        asin (str): ASIN to validate.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not asin:
        return False, "ASIN cannot be empty"
    
    # ASIN should be 10 characters long
    if len(asin) != 10:
        return False, "ASIN must be exactly 10 characters long"
    
    # ASIN should contain only alphanumeric characters
    if not re.match(r'^[A-Z0-9]{10}$', asin.upper()):
        return False, "ASIN must contain only alphanumeric characters"
    
    return True, None


def validate_price(price: Optional[float]) -> Tuple[bool, Optional[str]]:
    """
    Validate product price.
    
    Args:
        price (Optional[float]): Price to validate.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if price is None:
        return True, None  # Price is optional
    
    if price < 0:
        return False, "Price cannot be negative"
    
    if price > 1000000:  # Reasonable upper limit
        return False, "Price seems unreasonably high"
    
    return True, None


def validate_rating(rating: Optional[float]) -> Tuple[bool, Optional[str]]:
    """
    Validate product rating.
    
    Args:
        rating (Optional[float]): Rating to validate.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if rating is None:
        return True, None  # Rating is optional
    
    if not (0 <= rating <= 5):
        return False, "Rating must be between 0 and 5"
    
    return True, None


def validate_review_count(review_count: Optional[int]) -> Tuple[bool, Optional[str]]:
    """
    Validate product review count.
    
    Args:
        review_count (Optional[int]): Review count to validate.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if review_count is None:
        return True, None  # Review count is optional
    
    if review_count < 0:
        return False, "Review count cannot be negative"
    
    return True, None 