"""
Product data schemas and validation for e-commerce scraping.

This module provides data models, JSON schemas, and validation utilities
for extracting and normalizing product data from e-commerce websites.
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse


@dataclass
class ProductData:
    """Product data model with all required e-commerce fields."""

    # Basic product information
    name: str = ""
    retailer: str = ""
    url: str = ""
    description: Optional[str] = None
    product_key: Optional[str] = None

    # Pricing information
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    has_discount: bool = False
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None

    # Product details
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    volume: Optional[str] = None
    dimensions: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None

    # Media and metadata
    images: List[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Post-initialization processing and validation."""
        # Generate product key if not provided
        if not self.product_key:
            self.product_key = self._generate_product_key()

        # Extract retailer from URL if not provided
        if not self.retailer and self.url:
            self.retailer = self._extract_retailer_from_url()

        # Calculate discount information
        self._calculate_discounts()

        # Clean and validate data
        self._clean_data()

    def _generate_product_key(self) -> str:
        """Generate a unique product key based on URL and name."""
        content = f"{self.url}:{self.name}:{self.brand or ''}:{self.sku or ''}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _extract_retailer_from_url(self) -> str:
        """Extract retailer name from URL domain."""
        try:
            parsed = urlparse(self.url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            domain = domain.replace('www.', '')

            # Known retailer mappings
            retailer_mappings = {
                'thaiwatsadu.com': 'Thai Watsadu',
                'homepro.co.th': 'HomePro',
                'lazada.co.th': 'Lazada',
                'shopee.co.th': 'Shopee',
                'central.co.th': 'Central',
                'powerbuy.co.th': 'Power Buy',
                'jaymart.co.th': 'Jaymart',
                'banana-it': 'Banana IT',
                'advice.co.th': 'Advice',
            }

            for domain_pattern, retailer in retailer_mappings.items():
                if domain_pattern in domain:
                    return retailer

            # Extract domain name as fallback
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                return domain_parts[-2].title()

            return domain.title()

        except Exception:
            return "Unknown Retailer"

    def _calculate_discounts(self):
        """Calculate discount information based on prices with proper defaults."""
        # Initialize defaults
        self.has_discount = False
        self.discount_amount = 0.0
        self.discount_percent = 0.0

        # Calculate discounts only if we have valid pricing data
        if (self.current_price is not None and
            self.original_price is not None and
            self.original_price > 0):

            self.discount_amount = round(self.original_price - self.current_price, 2)
            self.discount_percent = round((self.discount_amount / self.original_price) * 100, 2)
            self.has_discount = self.discount_amount > 0

        # Ensure discount fields are never None
        if self.discount_amount is None:
            self.discount_amount = 0.0
        if self.discount_percent is None:
            self.discount_percent = 0.0

    def _clean_data(self):
        """Clean and normalize data fields with proper discount handling."""
        # Clean price fields
        if self.current_price is not None:
            self.current_price = round(float(self.current_price), 2)
        if self.original_price is not None:
            self.original_price = round(float(self.original_price), 2)

        # Ensure discount fields are never None and properly formatted
        if self.discount_percent is None:
            self.discount_percent = 0.0
        else:
            self.discount_percent = round(float(self.discount_percent), 4)

        if self.discount_amount is None:
            self.discount_amount = 0.0
        else:
            self.discount_amount = round(float(self.discount_amount), 2)

        # Ensure has_discount is always boolean
        if self.has_discount is None:
            self.has_discount = False
        else:
            self.has_discount = bool(self.has_discount)

        # Clean text fields
        if self.name:
            self.name = ' '.join(self.name.split())
        if self.description:
            self.description = ' '.join(self.description.split())
        if self.brand:
            self.brand = self.brand.strip()
        if self.model:
            self.model = self.model.strip()
        if self.sku:
            self.sku = self.sku.strip()

        # Filter images
        self.images = [img for img in self.images if img and img.startswith(('http://', 'https://'))]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with all required fields."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# JSON schema for product data validation
PRODUCT_JSON_SCHEMA = {
    "type": "object",
    "required": ["name", "retailer", "url"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Product name"
        },
        "retailer": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "description": "Retailer name"
        },
        "url": {
            "type": "string",
            "format": "uri",
            "description": "Product URL"
        },
        "description": {
            "type": ["string", "null"],
            "maxLength": 2000,
            "description": "Product description"
        },
        "product_key": {
            "type": ["string", "null"],
            "pattern": "^[a-zA-Z0-9]{16}$",
            "description": "Unique product identifier"
        },
        "current_price": {
            "type": ["number", "null"],
            "minimum": 0,
            "description": "Current selling price"
        },
        "original_price": {
            "type": ["number", "null"],
            "minimum": 0,
            "description": "Original price before discount"
        },
        "has_discount": {
            "type": "boolean",
            "description": "Whether product has discount"
        },
        "discount_percent": {
            "type": ["number", "null"],
            "minimum": 0,
            "maximum": 100,
            "description": "Discount percentage"
        },
        "discount_amount": {
            "type": ["number", "null"],
            "minimum": 0,
            "description": "Discount amount in currency"
        },
        "brand": {
            "type": ["string", "null"],
            "maxLength": 100,
            "description": "Product brand"
        },
        "model": {
            "type": ["string", "null"],
            "maxLength": 100,
            "description": "Product model"
        },
        "sku": {
            "type": ["string", "null"],
            "maxLength": 100,
            "description": "Product SKU"
        },
        "category": {
            "type": ["string", "null"],
            "maxLength": 100,
            "description": "Product category"
        },
        "volume": {
            "type": ["string", "null"],
            "maxLength": 50,
            "description": "Product volume/capacity"
        },
        "dimensions": {
            "type": ["string", "null"],
            "maxLength": 100,
            "description": "Product dimensions"
        },
        "material": {
            "type": ["string", "null"],
            "maxLength": 100,
            "description": "Product material"
        },
        "color": {
            "type": ["string", "null"],
            "maxLength": 50,
            "description": "Product color"
        },
        "images": {
            "type": "array",
            "items": {
                "type": "string",
                "format": "uri"
            },
            "maxItems": 20,
            "description": "Product image URLs"
        },
        "scraped_at": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when data was scraped"
        }
    }
}


