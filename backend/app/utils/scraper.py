"""
Scraping utilities for Amazon Product Analyzer.

This module provides basic scraping utilities including URL parsing,
ASIN extraction, and helper functions for web scraping.
"""

import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs


def extract_asin_from_url(url: str) -> Optional[str]:
    """
    Extract ASIN from Amazon product URL.
    
    Args:
        url (str): Amazon product URL.
    
    Returns:
        Optional[str]: Extracted ASIN or None if not found.
    """
    try:
        # Common ASIN patterns in Amazon URLs
        asin_patterns = [
            r'/dp/([A-Z0-9]{10})',          # /dp/ASIN
            r'/product/([A-Z0-9]{10})',     # /product/ASIN
            r'/gp/product/([A-Z0-9]{10})',  # /gp/product/ASIN
            r'asin=([A-Z0-9]{10})',         # asin=ASIN in query params
        ]
        
        for pattern in asin_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
        
    except Exception:
        return None


def parse_amazon_url(url: str) -> Dict[str, Any]:
    """
    Parse Amazon URL and extract useful information.
    
    Args:
        url (str): Amazon product URL.
    
    Returns:
        Dict[str, Any]: Parsed URL information including domain, ASIN, etc.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    result = {
        "original_url": url,
        "domain": parsed_url.netloc,
        "path": parsed_url.path,
        "query_params": query_params,
        "asin": extract_asin_from_url(url),
        "is_valid": False,
    }
    
    # Determine marketplace
    domain_lower = parsed_url.netloc.lower()
    if 'amazon.com' in domain_lower:
        result["marketplace"] = "US"
    elif 'amazon.co.uk' in domain_lower:
        result["marketplace"] = "UK"
    elif 'amazon.de' in domain_lower:
        result["marketplace"] = "DE"
    elif 'amazon.fr' in domain_lower:
        result["marketplace"] = "FR"
    elif 'amazon.it' in domain_lower:
        result["marketplace"] = "IT"
    elif 'amazon.es' in domain_lower:
        result["marketplace"] = "ES"
    elif 'amazon.ca' in domain_lower:
        result["marketplace"] = "CA"
    elif 'amazon.co.jp' in domain_lower:
        result["marketplace"] = "JP"
    else:
        result["marketplace"] = "UNKNOWN"
    
    # Check if it's a valid product URL
    if result["asin"] and any(pattern in parsed_url.path.lower() 
                             for pattern in ['/dp/', '/product/', '/gp/product/']):
        result["is_valid"] = True
    
    return result


def clean_amazon_url(url: str) -> str:
    """
    Clean Amazon URL by removing unnecessary parameters.
    
    Args:
        url (str): Original Amazon URL.
    
    Returns:
        str: Cleaned URL with only essential parameters.
    """
    parsed_info = parse_amazon_url(url)
    
    if not parsed_info["is_valid"] or not parsed_info["asin"]:
        return url  # Return original if we can't parse it
    
    # Construct clean URL
    domain = parsed_info["domain"]
    asin = parsed_info["asin"]
    
    # Use the most common format
    clean_url = f"https://{domain}/dp/{asin}"
    
    return clean_url


def get_user_agent() -> str:
    """
    Get a realistic user agent string for web scraping.
    
    Returns:
        str: User agent string.
    """
    return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


def get_request_headers() -> Dict[str, str]:
    """
    Get HTTP headers for web scraping requests.
    
    Returns:
        Dict[str, str]: Headers dictionary.
    """
    return {
        'User-Agent': get_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def is_amazon_url(url: str) -> bool:
    """
    Quick check if URL is from Amazon.
    
    Args:
        url (str): URL to check.
    
    Returns:
        bool: True if URL is from Amazon domain.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        return 'amazon.' in domain
    except:
        return False 