class PriceParser:
    """Utility class for parsing price strings from various formats."""

    @staticmethod
    def parse_price(price_text: str) -> Optional[float]:
        """Parse price from various text formats."""
        if not price_text:
            return None

        # Remove common currency symbols and whitespace
        price_clean = re.sub(r'[฿$,€£¥\s]', '', price_text.strip())

        # Handle comma separators in numbers (e.g., "1,299.00")
        price_clean = re.sub(r'[^0-9.]', '', price_clean)

        # Remove multiple decimal points, keep the last one
        parts = price_clean.split('.')
        if len(parts) > 2:
            price_clean = ''.join(parts[:-1]) + '.' + parts[-1]

        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def extract_prices(text: str) -> tuple[Optional[float], Optional[float]]:
        """Extract current and original prices from text."""
        if not text:
            return None, None

        # Common price patterns
        current_price_patterns = [
            r'(?:ราคา|price)[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'([฿$]?[\d,]+\.?\d*)\s*(?:บาท|THB|฿)',
            r'ตอนนี้[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'ลดเหลือ[:\s]*([฿$]?[\d,]+\.?\d*)',
        ]

        original_price_patterns = [
            r'(?:ราคาปกติ|ปกติ|original|regular)[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'([฿$]?[\d,]+\.?\d*)\s*(?:บาท|THB|฿)\s*(?:ปกติ|regular|original)',
            r'ก่อนลด[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'ราคาพิเศษ[:\s]*([฿$]?[\d,]+\.?\d*)',
        ]

        current_price = None
        original_price = None

        # Extract current price
        for pattern in current_price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                current_price = PriceParser.parse_price(match.group(1))
                break

        # Extract original price
        for pattern in original_price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                original_price = PriceParser.parse_price(match.group(1))
                break

        # If no structured patterns found, try to extract any numbers
        if not current_price and not original_price:
            all_prices = re.findall(r'([฿$]?[\d,]+\.?\d*)', text)
            prices = [PriceParser.parse_price(p) for p in all_prices]
            prices = [p for p in prices if p is not None]

            if len(prices) >= 2:
                # Assume higher price is original price
                original_price = max(prices)
                current_price = min(prices)
            elif len(prices) == 1:
                current_price = prices[0]

        return current_price, original_price


def validate_product_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate product data against the schema.

    Args:
        data: Dictionary containing product data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check required fields
    required_fields = ['name', 'retailer', 'url']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")

    # Validate URL format
    if 'url' in data and data['url']:
        try:
            parsed = urlparse(data['url'])
            if not parsed.scheme or not parsed.netloc:
                errors.append("Invalid URL format")
        except Exception:
            errors.append("Invalid URL format")

    # Validate price fields
    price_fields = ['current_price', 'original_price', 'discount_amount', 'discount_percent']
    for field in price_fields:
        if field in data and data[field] is not None:
            try:
                float(data[field])
            except (ValueError, TypeError):
                errors.append(f"Invalid {field}: must be a number")

    # Validate images array
    if 'images' in data:
        if not isinstance(data['images'], list):
            errors.append("Images must be an array")
        else:
            for i, img_url in enumerate(data['images']):
                if not isinstance(img_url, str) or not img_url.strip():
                    errors.append(f"Invalid image URL at index {i}")

    return len(errors) == 0, errors


def normalize_product_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize and clean raw product data with proper discount handling.

    Args:
        raw_data: Raw extracted data

    Returns:
        Normalized product data dictionary
    """
    normalized = {}

    # Basic fields with type conversion
    for field in ['name', 'retailer', 'url', 'description', 'brand', 'model',
                  'sku', 'category', 'volume', 'dimensions', 'material', 'color']:
        value = raw_data.get(field)
        if value is not None:
            normalized[field] = str(value).strip() if value else None

    # Price fields with proper type conversion
    price_fields = ['current_price', 'original_price']
    for field in price_fields:
        value = raw_data.get(field)
        if value is not None:
            try:
                normalized[field] = float(value)
            except (ValueError, TypeError):
                normalized[field] = None

    # Discount fields with proper defaults to 0.0
    for field in ['discount_amount', 'discount_percent']:
        value = raw_data.get(field)
        if value is not None:
            try:
                normalized[field] = float(value)
            except (ValueError, TypeError):
                normalized[field] = 0.0
        else:
            normalized[field] = 0.0

    # Boolean fields with proper defaults
    has_discount = raw_data.get('has_discount')
    if has_discount is not None:
        normalized['has_discount'] = bool(has_discount)
    else:
        normalized['has_discount'] = False

    # Array fields
    if 'images' in raw_data:
        images = raw_data['images']
        if isinstance(images, list):
            normalized['images'] = [str(img) for img in images if img]
        elif isinstance(images, str):
            normalized['images'] = [images]
        else:
            normalized['images'] = []
    else:
        normalized['images'] = []

    # Timestamp
    normalized['scraped_at'] = datetime.now().isoformat()

    return normalized
