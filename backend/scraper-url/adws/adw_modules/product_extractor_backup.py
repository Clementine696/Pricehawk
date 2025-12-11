"""
Product data extraction module for e-commerce websites.

This module provides extraction strategies and utilities for extracting
product information from various e-commerce website structures.
"""

import re
import json
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse

from .product_schemas import ProductData, PriceParser, normalize_product_data


class ProductExtractor:
    """Extracts product data from e-commerce web pages."""

    def __init__(self, base_url: str = None):
        """Initialize the extractor with base URL for resolving relative URLs."""
        self.base_url = base_url

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data from HTML content.

        Args:
            html_content: HTML content of the product page
            url: URL of the product page (for context)

        Returns:
            ProductData object or None if extraction failed
        """
        if not html_content:
            return None

        # Set base URL if provided
        if url:
            self.base_url = url

        # Extract all product information
        raw_data = {}

        # Extract basic product information
        # Extract retailer from URL
        raw_data['retailer'] = self._extract_retailer_from_url(url)
        raw_data['name'] = self._extract_product_name(html_content)
        raw_data['description'] = self._extract_description(html_content)
        raw_data['brand'] = self._extract_brand(html_content)
        raw_data['model'] = self._extract_model(html_content)
        raw_data['sku'] = self._extract_sku(html_content)
        raw_data['category'] = self._extract_category(html_content)

        # Extract pricing information
        current_price, original_price = self._extract_prices(html_content)
        raw_data['current_price'] = current_price
        raw_data['original_price'] = original_price

        # Extract product specifications
        raw_data['volume'] = self._extract_volume(html_content)
        raw_data['dimensions'] = self._extract_dimensions(html_content)
        raw_data['material'] = self._extract_material(html_content)
        raw_data['color'] = self._extract_color(html_content)

        # Apply systematic field sanitization
        if raw_data['brand']:
            raw_data['brand'] = self._sanitize_brand_field(raw_data['brand'])

        if raw_data['model']:
            # Prevent HTML element names as model values
            clean_model = self._sanitize_text_field(raw_data['model'], max_length=50)
            # Reject common HTML element names
            html_elements = ['html', 'body', 'div', 'span', 'section', 'article', 'header', 'footer']
            if clean_model and clean_model.lower() not in html_elements:
                raw_data['model'] = clean_model
            else:
                raw_data['model'] = None

        if raw_data['sku']:
            raw_data['sku'] = self._sanitize_sku_field(raw_data['sku'])

        if raw_data['color']:
            raw_data['color'] = self._sanitize_color_field(raw_data['color'])

        if raw_data['dimensions']:
            raw_data['dimensions'] = self._sanitize_dimensions_field(raw_data['dimensions'])

        if raw_data['material']:
            raw_data['material'] = self._sanitize_material_field(raw_data['material'])

        if raw_data['volume']:
            raw_data['volume'] = self._sanitize_text_field(raw_data['volume'], max_length=50)

        if raw_data['category']:
            raw_data['category'] = self._sanitize_text_field(raw_data['category'], max_length=100)

        # Extract images
        raw_data['images'] = self._extract_images(html_content)

        # Add URL
        raw_data['url'] = url or self.base_url

        # Normalize and validate data
        normalized_data = normalize_product_data(raw_data)

        # Create ProductData object
        try:
            return ProductData(**normalized_data)
        except Exception as e:
            print(f"Error creating ProductData: {e}")
            return None

    def extract_from_json_ld(self, html_content: str) -> Dict[str, Any]:
        """Extract product data from JSON-LD structured data.

        Args:
            html_content: HTML content containing JSON-LD

        Returns:
            Dictionary with extracted product data
        """
        json_ld_data = {}

        # Find JSON-LD scripts
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, dict):
                    # Handle single object
                    if data.get('@type') in ['Product', 'ProductModel']:
                        json_ld_data.update(self._parse_json_ld_product(data))
                    # Handle array of objects
                    elif isinstance(data.get('@graph'), list):
                        for item in data['@graph']:
                            if item.get('@type') in ['Product', 'ProductModel']:
                                json_ld_data.update(self._parse_json_ld_product(item))
            except json.JSONDecodeError:
                continue

        return json_ld_data

    def _parse_json_ld_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse product data from JSON-LD structure."""
        parsed = {}

        # Basic fields
        parsed['name'] = data.get('name')
        parsed['description'] = data.get('description')
        parsed['brand'] = data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand')
        parsed['model'] = data.get('model')
        parsed['sku'] = data.get('sku')
        parsed['category'] = data.get('category', [None])[0] if isinstance(data.get('category'), list) else data.get('category')

        # Pricing
        offers = data.get('offers')
        if isinstance(offers, dict):
            parsed['current_price'] = offers.get('price')
            parsed['original_price'] = offers.get('highPrice') or offers.get('price') if offers.get('priceSpecification', {}).get('highPrice') else None
        elif isinstance(offers, list) and offers:
            offer = offers[0]  # Take first offer
            parsed['current_price'] = offer.get('price')
            parsed['original_price'] = offer.get('highPrice')

        # Images
        images = data.get('image')
        if isinstance(images, list):
            parsed['images'] = images
        elif isinstance(images, str):
            parsed['images'] = [images]

        return parsed

    def _extract_product_name(self, html_content: str) -> Optional[str]:
        """Extract product name from HTML."""
        # Common selectors for product name
        patterns = [
            r'<h1[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</h1>',
            r'<h1[^>]*>(.*?)</h1>',
            r'<title[^>]*>(.*?)</title>',
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            r'<div[^>]*class="[^"]*product-title[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*product-name[^"]*"[^>]*>(.*?)</span>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                name = self._clean_text(val)

                # Filter out retailer names and site branding
                if name:
                    # Common retailer names and site branding to filter out
                    retailer_names = [
                        'megahome', 'mega home', 'homepro', 'home pro', 'boonthavorn', 'dohome', 'do home',
                        'global house', 'thai watsadu', 'watsadu', 'power buy', 'powerbuy',
                        'lazada', 'shopee', 'central', 'jaymart', 'Vivin', 'banner'
                    ]

                    # Check if the name is just a retailer name (case insensitive)
                    name_lower = name.lower().strip()
                    if name_lower in retailer_names:
                        continue  # Skip this pattern and try the next one

                    # Check if the name starts with a retailer name and clean it
                    for retailer in retailer_names:
                        if name_lower.startswith(retailer + ' '):
                            # Remove retailer prefix
                            name = name[len(retailer):].strip()
                            if not name or len(name) < 3:
                                continue  # Skip if name becomes too short after cleaning
                            break

                if name and len(name) > 3:  # Minimum length check
                    return name

        return None

    def _extract_description(self, html_content: str) -> Optional[str]:
        """Extract product description from HTML."""
        patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*product-description[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                desc = self._clean_text(val)
                if desc and len(desc) > 10:
                    return desc

        return None

    def _extract_brand(self, html_content: str) -> Optional[str]:
        """Extract product brand from HTML with enhanced patterns and JSON-LD support."""
        # First try JSON-LD extraction
        json_ld_data = self.extract_from_json_ld(html_content)
        if json_ld_data.get('brand'):
            brand_value = json_ld_data['brand']
            if isinstance(brand_value, dict):
                brand_value = brand_value.get('name')
            if brand_value:
                clean_brand = self._sanitize_brand_field(str(brand_value))
                if clean_brand:
                    return clean_brand

        # HTML patterns for brand extraction
        patterns = [
            r'<meta[^>]*property=["\']og:brand["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']brand["\'][^>]*content=["\']([^"\']+)["\']',
            r'<span[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</div>',
            r'<a[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</a>',
            r'ยี่ห้อ[:\s]*([^\n<]+)',
            r'แบรนด์[:\s]*([^\n<]+)',
            r'Brand[:\s]*([^\n<]+)',
            r'Manufacturer[:\s]*([^\n<]+)',
            # Thai variations
            r'ผู้ผลิต[:\s]*([^\n<]+)',
            r'เครื่องหมาย[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                brand = self._clean_text(val)
                if brand and len(brand) > 1:
                    # Additional sanitization to prevent contamination
                    clean_brand = self._sanitize_brand_field(brand)
                    if clean_brand:
                        return clean_brand

        # Try to extract from title (first word is often brand)
        title_patterns = [
            r'<title[^>]*>(.*?)</title>',
            r'<h1[^>]*class="[^"]*product-title[^"]*"[^>]*>(.*?)</h1>',
            r'<h1[^>]*>(.*?)</h1>',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                title_text = self._clean_text(match.group(1))
                if title_text:
                    # First word or phrase might be brand
                    words = title_text.split()
                    if len(words) >= 2:
                        potential_brand = ' '.join(words[:2])  # Try first two words
                        clean_brand = self._sanitize_brand_field(potential_brand)
                        if clean_brand and len(clean_brand) >= 3:
                            # Validate it looks like a brand (starts with capital)
                            if clean_brand[0].isupper():
                                return clean_brand

        return None

    def _extract_model(self, html_content: str) -> Optional[str]:
        """Extract product model from HTML with enhanced patterns and contamination prevention."""
        # First try JSON-LD extraction
        json_ld_data = self.extract_from_json_ld(html_content)
        if json_ld_data.get('model'):
            model_value = json_ld_data['model']
            if model_value:
                clean_model = self._sanitize_text_field(str(model_value), max_length=200)
                if clean_model:
                    return clean_model

        # HTML patterns for model extraction
        patterns = [
            r'<span[^>]*class="[^"]*model[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*model[^"]*"[^>]*>(.*?)</div>',
            r'<meta[^>]*property=["\']product:model["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']model["\'][^>]*content=["\']([^"\']+)["\']',
            r'รุ่น[:\s]*([^\n<]+)',
            r'โมเดล[:\s]*([^\n<]+)',
            r'Model[:\s]*([^\n<]+)',
            r'Model No[:\s]*([^\n<]+)',
            r'Model Number[:\s]*([^\n<]+)',
            r'Type[:\s]*([^\n<]+)',
            r'แบบ[:\s]*([^\n<]+)',
            r'รหัสแบบ[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                model = self._clean_text(val)
                if model and len(model) > 1:
                    # Additional sanitization to prevent contamination
                    clean_model = self._sanitize_text_field(model, max_length=200)
                    if clean_model:
                        return clean_model

        # Try to extract model from title and description using regex patterns
        text_sources = []

        # Add title to sources
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            text_sources.append(self._clean_text(title_match.group(1)))

        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE)
        if h1_match:
            text_sources.append(self._clean_text(h1_match.group(1)))

        # Add description to sources
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if desc_match:
            text_sources.append(self._clean_text(desc_match.group(1)))

        # Model extraction patterns from text
        model_patterns = [
            r'รุ่น\s+([A-Za-z0-9\-\_]+)',
            r'โมเดล\s+([A-Za-z0-9\-\_]+)',
            r'Model[:\s]+([A-Za-z0-9\-\_]+)',
            r'Type[:\s]+([A-Za-z0-9\-\_]+)',
            r'([A-Z]{2,4}-?\d{3,6})',  # Common model pattern like "ABC-1234"
            r'([A-Z][a-z]*-\d+[A-Za-z]*)',  # Pattern like "Product-123X"
        ]

        for text_source in text_sources:
            if text_source:
                for pattern in model_patterns:
                    match = re.search(pattern, text_source, re.IGNORECASE)
                    if match:
                        potential_model = match.group(1).strip()
                        clean_model = self._sanitize_text_field(potential_model, max_length=200)
                        if clean_model and len(clean_model) >= 2:
                            return clean_model

        return None

    def _extract_sku(self, html_content: str) -> Optional[str]:
        """Extract product SKU from HTML with enhanced validation to prevent URL contamination."""
        patterns = [
            r'<span[^>]*class="[^"]*sku[^"]*"[^>]*>(.*?)</span>',
            r'<meta[^>]*property=["\']product:retailer_item_id["\'][^>]*content=["\']([^"\']+)["\']',
            r'รหัสสินค้า[:\s]*([^\n<]+)',
            r'SKU[:\s]*([^\n<]+)',
            r'Article No[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                sku = self._clean_text(val)
                if sku and len(sku) > 1:
                    # Apply enhanced sanitization
                    clean_sku = self._sanitize_sku_field(sku)
                    if clean_sku:
                        return clean_sku

        # Try to extract from URL (enhanced to extract meaningful product codes)
        if self.base_url:
            url_patterns = [
                r'/product/([^/]+?)(?:/|$)',
                r'/item/([^/]+?)(?:/|$)',
                r'/p/([^/]+?)(?:/|$)',
                r'sku[=/]([^/&]+)',
                r'/(\d{6,})',  # Extract numeric product codes
                r'-([A-Z0-9]{4,})',  # Extract alphanumeric codes at end
            ]
            for pattern in url_patterns:
                match = re.search(pattern, self.base_url, re.IGNORECASE)
                if match:
                    potential_sku = match.group(1).strip()
                    # Validate the extracted URL component is a meaningful SKU
                    if self._is_valid_sku(potential_sku):
                        return potential_sku

        return None

    def _sanitize_sku_field(self, sku: str) -> Optional[str]:
        """Specialized sanitization for SKU field to prevent URL contamination."""
        if not sku:
            return None

        # Apply general sanitization first
        sku = self._sanitize_text_field(sku, max_length=50)
        if not sku:
            return None

        # Additional SKU-specific validation
        if self._is_valid_sku(sku):
            return sku

        return None

    def _is_valid_sku(self, sku: str) -> bool:
        """Validate that SKU is actually a SKU and not a URL or other invalid data."""
        if not sku:
            return False

        # Must be alphanumeric with reasonable length
        if len(sku) < 2 or len(sku) > 50:
            return False

        # Must not contain URLs or domains (more specific patterns)
        sku_lower = sku.lower()
        if (sku_lower.startswith(('http', 'https', 'www')) or
            any(domain in sku_lower for domain in ['.com', '.co.th', '.net', '.org']) or
            '/product/' in sku_lower or
            '/item/' in sku_lower or
            '/category/' in sku_lower or
            '/search/' in sku_lower or
            '/page/' in sku_lower):
            return False

        # Must not contain path separators (except valid SKU patterns with hyphens)
        if '/' in sku or '\\' in sku:
            return False

        # Must not be just numeric dates
        if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', sku):
            return False

        # Allow alphanumeric, hyphens, and underscores
        if re.match(r'^[A-Za-z0-9\-_]+$', sku):
            return True

        return False

    def _extract_category(self, html_content: str) -> Optional[str]:
        """Extract product category from HTML."""
        patterns = [
            r'<nav[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>.*?</nav>',
            r'<div[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>.*?</div>',
            r'หมวดหมู่[:\s]*([^\n<]+)',
            r'Category[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                category = self._clean_text(val)
                if category and len(category) > 1:
                    # If it's breadcrumb, take the last part
                    if '>' in category:
                        parts = [p.strip() for p in category.split('>')]
                        category = parts[-1] if parts else category
                    return category

        return None

    def _extract_prices(self, html_content: str) -> tuple[Optional[float], Optional[float]]:
        """Extract current and original prices from HTML."""
        # Extract price information
        price_patterns = [
            r'<span[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</div>',
            r'<meta[^>]*property=["\']product:price:amount["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:price:amount["\'][^>]*content=["\']([^"\']+)["\']',
        ]

        all_price_text = []
        for pattern in price_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            all_price_text.extend(matches)

        # Also look for prices in text content
        price_text_patterns = [
            r'ราคา[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'Price[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'([฿$]?[\d,]+\.?\d*)\s*บาท',
        ]

        for pattern in price_text_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            all_price_text.extend(matches)

        # Original price patterns
        original_price_patterns = [
            r'<span[^>]*class="[^"]*original[^"]*price[^"]*"[^>]*>(.*?)</span>',
            r'<span[^>]*class="[^"]*was[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*original-price[^"]*"[^>]*>(.*?)</div>',
            r'ราคาปกติ[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'ปกติ[:\s]*([฿$]?[\d,]+\.?\d*)',
        ]

        original_prices = []
        for pattern in original_price_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            original_prices.extend(matches)

        # Parse all found prices
        all_prices = [PriceParser.parse_price(price) for price in all_price_text]
        all_prices = [p for p in all_prices if p is not None]

        orig_prices = [PriceParser.parse_price(price) for price in original_prices]
        orig_prices = [p for p in orig_prices if p is not None]

        current_price = None
        original_price = None

        if orig_prices:
            original_price = max(orig_prices)  # Highest price is likely original price
            # Current price is the lowest price that's not the original
            other_prices = [p for p in all_prices if p != original_price]
            current_price = min(other_prices) if other_prices else None
        elif all_prices:
            # If no clear original price, use min/max logic
            if len(all_prices) >= 2:
                original_price = max(all_prices)
                current_price = min(all_prices)
            else:
                current_price = all_prices[0]

        return current_price, original_price

    def _extract_volume(self, html_content: str) -> Optional[str]:
        """Extract product volume/capacity from HTML."""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:ลิตร|L|l)(?:\s*ตัน)?',
            r'(\d+(?:\.\d+)?)\s*(?:มล|ml|ML)',
            r'(\d+(?:\.\d+)?)\s*(?:แกลลอน|gallon)',
            r'ความจุ[:\s]*([^\n<]+)',
            r'Volume[:\s]*([^\n<]+)',
            r'Capacity[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                volume = self._clean_text(match.group(1) if match.groups() else match.group(0))
                if volume:
                    return volume

        return None

    def _extract_dimensions(self, html_content: str) -> Optional[str]:
        """Extract product dimensions from HTML with enhanced sanitization."""
        patterns = [
            r'(\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?)\s*(?:ซม|cm|mm|m)',
            r'ขนาด[:\s]*([^\n<]+)',
            r'Dimension[:\s]*([^\n<]+)',
            r'Size[:\s]*([^\n<]+)',
            r'(\d+(?:\.\d+)?)\s*ซม',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                dimensions = self._clean_text(match.group(1) if match.groups() else match.group(0))
                if dimensions:
                    # Apply specialized dimensions sanitization
                    clean_dimensions = self._sanitize_dimensions_field(dimensions)
                    if clean_dimensions:
                        return clean_dimensions

        return None

    def _extract_material(self, html_content: str) -> Optional[str]:
        """Extract product material from HTML with enhanced sanitization."""
        patterns = [
            r'วัสดุ[:\s]*([^\n<]+)',
            r'Material[:\s]*([^\n<]+)',
            r'ผลิตจาก[:\s]*([^\n<]+)',
            r'เนื้อวัสดุ[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                material = self._clean_text(match.group(1))
                if material and len(material) > 1:
                    # Apply specialized material sanitization
                    clean_material = self._sanitize_material_field(material)
                    if clean_material:
                        return clean_material

        return None

    def _extract_color(self, html_content: str) -> Optional[str]:
        """Extract product color from HTML with enhanced sanitization."""
        patterns = [
            r'สี[:\s]*([^\n<]+)',
            r'Color[:\s]*([^\n<]+)',
            r'สีแบบ[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                color = self._clean_text(match.group(1))
                if color and len(color) > 1:
                    # Apply specialized color sanitization
                    clean_color = self._sanitize_color_field(color)
                    if clean_color:
                        return clean_color

        return None

    def _extract_images(self, html_content: str) -> List[str]:
        """Extract product image URLs from HTML."""
        images = []

        # Product image patterns
        patterns = [
            r'<img[^>]*class="[^"]*product[^"]*image[^"]*"[^>]*src=["\']([^"\']+)["\']',
            r'<img[^>]*class="[^"]*product-image[^"]*"[^>]*src=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']product:image["\'][^>]*content=["\']([^"\']+)["\']',
            r'<img[^>]*src=["\']([^"\']*product[^"\']*)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                img_url = self._resolve_url(match.strip())
                if img_url and img_url not in images:
                    images.append(img_url)

        # Also check JSON-LD for images
        json_ld_data = self.extract_from_json_ld(html_content)
        if 'images' in json_ld_data:
            for img_url in json_ld_data['images']:
                resolved_url = self._resolve_url(img_url)
                if resolved_url and resolved_url not in images:
                    images.append(resolved_url)

        return images[:10]  # Limit to 10 images

    def _resolve_url(self, url: str) -> Optional[str]:
        """Resolve relative URL to absolute URL."""
        if not url:
            return None

        # Skip data URLs and invalid URLs
        if url.startswith(('data:', 'mailto:', 'tel:', 'javascript:')):
            return None

        # If already absolute, return as is
        if url.startswith(('http://', 'https://')):
            return url

        # Resolve relative URL
        if self.base_url:
            try:
                return urljoin(self.base_url, url)
            except Exception:
                pass

        return url

    def _extract_retailer_from_url(self, url: str) -> str:
        """Extract retailer name from URL domain."""
        if not url:
            return "Unknown Retailer"

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            domain = domain.replace('www.', '')

            # Known retailer mappings
            retailer_mappings = {
                'advice.co.th': 'Advice',
                'banana-it': 'Banana IT',
                'dohome.co.th': 'DoHome',
                'globalhouse.co.th': 'Global House',
                'homepro.co.th': 'HomePro',
                'jaymart.co.th': 'Jaymart',
                'lazada.co.th': 'Lazada',
                'megahome.co.th': 'Mega Home',
                'powerbuy.co.th': 'Power Buy',
                'shopee.co.th': 'Shopee',
                'thaiwatsadu.com': 'Thai Watsadu',
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

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing HTML tags and extra whitespace."""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')

        # Clean whitespace
        text = ' '.join(text.split())

        return text.strip()

    def _sanitize_text_field(self, text: str, max_length: int = 100) -> Optional[str]:
        """Enhanced field sanitization to prevent HTML/CSS/JSON contamination and ensure clean data."""
        if not text:
            return None

        # Remove HTML/CSS class names and attributes patterns
        css_patterns = [
            r'class="[^"]*"',
            r'quickInfo-infoLabel-[^"\s]*',
            r'quickInfo-infoValue-[^"\s]*',
            r'style="[^"]*"',
            r'id="[^"]*"',
            r'<label[^>]*>',
            r'</label>',
            r'<span[^>]*>',
            r'</span>',
            r'<div[^>]*>',
            r'</div>',
        ]

        for pattern in css_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove URLs and domain names from text fields
        url_patterns = [
            r'https?://[^\s<>"\']+',
            r'www\.[^\s<>"\']+',
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"\']*)?',
        ]

        for pattern in url_patterns:
            text = re.sub(pattern, '', text)

        # Remove JSON-like structures and objects
        text = re.sub(r'\{[^}]*\}', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)

        # Remove common JSON keys and values
        json_patterns = [
            r'"name"\s*:\s*"[^"]*"',
            r'"type"\s*:\s*"[^"]*"',
            r'"@[^"]*"\s*:\s*"[^"]*"',
            r'"[^"]*"\s*:\s*"[^"]*"',
            r'true|false|null',
            r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}',  # ISO dates
        ]

        for pattern in json_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove excessive punctuation and special characters
        text = re.sub(r'[{}[\]"\',:;\\<>]', '', text)

        # Handle trailing comma truncation by removing trailing commas
        text = text.rstrip(',;')

        # Clean whitespace again
        text = ' '.join(text.split())

        # Validate the cleaned text
        if (text and
            len(text) > 1 and
            len(text) <= max_length and
            not text.lower().startswith(('http', 'www', 'data:', 'class=', 'style=')) and
            not any(char in text for char in ['{', '}', '[', ']', '"', "'", '\\', '<', '>', '='])):
            return text.strip()

        return None

    def _sanitize_dimensions_field(self, dimensions: str) -> Optional[str]:
        """Specialized sanitization for dimensions field."""
        if not dimensions:
            return None

        # Remove CSS variables first
        css_variable_patterns = [
            r'var\([^)]+\)',
        ]

        for pattern in css_variable_patterns:
            dimensions = re.sub(pattern, '', dimensions, flags=re.IGNORECASE)

        # Extract dimension patterns more precisely before general sanitization
        dim_patterns = [
            r'(\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)',
        ]

        # First try to extract dimension pattern
        for pattern in dim_patterns:
            match = re.search(pattern, dimensions)
            if match:
                clean_dim = match.group(1).strip()
                if clean_dim and len(clean_dim) <= 200:
                    return clean_dim

        # If no pattern found, apply general sanitization
        dimensions = self._sanitize_text_field(dimensions, max_length=200)
        if dimensions and len(dimensions) <= 200:
            return dimensions

        return None

    def _sanitize_color_field(self, color: str) -> Optional[str]:
        """Specialized sanitization for color field to prevent CSS color codes."""
        if not color:
            return None

        # Remove CSS color codes and patterns first
        css_color_patterns = [
            r'#[0-9a-fA-F]{3,6}',
            r'rgb\([^)]+\)',
            r'rgba\([^)]+\)',
            r'hsl\([^)]+\)',
            r'hsla\([^)]+\)',
            r'color:\s*[^;\\]+',
            r'background:\s*[^;\\]+',
            r'var\([^)]+\)',
        ]

        for pattern in css_color_patterns:
            color = re.sub(pattern, '', color, flags=re.IGNORECASE)

        # Final cleanup and validation
        color = ' '.join(color.split()).strip()

        # Apply general sanitization
        color = self._sanitize_text_field(color, max_length=50)
        if not color:
            return None

        # Validate color is not a code
        if (color and
            len(color) >= 2 and
            len(color) <= 50 and
            not color.startswith(('#', 'rgb', 'hsl')) and
            not re.match(r'^[0-9a-fA-F]{3,6}$', color)):
            return color

        return None

    def _sanitize_material_field(self, material: str) -> Optional[str]:
        """Specialized sanitization for material field."""
        if not material:
            return None

        # Remove common prefixes first
        material = re.sub(r'วัสดุ\s*[:\s]*|Material\s*[:\s]*|ผลิตจาก\s*[:\s]*|เนื้อวัสดุ\s*[:\s]*', '', material, flags=re.IGNORECASE)
        material = ' '.join(material.split()).strip()

        # Apply general sanitization
        material = self._sanitize_text_field(material, max_length=100)
        if not material:
            return None

        if material and len(material) >= 2 and len(material) <= 100:
            return material

        return None

    def _sanitize_brand_field(self, brand: str) -> Optional[str]:
        """Sanitize brand field to prevent JSON contamination and ensure clean data."""
        return self._sanitize_text_field(brand, max_length=100)


# Retailer-specific extractors
class ThaiWatsaduExtractor(ProductExtractor):
    """Specialized extractor for Thai Watsadu website with enhanced sanitization."""

    # Thai Watsadu specific strings to filter out
    THAIWATSADU_FILTER_STRINGS = [
        'ไทวัสดุ',
        'thaiwatsadu',
        'ครบเรื่องบ้าน ถูกและดี',
        'ครบเรื่องบ้าน',
        'ถูกและดี',
    ]

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Thai Watsadu with enhanced sanitization."""
        product = ProductData(url=url)

        # 1. Extract SKU from URL first (most reliable for Thai Watsadu)
        # URL pattern: /product/...-60272160 or /th/sku/60272160
        if url:
            # Try pattern: -SKU at end of URL
            sku_match = re.search(r'-(\d{8})(?:\?|$)', url)
            if sku_match:
                product.sku = sku_match.group(1)
            else:
                # Try pattern: /sku/SKU
                sku_match = re.search(r'/sku/(\d+)', url)
                if sku_match:
                    product.sku = sku_match.group(1)

        # 2. Try JSON-LD extraction
        json_ld_data = self._extract_json_ld(html_content)

        if json_ld_data:
            product.name = self._clean_thaiwatsadu_text(json_ld_data.get('name'))
            product.description = self._clean_thaiwatsadu_text(json_ld_data.get('description'), strip_html=True)

            brand_value = json_ld_data.get('brand')
            if brand_value:
                if isinstance(brand_value, dict):
                    brand_value = brand_value.get('name')
                if brand_value:
                    product.brand = self._clean_thaiwatsadu_text(str(brand_value))

            # Don't use SKU from JSON-LD as it's often contaminated
            # We already extracted from URL above

            offers = json_ld_data.get('offers', {})
            if isinstance(offers, dict):
                price = offers.get('price')
                if price:
                    try:
                        product.current_price = float(price)
                    except (ValueError, TypeError):
                        pass

            image = json_ld_data.get('image')
            if image:
                if isinstance(image, list):
                    product.images = image
                elif isinstance(image, str):
                    product.images = [image]

        # 3. Extract category from breadcrumb
        product.category = self._extract_thaiwatsadu_category(html_content)

        # 3.5. Extract product specifications from "ข้อมูลเฉพาะสินค้า" section
        specs = self._extract_thaiwatsadu_specs(html_content)
        if specs:
            if specs.get('dimensions'):
                product.dimensions = specs['dimensions']
            if specs.get('material'):
                product.material = specs['material']
            if specs.get('brand') and not product.brand:
                product.brand = specs['brand']
            if specs.get('color') and not product.color:
                product.color = specs['color']
            if specs.get('model') and not product.model:
                product.model = specs['model']
            if specs.get('weight'):
                # Store weight in dimensions if no dimensions found
                if not product.dimensions:
                    product.dimensions = f"น้ำหนัก: {specs['weight']} กก."

        # 4. Extract product name if not found
        if not product.name:
            name_patterns = [
                r'<h1[^>]*class="[^"]*product[^"]*name[^"]*"[^>]*>(.*?)</h1>',
                r'<h1[^>]*>(.*?)</h1>',
            ]
            for pattern in name_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    name = self._clean_text(match.group(1))
                    name = self._clean_thaiwatsadu_text(name)
                    if name and len(name) > 3:
                        product.name = name
                        break

        # 5. Extract model from product name (pattern: รุ่น XXX)
        if product.name:
            # Model can include dots like NO.888
            model_match = re.search(r'รุ่น\s+([A-Za-z0-9\-_.]+)', product.name)
            if model_match:
                product.model = model_match.group(1).strip()

        # 5b. Extract brand from product name if not found in specs
        # Common brands in Thai hardware stores often appear as UPPERCASE before "รุ่น"
        if not product.brand and product.name:
            # Common brand patterns: MAKITA รุ่น, BOSCH รุ่น, etc.
            brand_match = re.search(r'([A-Z][A-Z0-9]+)\s+รุ่น', product.name)
            if brand_match:
                product.brand = brand_match.group(1).strip()
            else:
                # Try to find known brands in the name
                known_brands = ['MAKITA', 'BOSCH', 'DEWALT', 'MILWAUKEE', 'HITACHI', 'TOSHIBA',
                               'PHILIPS', 'PANASONIC', 'SAMSUNG', 'LG', 'SONY', 'TCL', 'HAIER',
                               'ELECTROLUX', 'MITSUBISHI', 'DAIKIN', 'CARRIER', 'SHARP',
                               'TOA', 'BEGER', 'NIPPON', 'JOTUN', 'DULUX', 'NIPPON',
                               'AMERICAN STANDARD', 'COTTO', 'KOHLER', 'GROHE', 'TOTO',
                               'YALE', 'HAFELE', 'YALE', 'SCHLAGE',
                               'THE TREE', 'ZD', 'GTS', 'SCG', 'THAI WATSADU']
                for brand in known_brands:
                    if brand.upper() in product.name.upper():
                        product.brand = brand
                        break

        # 6. Extract color from product name or HTML
        color = self._extract_color(html_content)
        if color:
            product.color = self._clean_thaiwatsadu_text(color)
        else:
            # Try to extract from product name (pattern: สีXXX)
            if product.name:
                color_match = re.search(r'สี([ก-๙a-zA-Z]+)', product.name)
                if color_match:
                    product.color = color_match.group(1).strip()

        # 7. Extract dimensions (fallback if not found in specs)
        # Only use fallback if it looks like actual dimensions (contains x or multiple numbers)
        if not product.dimensions:
            dimensions = self._extract_dimensions(html_content)
            if dimensions:
                dimensions = self._clean_thaiwatsadu_text(dimensions)
                # Only accept if it looks like dimensions (has x or multiple parts)
                if dimensions and ('x' in dimensions.lower() or len(re.findall(r'\d+', dimensions)) > 1):
                    product.dimensions = dimensions

        # 8. Extract material (fallback if not found in specs)
        if not product.material:
            material = self._extract_material(html_content)
            if material:
                material = self._clean_thaiwatsadu_text(material)
                # Filter out invalid values - company names, slogans, categories, etc.
                invalid_material_patterns = [
                    'ครบเรื่องบ้าน', 'ถูกและดี', 'ไทวัสดุ', 'thaiwatsadu',
                    'บริษัท', 'จำกัด', 'มหาชน', 'corporation', 'company',
                    'เซ็นทรัล', 'central', 'retail', 'รีเทล',
                    'http', 'www', '.com', '.co.th',
                    # Category-related words that get falsely extracted as material
                    'ตกแต่ง', 'วัสดุตกแต่ง', 'อุปกรณ์', 'ประตู', 'หน้าต่าง',
                    'บันได', 'รั้ว', 'สินค้า', 'หมวดหมู่'
                ]
                if material and not any(s.lower() in material.lower() for s in invalid_material_patterns):
                    product.material = material

        # 9. Extract volume
        if not product.volume:
            product.volume = self._extract_volume(html_content)

        # 10. Extract images if not found
        if not product.images:
            product.images = self._extract_images(html_content)

        # 11. Fallback: use base extraction for missing fields
        if not product.name or not product.current_price:
            base_product = super().extract_from_html(html_content, url)
            if base_product:
                if not product.name:
                    product.name = self._clean_thaiwatsadu_text(base_product.name)
                if not product.current_price:
                    product.current_price = base_product.current_price
                if not product.original_price:
                    product.original_price = base_product.original_price
                if not product.brand:
                    product.brand = self._clean_thaiwatsadu_text(base_product.brand)
                if not product.images:
                    product.images = base_product.images

        product.retailer = "Thai Watsadu"
        return product

    def _clean_thaiwatsadu_text(self, text: str, strip_html: bool = False) -> Optional[str]:
        """Remove Thai Watsadu specific contamination from text."""
        if not text:
            return None

        # Strip HTML tags if requested
        if strip_html:
            text = re.sub(r'<[^>]+>', '', text)

        # Remove Thai Watsadu branding and slogan
        for filter_str in self.THAIWATSADU_FILTER_STRINGS:
            text = re.sub(re.escape(filter_str), '', text, flags=re.IGNORECASE)

        # Remove patterns like "- ไทวัสดุ" or "| ไทวัสดุ"
        text = re.sub(r'[-|]\s*$', '', text)

        # Clean whitespace
        text = ' '.join(text.split()).strip()

        # Remove trailing punctuation
        text = text.rstrip('-|,;:')

        return text if text else None

    def _extract_thaiwatsadu_category(self, html_content: str) -> Optional[str]:
        """Extract category from Thai Watsadu breadcrumb or JSON-LD."""
        # 1. Try Thai Watsadu specific categoryBar pattern first (most reliable)
        # Look for all links with categoryBar_journeyNavText class
        categorybar_links = re.findall(
            r'<a[^>]*class="[^"]*categoryBar_journeyNavText[^"]*"[^>]*>([^<]+)</a>',
            html_content,
            re.IGNORECASE
        )
        if categorybar_links:
            # Return the first category (most general/biggest)
            return categorybar_links[0].strip()

        # 2. Try JSON-LD BreadcrumbList
        try:
            breadcrumb_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(breadcrumb_pattern, html_content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                try:
                    data = json.loads(match)
                    # Check for BreadcrumbList
                    if isinstance(data, dict) and data.get('@type') == 'BreadcrumbList':
                        items = data.get('itemListElement', [])
                        categories = []
                        for item in items:
                            name = item.get('name') or item.get('item', {}).get('name')
                            if name:
                                categories.append(name)

                        skip_categories = ['หน้าแรก', 'home', 'สินค้า', 'products', 'ทั้งหมด', 'all', 'thaiwatsadu', 'ไทวัสดุ']
                        for cat in reversed(categories[:-1]):
                            cat_clean = cat.strip()
                            if cat_clean and cat_clean.lower() not in [s.lower() for s in skip_categories]:
                                return cat_clean

                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'BreadcrumbList':
                                items = item.get('itemListElement', [])
                                categories = []
                                for it in items:
                                    name = it.get('name') or it.get('item', {}).get('name')
                                    if name:
                                        categories.append(name)

                                skip_categories = ['หน้าแรก', 'home', 'สินค้า', 'products', 'ทั้งหมด', 'all', 'thaiwatsadu', 'ไทวัสดุ']
                                for cat in reversed(categories[:-1]):
                                    cat_clean = cat.strip()
                                    if cat_clean and cat_clean.lower() not in [s.lower() for s in skip_categories]:
                                        return cat_clean
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

        # 3. Try standard HTML breadcrumb patterns
        breadcrumb_patterns = [
            r'<nav[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</nav>',
            r'<div[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</div>',
            r'<ol[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</ol>',
            r'<ul[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</ul>',
        ]

        for pattern in breadcrumb_patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                breadcrumb_content = match.group(1)
                category_matches = re.findall(r'<a[^>]*>([^<]+)</a>', breadcrumb_content)
                if not category_matches:
                    category_matches = re.findall(r'<span[^>]*>([^<]+)</span>', breadcrumb_content)

                skip_categories = ['หน้าแรก', 'home', 'สินค้า', 'products', 'ทั้งหมด', 'all']
                for cat in reversed(category_matches):
                    cat_clean = self._clean_text(cat)
                    if cat_clean and cat_clean.lower() not in skip_categories:
                        return cat_clean

        # 4. Try Product JSON-LD category field
        try:
            product_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(product_pattern, html_content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        category = data.get('category')
                        if category:
                            if isinstance(category, list):
                                for cat in reversed(category):
                                    if cat and cat.lower() not in ['สินค้า', 'products']:
                                        return cat
                            elif isinstance(category, str):
                                return category
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

        return None

    def _extract_thaiwatsadu_specs(self, html_content: str) -> Dict[str, str]:
        """Extract product specifications from Thai Watsadu's 'ข้อมูลเฉพาะสินค้า' section.

        Parses the flex-based specification table and returns a dictionary of extracted values.
        """
        specs = {}

        # Map Thai labels to our field names (order matters - more specific first)
        label_mapping = [
            ('ขนาด (กxลxส)(ซม.)', 'dimensions'),
            ('ขนาด(กxลxส)(ซม.)', 'dimensions'),
            ('ขนาดสินค้า (ซม.)', 'dimensions'),
            ('วัสดุหลัก', 'material'),
            ('วัสดุด้ามจับ', 'handle_material'),
            ('วัสดุ', 'material'),
            ('แบรนด์', 'brand'),
            ('ยี่ห้อ', 'brand'),
            ('สี', 'color'),
            ('รุ่น', 'model'),
            ('น้ำหนัก (กก.)', 'weight'),
            ('น้ำหนัก', 'weight'),
            ('ประเภท', 'type'),
            ('ฟังก์ชัน', 'function'),
            ('ขนาด', 'size'),  # Generic size - must be last
        ]

        try:
            # Method 1: Direct pattern matching for Thai Watsadu spec table
            # HTML: <div class="w-1/2..."><div>LABEL</div></div><div class="w-1/2"><div>VALUE</div></div>
            for thai_label, field_name in label_mapping:
                escaped_label = re.escape(thai_label)
                # Pattern: label div -> close div -> close parent div -> value div container -> value div
                patterns = [
                    # Most specific: exact structure with w-1/2 class
                    rf'<div>{escaped_label}</div></div><div class="w-1/2"><div>([^<]+)</div>',
                    # With whitespace
                    rf'<div>{escaped_label}</div>\s*</div>\s*<div\s+class="w-1/2">\s*<div>([^<]+)</div>',
                    # More flexible class matching
                    rf'<div>{escaped_label}</div></div><div[^>]*class="[^"]*w-1/2[^"]*"[^>]*><div>([^<]+)</div>',
                ]
                for pattern in patterns:
                    match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value:
                            clean_value = self._clean_thaiwatsadu_text(value)
                            if clean_value:
                                if field_name == 'dimensions':
                                    specs['dimensions'] = clean_value
                                elif field_name == 'size' and 'dimensions' not in specs:
                                    specs['size'] = clean_value
                                elif field_name not in specs:
                                    specs[field_name] = clean_value
                                break
                if field_name in specs or (field_name == 'dimensions' and 'dimensions' in specs):
                    continue

            # Method 2: Direct search for dimension value format (18 x 2 x 13)
            if 'dimensions' not in specs:
                # Look for X x Y x Z pattern wrapped in div tags
                dim_match = re.search(r'<div>(\d+\s*x\s*\d+\s*x\s*\d+)</div>', html_content, re.IGNORECASE)
                if dim_match:
                    specs['dimensions'] = dim_match.group(1).strip()

            # Method 2b: Extract from delivery size format (ก) 35 x (ย) 67 x (ส) 50
            if 'dimensions' not in specs:
                # Pattern for Thai Watsadu delivery size: (ก)35 x (ย)67 x (ส)50
                # Also handles decimals like 12.5 x 3.5 x 19
                # HTML: (<!-- -->ก<!-- -->)<!-- -->35<!-- --> x (<!-- -->ย<!-- -->)<!-- -->67<!-- --> x (<!-- -->ส<!-- -->)<!-- -->50
                delivery_pattern = r'\((?:<!--[^>]*-->)*ก(?:<!--[^>]*-->)*\)(?:<!--[^>]*-->)*([\d.]+)(?:<!--[^>]*-->)*\s*x\s*\((?:<!--[^>]*-->)*ย(?:<!--[^>]*-->)*\)(?:<!--[^>]*-->)*([\d.]+)(?:<!--[^>]*-->)*\s*x\s*\((?:<!--[^>]*-->)*ส(?:<!--[^>]*-->)*\)(?:<!--[^>]*-->)*([\d.]+)'
                delivery_match = re.search(delivery_pattern, html_content, re.IGNORECASE)
                if delivery_match:
                    w, d, h = delivery_match.group(1), delivery_match.group(2), delivery_match.group(3)
                    specs['dimensions'] = f"{w} x {d} x {h}"

            # Method 3: Look for material value "เหล็ก CR-V" pattern
            if 'material' not in specs:
                material_patterns = [
                    r'<div>วัสดุหลัก</div></div><div class="w-1/2"><div>([^<]+)</div>',
                    r'<div>วัสดุหลัก</div>\s*</div>\s*<div[^>]*class="[^"]*w-1/2[^"]*"[^>]*>\s*<div>([^<]+)</div>',
                    r'>วัสดุหลัก</div></div><div[^>]*><div>([^<]+)</div>',
                ]
                for pattern in material_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value:
                            specs['material'] = self._clean_thaiwatsadu_text(value)
                            break

            # If we have size but not dimensions, use size as dimensions
            if 'size' in specs and 'dimensions' not in specs:
                specs['dimensions'] = specs['size']

        except Exception:
            pass

        return specs

    def _extract_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON-LD data from HTML."""
        try:
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.finditer(pattern, html_content, re.DOTALL)

            for match in matches:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return data
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return None


class HomeProExtractor(ProductExtractor):
    """Specialized extractor for HomePro website with enhanced JSON-LD and field sanitization."""

    # HomePro specific strings to filter out
    HOMEPRO_FILTER_STRINGS = [
        'homepro', 'home pro', 'โฮมโปร',
        'กรุณากดยืนยันเพื่อออกจากระบบ',  # Logout confirmation message
        'ศูนย์การตั้งค่าความเป็นส่วนตัว',  # Privacy settings
    ]

    # Invalid model values to filter
    INVALID_MODEL_VALUES = [
        'อื่น', 'อื่นๆ', 'other', 'others', '-', 'n/a', 'na', 'none',
    ]

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from HomePro using JSON-LD as primary source."""
        product = ProductData(url=url)

        # 1. Extract SKU from URL first (most reliable for HomePro)
        # URL pattern: /p/246513
        if url:
            sku_match = re.search(r'/p/(\d+)', url)
            if sku_match:
                product.sku = sku_match.group(1)

        # 2. Try JSON-LD extraction (primary source for HomePro - most accurate)
        json_ld_data = self._extract_json_ld(html_content)

        if json_ld_data:
            # Name from JSON-LD
            product.name = self._clean_homepro_text(json_ld_data.get('name'))

            # Description from JSON-LD
            desc = json_ld_data.get('description')
            if desc:
                product.description = self._clean_homepro_text(desc, strip_html=True)

            # Brand from JSON-LD
            brand_value = json_ld_data.get('brand')
            if brand_value:
                if isinstance(brand_value, dict):
                    brand_value = brand_value.get('name')
                if brand_value:
                    product.brand = self._clean_homepro_text(str(brand_value))

            # SKU from JSON-LD (backup)
            if not product.sku:
                sku_value = json_ld_data.get('sku')
                if sku_value:
                    product.sku = str(sku_value).strip()

            # Price from JSON-LD offers (most reliable)
            offers = json_ld_data.get('offers', {})
            if isinstance(offers, dict):
                price = offers.get('price')
                if price:
                    try:
                        product.current_price = float(price)
                    except (ValueError, TypeError):
                        pass

            # Images from JSON-LD
            image = json_ld_data.get('image')
            if image:
                if isinstance(image, list):
                    # Filter to only product images (cdn.homepro.co.th)
                    product.images = [img for img in image if 'cdn.homepro.co.th' in img and 'ART_IMAGE' in img]
                elif isinstance(image, str):
                    if 'cdn.homepro.co.th' in image:
                        product.images = [image]

        # 2b. If JSON-LD price not found, try HomePro-specific HTML price patterns
        if not product.current_price:
            # HomePro specific price patterns - prioritized from most specific to general
            # Based on actual HTML: <input id="gtmPrice-246513" value="209.0">
            #                       <span class="amount">209</span>
            #                       <div class="price">฿ 209</div>
            homepro_price_patterns = [
                # GTM hidden input (most reliable) - id="gtmPrice-246513" value="209.0"
                r'<input[^>]*id=["\']gtmPrice-\d+["\'][^>]*value=["\']([\d.]+)["\']',
                # Discount/sale price span with amount class
                r'<span[^>]*class=["\']amount["\'][^>]*>([\d,]+)</span>',
                # Price div with ฿ symbol
                r'<div[^>]*class=["\'](?:price|offer-price)["\'][^>]*>\s*฿\s*([\d,]+)',
                # Price with ฿ symbol in various formats
                r'฿\s*([\d,]+(?:\.\d{2})?)\s*</span>',
                r'฿\s*([\d,]+(?:\.\d{2})?)\s*</div>',
                # Price meta tag
                r'<meta[^>]*property=["\']product:price:amount["\'][^>]*content=["\']([\d.]+)["\']',
            ]

            for pattern in homepro_price_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if matches:
                    # Filter to reasonable price range (1-100000 THB)
                    for price_str in matches:
                        try:
                            price = float(price_str.replace(',', ''))
                            if 1 <= price <= 100000:
                                product.current_price = price
                                break
                        except ValueError:
                            continue
                if product.current_price:
                    break

        # 3. Extract original price from HTML (for discount calculation)
        # HomePro HTML: <div class="original-price">...<span class="amount">235</span>
        if not product.original_price:
            orig_price_patterns = [
                # HomePro original-price div with amount span
                r'<div[^>]*class=["\']original-price["\'][^>]*>.*?<span[^>]*class=["\']amount["\'][^>]*>([\d,]+)</span>',
                # Original price div with direct number
                r'<div[^>]*class=["\']original-price["\'][^>]*>\s*([\d,]+)',
                # Line-through style
                r'<span[^>]*class="[^"]*line-through[^"]*"[^>]*>.*?฿?\s*([\d,]+)',
                r'<del[^>]*>.*?฿?\s*([\d,]+)',
                r'ราคาปกติ[:\s]*฿?\s*([\d,]+)',
            ]
            for pattern in orig_price_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace(',', '')
                    try:
                        orig_price = float(price_str)
                        if orig_price > 0 and (not product.current_price or orig_price > product.current_price):
                            product.original_price = orig_price
                            break
                    except ValueError:
                        pass

        # 4. Extract category from breadcrumb
        product.category = self._extract_homepro_category(html_content)

        # 5. Extract dimensions, volume, and other specs from product specifications
        specs = self._extract_homepro_specs(html_content)
        if specs:
            if specs.get('dimensions'):
                product.dimensions = specs['dimensions']
            if specs.get('volume') and not product.volume:
                product.volume = specs['volume']
            if specs.get('color') and not product.color:
                product.color = specs['color']
            if specs.get('brand') and not product.brand:
                product.brand = specs['brand']
            if specs.get('model') and not product.model:
                # Filter invalid model values
                model = specs['model']
                if model.lower() not in [v.lower() for v in self.INVALID_MODEL_VALUES]:
                    product.model = model

        # 6. Extract product name from HTML if not found in JSON-LD
        if not product.name:
            name_patterns = [
                r'<h1[^>]*class="[^"]*product[^"]*name[^"]*"[^>]*>(.*?)</h1>',
                r'<h1[^>]*class="[^"]*pdp[^"]*"[^>]*>(.*?)</h1>',
                r'<h1[^>]*>(.*?)</h1>',
            ]
            for pattern in name_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    name = self._clean_text(match.group(1))
                    name = self._clean_homepro_text(name)
                    if name and len(name) > 3:
                        product.name = name
                        break

        # 7. Extract images from HTML if not found (fallback)
        if not product.images:
            # HomePro product images pattern
            img_patterns = [
                r'<img[^>]*src="(https://cdn\.homepro\.co\.th/ART_IMAGE[^"]+)"',
                r'"(https://cdn\.homepro\.co\.th/ART_IMAGE[^"]+)"',
            ]
            images = []
            for pattern in img_patterns:
                matches = re.findall(pattern, html_content)
                for img in matches:
                    if img not in images:
                        images.append(img)
            if images:
                product.images = images[:10]

        # 8. Clean and validate color field (prevent CSS contamination)
        if product.color:
            product.color = self._sanitize_homepro_color(product.color)

        # 9. Clean model field (filter invalid values)
        if product.model:
            if product.model.lower() in [v.lower() for v in self.INVALID_MODEL_VALUES]:
                product.model = None

        # 10. Extract brand from product name if not found elsewhere
        # Pattern: "Product Name BRAND 500ml" - brand is often uppercase word before size
        if not product.brand and product.name:
            # Common Thai hardware store brands
            known_brands = [
                'HG', 'KARCHER', 'BOSCH', 'MAKITA', 'DEWALT', 'MILWAUKEE', 'STANLEY',
                'BLACK+DECKER', 'PHILIPS', 'PANASONIC', 'TOSHIBA', 'LG', 'SAMSUNG',
                'ELECTROLUX', 'MITSUBISHI', 'DAIKIN', 'HITACHI', 'SHARP', 'HAIER',
                'TOA', 'BEGER', 'NIPPON', 'JOTUN', 'DULUX',
                'COTTO', 'AMERICAN STANDARD', 'KOHLER', 'GROHE', 'TOTO',
                'YALE', 'HAFELE', 'SCHLAGE', 'SCG', '3M', 'SCOTCH-BRITE',
            ]
            name_upper = product.name.upper()
            for brand in known_brands:
                if brand in name_upper:
                    product.brand = brand
                    break

            # Try to find uppercase word that looks like a brand
            if not product.brand:
                brand_match = re.search(r'\b([A-Z][A-Z0-9+\-]{1,15})\b', product.name)
                if brand_match:
                    potential_brand = brand_match.group(1)
                    # Filter out size indicators
                    if potential_brand not in ['ML', 'CM', 'MM', 'KG', 'G', 'L', 'M', 'W', 'V', 'HP']:
                        product.brand = potential_brand

        # 11. Fallback: use base extraction for missing fields
        if not product.name or not product.current_price:
            base_product = super().extract_from_html(html_content, url)
            if base_product:
                if not product.name:
                    product.name = self._clean_homepro_text(base_product.name)
                # Use base price only if we truly have nothing
                # But reject prices that look like volume/size (50, 100, 250, 500, 1000 are common ml values)
                if not product.current_price and base_product.current_price:
                    price = base_product.current_price
                    # Common volume values in ml that get mistaken for prices
                    volume_values = [50, 100, 150, 200, 250, 300, 400, 500, 750, 1000]
                    # Also check if price matches product name volume (e.g., "500ml" -> 500)
                    is_volume_in_name = False
                    if product.name:
                        vol_match = re.search(r'(\d+)\s*(?:ml|มล|ลิตร|L|g|กรัม)', product.name, re.IGNORECASE)
                        if vol_match:
                            vol_value = int(vol_match.group(1))
                            if price == vol_value or price == vol_value * 10:
                                is_volume_in_name = True

                    if not is_volume_in_name and price not in volume_values:
                        if 10 <= price <= 50000:
                            product.current_price = price

                if not product.original_price and base_product.original_price:
                    orig_price = base_product.original_price
                    # Same volume filter for original price
                    volume_values = [50, 100, 150, 200, 250, 300, 400, 500, 750, 1000]
                    is_volume_in_name = False
                    if product.name:
                        vol_match = re.search(r'(\d+)\s*(?:ml|มล|ลิตร|L|g|กรัม)', product.name, re.IGNORECASE)
                        if vol_match:
                            vol_value = int(vol_match.group(1))
                            if orig_price == vol_value or orig_price == vol_value * 10:
                                is_volume_in_name = True

                    if not is_volume_in_name and orig_price not in volume_values:
                        if 10 <= orig_price <= 100000:
                            product.original_price = orig_price

        product.retailer = "HomePro"
        return product

    def _clean_homepro_text(self, text: str, strip_html: bool = False) -> Optional[str]:
        """Remove HomePro specific contamination from text."""
        if not text:
            return None

        # Strip HTML tags if requested
        if strip_html:
            text = re.sub(r'<[^>]+>', '', text)

        # Remove HomePro branding and invalid messages
        for filter_str in self.HOMEPRO_FILTER_STRINGS:
            text = re.sub(re.escape(filter_str), '', text, flags=re.IGNORECASE)

        # Remove patterns like "- HomePro" or "| HomePro"
        text = re.sub(r'[-|]\s*$', '', text)

        # Clean whitespace
        text = ' '.join(text.split()).strip()

        # Remove trailing punctuation
        text = text.rstrip('-|,;:')

        return text if text else None

    def _sanitize_homepro_color(self, color: str) -> Optional[str]:
        """Sanitize color field to prevent CSS contamination."""
        if not color:
            return None

        # Check for CSS contamination patterns
        css_contamination_patterns = [
            r'margin', r'padding', r'px', r'rem', r'em',
            r'font', r'color:', r'background', r'border',
            r'display', r'position', r'width', r'height',
            r'ศูนย์การตั้งค่า', r'ความเป็นส่วนตัว',
        ]

        color_lower = color.lower()
        for pattern in css_contamination_patterns:
            if re.search(pattern, color_lower):
                return None

        # Apply general color sanitization
        clean_color = self._sanitize_color_field(color)
        return clean_color

    def _extract_homepro_category(self, html_content: str) -> Optional[str]:
        """Extract category from HomePro breadcrumb."""
        # Try breadcrumb patterns
        breadcrumb_patterns = [
            r'<nav[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</nav>',
            r'<div[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</div>',
            r'<ol[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</ol>',
        ]

        for pattern in breadcrumb_patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                breadcrumb_content = match.group(1)
                # Extract category names from links
                category_matches = re.findall(r'<a[^>]*>([^<]+)</a>', breadcrumb_content)
                if not category_matches:
                    category_matches = re.findall(r'<span[^>]*>([^<]+)</span>', breadcrumb_content)

                skip_categories = ['หน้าแรก', 'home', 'homepro', 'โฮมโปร', 'สินค้า', 'products']
                for cat in reversed(category_matches[:-1] if len(category_matches) > 1 else category_matches):
                    cat_clean = self._clean_text(cat)
                    if cat_clean and cat_clean.lower() not in skip_categories:
                        return cat_clean

        return None

    def _extract_homepro_specs(self, html_content: str) -> Dict[str, str]:
        """Extract product specifications from HomePro product page.

        HomePro specs are in table format:
        <tr class="pdp-HO_HEIGHT">
            <td>ความสูง (ซม.)</td>
            <td>25</td>
        </tr>
        """
        specs = {}

        # HomePro table-based spec patterns - label in first td, value in second td
        # Pattern: <td>label</td>...<td>value</td>
        table_spec_patterns = [
            (r'<td[^>]*>ความสูง[^<]*</td>\s*<td[^>]*>([\d.]+)</td>', 'height'),
            (r'<td[^>]*>ความกว้าง[^<]*</td>\s*<td[^>]*>([\d.]+)</td>', 'width'),
            (r'<td[^>]*>ความลึก[^<]*</td>\s*<td[^>]*>([\d.]+)</td>', 'depth'),
            (r'<td[^>]*>น้ำหนัก[^<]*</td>\s*<td[^>]*>([\d.]+)</td>', 'weight'),
            (r'<td[^>]*>ขนาดสินค้า</td>\s*<td[^>]*>([^<]+)</td>', 'size'),
            (r'<td[^>]*>สี</td>\s*<td[^>]*>([^<]+)</td>', 'color'),
            (r'<td[^>]*>ยี่ห้อ</td>\s*<td[^>]*>([^<]+)</td>', 'brand'),
            (r'<td[^>]*>รุ่น</td>\s*<td[^>]*>([^<]+)</td>', 'model'),
        ]

        for pattern, field in table_spec_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                value = self._clean_text(match.group(1))
                if value and len(value) < 100:
                    specs[field] = value

        # Build dimensions from height/width/depth
        if 'height' in specs or 'width' in specs or 'depth' in specs:
            dim_parts = []
            for key in ['width', 'depth', 'height']:
                if key in specs:
                    # Extract numeric value - require at least one digit
                    num_match = re.search(r'(\d+(?:\.\d+)?)', specs[key])
                    if num_match:
                        dim_parts.append(num_match.group(1))
            # Only build dimensions if we have at least 2 valid numeric parts
            if len(dim_parts) >= 2:
                specs['dimensions'] = ' x '.join(dim_parts) + ' cm'

        # Extract volume from size field (e.g., "500ML")
        if 'size' in specs and not specs.get('volume'):
            size_val = specs['size'].upper()
            vol_match = re.search(r'(\d+)\s*(ML|L|ลิตร|มล)', size_val, re.IGNORECASE)
            if vol_match:
                specs['volume'] = specs['size']

        return specs

    def _extract_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON-LD data from HTML."""
        try:
            pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.finditer(pattern, html_content, re.DOTALL)

            for match in matches:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return data
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return None


class BoonthavornExtractor(ProductExtractor):
    """Specialized extractor for Boonthavorn website using JSON-LD with enhanced sanitization."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Boonthavorn using JSON-LD and HTML parsing with enhanced sanitization."""
        product = ProductData(url=url)

        # 1. Try to extract from JSON-LD (Structured Data) - Most reliable for basic info
        json_ld_data = self._extract_json_ld(html_content)

        if json_ld_data:
            product.name = json_ld_data.get('name')
            product.description = json_ld_data.get('description')

            # Enhanced brand extraction with sanitization
            brand_value = json_ld_data.get('brand')
            if brand_value:
                if isinstance(brand_value, dict):
                    brand_value = brand_value.get('name')
                if brand_value:
                    clean_brand = self._sanitize_brand_field(str(brand_value))
                    product.brand = clean_brand

            # Enhanced SKU extraction with validation
            sku_value = json_ld_data.get('sku')
            if sku_value:
                clean_sku = self._sanitize_sku_field(str(sku_value))
                product.sku = clean_sku

            offers = json_ld_data.get('offers', {})
            if isinstance(offers, dict):
                price = offers.get('price')
                if price:
                    product.current_price = float(price)
                    product.currency = offers.get('priceCurrency', 'THB')

            image = json_ld_data.get('image')
            if image:
                if isinstance(image, list):
                    product.images = image
                elif isinstance(image, str):
                    product.images = [image]

        # 2. Extract attributes from "Quick Info" section (HTML) with enhanced sanitization
        # Pattern: <label class="quickInfo-infoLabel-WkG">Label</label><label class="quickInfo-infoValue-NpP">Value</label>
        quick_info_pattern = r'class="quickInfo-infoLabel-[^"]+">([^<]+)</label><label class="quickInfo-infoValue-[^"]+">([^<]+)</label>'
        attributes = dict(re.findall(quick_info_pattern, html_content))

        if attributes:
            # Enhanced color extraction with CSS prevention
            if 'สี' in attributes and not product.color:
                color_value = attributes['สี'].strip()
                clean_color = self._sanitize_color_field(color_value)
                product.color = clean_color

            # Enhanced dimensions extraction
            if 'ขนาดสินค้า' in attributes:
                dimensions_value = attributes['ขนาดสินค้า'].strip()
                clean_dimensions = self._sanitize_dimensions_field(dimensions_value)
                product.dimensions = clean_dimensions

            # Enhanced volume extraction - get weight (น้ำหนัก) instead of unit count
            if 'น้ำหนัก' in attributes:
                weight_value = attributes['น้ำหนัก'].strip()
                clean_weight = self._sanitize_text_field(weight_value, max_length=50)
                product.volume = clean_weight

        # 2.3. Fallback: Extract weight from specifications tab or other patterns
        if not product.volume:
            # Try to find weight in various formats
            weight_patterns = [
                # Boonthavorn productAttributes pattern: <span class="productAttributes-name">น้ำหนัก</span>...<div class="richContent-root">2.2 KG</div>
                r'productAttributes-name[^>]*>น้ำหนัก</span>.*?richContent-root[^>]*>([^<]+)</div>',
                # Pattern: น้ำหนัก followed by number and unit
                r'น้ำหนัก[:\s]*([0-9.]+\s*(?:KG|kg|Kg|กก\.|กิโลกรัม))',
                # Pattern in table/list format
                r'>น้ำหนัก<[^>]*>[^<]*<[^>]*>([^<]+(?:KG|kg|กก))',
                # General weight pattern
                r'(?:Weight|weight)[:\s]*([0-9.]+\s*(?:KG|kg))',
            ]
            for pattern in weight_patterns:
                weight_match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if weight_match:
                    product.volume = weight_match.group(1).strip()
                    break

        if attributes:
            # Enhanced brand extraction
            if 'ยี่ห้อ' in attributes and not product.brand:
                brand_value = attributes['ยี่ห้อ'].strip()
                clean_brand = self._sanitize_brand_field(brand_value)
                if clean_brand:
                    product.brand = clean_brand

            # Enhanced SKU extraction with validation
            if 'รหัสสินค้า' in attributes and (not product.sku or product.sku == 'None'):
                sku_value = attributes['รหัสสินค้า'].strip()
                clean_sku = self._sanitize_sku_field(sku_value)
                if clean_sku:
                    product.sku = clean_sku

        # 2.5. Extract category from breadcrumbs - get the last category link (parent of product)
        # Pattern: <a class="breadcrumbs-link-mHX" href="...">CATEGORY</a>
        breadcrumb_links = re.findall(r'<a[^>]*class="breadcrumbs-link-[^"]*"[^>]*>([^<]+)</a>', html_content)
        if breadcrumb_links and len(breadcrumb_links) > 0:
            # The last link is the immediate parent category (before product name)
            category = breadcrumb_links[-1].strip()
            if category:
                product.category = category

        # 3. Extract Original Price (if exists) with enhanced cleaning
        if not product.original_price:
            old_price_match = re.search(r'productPrice-oldPrice.*?price-currency-[^>]+>บาท</span>((?:<span>[^<]+</span>)+)', html_content)
            if old_price_match:
                raw_price = old_price_match.group(1)
                # Remove tags and commas with enhanced cleaning
                clean_price = re.sub(r'<[^>]+>|,', '', raw_price)
                clean_price = ' '.join(clean_price.split()).strip()
                try:
                    product.original_price = float(clean_price)
                except ValueError:
                    pass

        # 4. Fallback/Supplement with base HTML extraction
        html_product = super().extract_from_html(html_content, url)
        if html_product:
            if not product.name: product.name = html_product.name
            if not product.description: product.description = html_product.description
            if not product.images: product.images = html_product.images

            # Use base extraction for material if not found yet
            if html_product.material and not product.material:
                product.material = html_product.material

        # 5. Extract Model from Name or Description with enhanced pattern matching
        if product.name and 'รุ่น' in product.name:
            model_match = re.search(r'รุ่น\s+([A-Za-z0-9\-_\s]+)', product.name)
            if model_match:
                model_value = model_match.group(1).strip()
                clean_model = self._sanitize_text_field(model_value, max_length=200)
                if clean_model:
                    product.model = clean_model
        elif product.description and 'รุ่น' in product.description:
            model_match = re.search(r'รุ่น\s+([A-Za-z0-9\-_\s]+)', product.description)
            if model_match:
                model_value = model_match.group(1).strip()
                clean_model = self._sanitize_text_field(model_value, max_length=200)
                if clean_model:
                    product.model = clean_model

        # 6. Enhanced URL-based SKU fallback with validation
        if url and (not product.sku or product.sku == 'None'):
            url_patterns = [
                r'-(\d+)$',
                r'/product/([^/]+)',
                r'/item/([^/]+)'
            ]
            for pattern in url_patterns:
                match = re.search(pattern, url)
                if match:
                    potential_sku = match.group(1).strip()
                    if self._is_valid_sku(potential_sku):
                        product.sku = potential_sku
                        break

        product.retailer = "Boonthavorn"
        return product

    def _extract_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON-LD data from HTML."""
        try:
            # Regex to find the script tag content
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.finditer(pattern, html_content, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match.group(1))
                    # We are looking for @type Product
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return data
                    # Sometimes it's a list of objects
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return None


class MegaHomeExtractor(ProductExtractor):
    """Specialized extractor for Mega Home website with specific HTML patterns."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Mega Home using its HTML patterns."""
        product = ProductData(url=url)

        # 1. Extract product name from prd-name h1
        name_match = re.search(r'<div class="prd-name">\s*<h1>([^<]+)</h1>', html_content)
        if name_match:
            product.name = name_match.group(1).strip()

        # 2. Extract brand from prd-brand
        brand_match = re.search(r'<div class="prd-brand">\s*<a[^>]*>([^<]+)</a>', html_content)
        if brand_match:
            product.brand = brand_match.group(1).strip()

        # 3. Extract price from discount-price span.amount or gtmPrice hidden input
        price_match = re.search(r'<div class="discount-price">.*?<span class="amount">([0-9,.]+)</span>', html_content, re.DOTALL)
        if price_match:
            try:
                product.current_price = float(price_match.group(1).replace(',', ''))
            except ValueError:
                pass
        # Fallback to hidden gtmPrice input
        if not product.current_price:
            gtm_price = re.search(r'<input[^>]*id="gtmPrice-\d+"[^>]*value="([0-9.]+)"', html_content)
            if gtm_price:
                try:
                    product.current_price = float(gtm_price.group(1))
                except ValueError:
                    pass

        # 4. Extract original price
        orig_price_match = re.search(r'<div class="original-price">.*?<span class="amount">([0-9,.]+)</span>', html_content, re.DOTALL)
        if orig_price_match:
            try:
                product.original_price = float(orig_price_match.group(1).replace(',', ''))
            except ValueError:
                pass

        # 5. Extract SKU from URL or hidden input
        if url:
            url_match = re.search(r'/p/(\d+)', url)
            if url_match:
                product.sku = url_match.group(1)

        # 6. Extract specification table values
        # MegaHome uses category prefixes: pdp-HT_ (Home Tools), pdp-LT_ (Lighting), etc.
        # Use generic pattern pdp-[A-Z]+_ to match any category

        # Material: pdp-*_MATERIAL
        material_match = re.search(r'class="pdp-[A-Z]+_MATERIAL"[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html_content, re.DOTALL)
        if material_match:
            product.material = material_match.group(1).strip()

        # Color: pdp-*_COLOR
        color_match = re.search(r'class="pdp-[A-Z]+_COLOR"[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html_content, re.DOTALL)
        if color_match:
            product.color = color_match.group(1).strip()

        # Dimensions: width x depth x height (skip label in first td, capture value in second td)
        width_match = re.search(r'class="pdp-[A-Z]+_WIDTH"[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html_content, re.DOTALL)
        depth_match = re.search(r'class="pdp-[A-Z]+_DEPTH"[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html_content, re.DOTALL)
        height_match = re.search(r'class="pdp-[A-Z]+_HEIGHT"[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html_content, re.DOTALL)

        dims = []
        if width_match:
            dims.append(width_match.group(1).strip())
        if depth_match:
            dims.append(depth_match.group(1).strip())
        if height_match:
            dims.append(height_match.group(1).strip())
        if dims:
            product.dimensions = ' x '.join(dims) + ' cm'

        # Weight: pdp-*_WEIGHT
        weight_match = re.search(r'class="pdp-[A-Z]+_WEIGHT"[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html_content, re.DOTALL)
        if weight_match:
            weight_val = weight_match.group(1).strip()
            if weight_val:
                product.volume = weight_val + ' kg'

        # 7. Extract images from image-index elements
        images = []
        img_matches = re.findall(r'<img[^>]*id="image-index-\d+"[^>]*src="([^"]+)"', html_content)
        for img_url in img_matches:
            if img_url and img_url not in images:
                images.append(img_url)
        product.images = images

        # 8. Extract category from breadcrumb (last item before product)
        breadcrumb_match = re.search(r'<div class="active section">([^<]+)</div>', html_content)
        # Get the breadcrumb links instead
        breadcrumb_links = re.findall(r'<a class="section"[^>]*>([^<]+)</a>', html_content)
        if breadcrumb_links:
            product.category = breadcrumb_links[-1].strip()

        # 9. Extract color from product name if not found in spec table (สีเงิน, สีดำ, etc.)
        if not product.color and product.name:
            color_match = re.search(r'สี(\S+)', product.name)
            if color_match:
                product.color = 'สี' + color_match.group(1)

        # 10. Extract model from product name (NO.2000, รุ่น XXX, etc.)
        if product.name:
            model_match = re.search(r'(?:NO\.|รุ่น\s*)([A-Za-z0-9\-_.]+)', product.name)
            if model_match:
                product.model = model_match.group(1).strip()

        product.retailer = "Mega Home"
        return product


class DoHomeExtractor(ProductExtractor):
    """Specialized extractor for DoHome website."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from DoHome."""
        product = ProductData(url=url)

        # 1. Try JSON-LD extraction first
        json_ld_data = self._extract_json_ld(html_content)

        if json_ld_data:
            product.name = json_ld_data.get('name')
            product.description = json_ld_data.get('description')

            brand_value = json_ld_data.get('brand')
            if brand_value:
                if isinstance(brand_value, dict):
                    brand_value = brand_value.get('name')
                if brand_value:
                    product.brand = self._sanitize_brand_field(str(brand_value))

            sku_value = json_ld_data.get('sku')
            if sku_value:
                product.sku = self._sanitize_sku_field(str(sku_value))

            offers = json_ld_data.get('offers', {})
            if isinstance(offers, dict):
                price = offers.get('price')
                if price:
                    try:
                        product.current_price = float(price)
                    except (ValueError, TypeError):
                        pass

            image = json_ld_data.get('image')
            if image:
                if isinstance(image, list):
                    product.images = image
                elif isinstance(image, str):
                    product.images = [image]

        # 2. Extract from HTML patterns specific to DoHome
        # Product name from h1 or specific DoHome classes
        if not product.name:
            name_patterns = [
                r'<h1[^>]*class="[^"]*product[^"]*name[^"]*"[^>]*>(.*?)</h1>',
                r'<h1[^>]*class="[^"]*pdp[^"]*"[^>]*>(.*?)</h1>',
                r'<h1[^>]*>(.*?)</h1>',
                r'<div[^>]*class="[^"]*product-name[^"]*"[^>]*>(.*?)</div>',
            ]
            for pattern in name_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    name = self._clean_text(match.group(1))
                    if name and len(name) > 3 and 'dohome' not in name.lower():
                        product.name = name
                        break

        # 3. Extract price from DoHome-specific patterns
        if not product.current_price:
            # DoHome uses Next.js/React with Tailwind CSS classes
            price_patterns = [
                # DoHome main price: <span class="text-3xl font-semibold text-[#343A40]">฿1,090.00</span>
                r'<span[^>]*class="[^"]*text-3xl[^"]*font-semibold[^"]*"[^>]*>฿?([\d,]+(?:\.\d{2})?)</span>',
                # JSON data in page: "marketPrice":"฿1,090.00"
                r'"marketPrice"\s*:\s*"฿?([\d,]+(?:\.\d{2})?)"',
                # Sale price in JSON: "salePrice":"฿999.00"
                r'"salePrice"\s*:\s*"฿?([\d,]+(?:\.\d{2})?)"',
                # Generic price with ฿ symbol
                r'>฿([\d,]+(?:\.\d{2})?)<',
                # Legacy patterns
                r'<span[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</span>',
                r'ราคา[:\s]*([฿]?[\d,]+\.?\d*)',
            ]
            for pattern in price_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    price_text = self._clean_text(match.group(1))
                    price = PriceParser.parse_price(price_text)
                    if price and price > 0:
                        product.current_price = price
                        break

        # 4. Extract original price
        if not product.original_price:
            orig_patterns = [
                r'<span[^>]*class="[^"]*old-price[^"]*"[^>]*>(.*?)</span>',
                r'<span[^>]*class="[^"]*regular-price[^"]*"[^>]*>(.*?)</span>',
                r'ราคาปกติ[:\s]*([฿]?[\d,]+\.?\d*)',
            ]
            for pattern in orig_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    price_text = self._clean_text(match.group(1))
                    price = PriceParser.parse_price(price_text)
                    if price and price > 0:
                        product.original_price = price
                        break

        # 5. Extract SKU from URL pattern: /product/product-name-SKU
        if url and not product.sku:
            # DoHome URL pattern: /product/product-name-10026550
            sku_match = re.search(r'-(\d{6,})(?:\?|$)', url)
            if sku_match:
                potential_sku = sku_match.group(1)
                if self._is_valid_sku(potential_sku):
                    product.sku = potential_sku

        # 6. Extract brand from HTML - DoHome specific patterns
        if not product.brand:
            brand_patterns = [
                # DoHome brand link: <a href="/brand/nippon">NIPPON</a>
                r'<a[^>]*href="/brand/[^"]*"[^>]*>([^<]+)</a>',
                # Fallback patterns
                r'<span[^>]*class="[^"]*brand[^"]*"[^>]*>([^<]+)</span>',
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    brand = self._clean_text(match.group(1))
                    # Validate brand - must be short and not contain garbage
                    if brand and len(brand) < 50 and not any(x in brand.lower() for x in ['attribute', 'product', 'sku', 'stock', 'link']):
                        product.brand = brand.strip()
                        break

        # 7. Extract category from DoHome breadcrumb
        if not product.category:
            # DoHome category in breadcrumb: <a href="/category/...">Category Name</a>
            cat_patterns = [
                r'<a[^>]*href="/category/[^"]*"[^>]*>([^<]+)</a>',
                r'"categoryName"\s*:\s*"([^"]+)"',
            ]
            for pattern in cat_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for cat in matches:
                    cat = self._clean_text(cat)
                    if cat and len(cat) > 2 and cat.lower() not in ['หน้าแรก', 'home', 'สินค้า', 'products', 'dohome']:
                        product.category = cat
                        break
                if product.category:
                    break

        # 8. Extract specifications from DoHome JSON data in page
        # DoHome embeds specs in Next.js script tags with escaped quotes: \"dimension\":{\"width\":29.6,...}
        # Extract dimension values directly using regex (handles both escaped and normal quotes)
        dimension_match = re.search(
            r'\\?"dimension\\?"\s*:\s*\{[^}]*\\?"width\\?"\s*:\s*([\d.]+)[^}]*\\?"long\\?"\s*:\s*([\d.]+)[^}]*\\?"high\\?"\s*:\s*([\d.]+)[^}]*\\?"weight\\?"\s*:\s*([\d.]+)',
            html_content
        )
        if dimension_match:
            width = dimension_match.group(1)
            length = dimension_match.group(2)
            height = dimension_match.group(3)
            weight = dimension_match.group(4)

            # Build dimensions string
            if width and length and height:
                product.dimensions = f"{width} x {length} x {height} cm"

            # Store weight
            if weight and not product.volume:
                product.volume = f"{weight} kg"

        # Extract model from specifications
        model_match = re.search(r'\\?"productModel\\?"\s*:\s*\\?"([^"\\]+)\\?"', html_content)
        if model_match and not product.model:
            product.model = model_match.group(1)

        # 9. Extract images if not found
        if not product.images:
            product.images = self._extract_images(html_content)

        product.retailer = "DoHome"
        return product

    def _extract_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON-LD data from HTML."""
        try:
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.finditer(pattern, html_content, re.DOTALL)

            for match in matches:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return data
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return None


class GlobalHouseExtractor(ProductExtractor):
    """Specialized extractor for Global House website."""

    def _extract_next_data(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract __NEXT_DATA__ from Next.js pages."""
        try:
            match = re.search(r'__NEXT_DATA__[^>]*type="application/json">(.+?)</script>', html_content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except (json.JSONDecodeError, Exception):
            pass
        return None

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Global House."""
        product = ProductData(url=url)

        # 1. Try __NEXT_DATA__ extraction first (Next.js specific)
        next_data = self._extract_next_data(html_content)
        if next_data:
            ast_data = next_data.get('props', {}).get('pageProps', {}).get('ast', {}).get('data', {})
            if ast_data:
                # Extract from attributes
                attrs = ast_data.get('attributes', [])
                width_val = depth_val = height_val = None
                for attr in attrs:
                    title = attr.get('title', '')
                    detail = attr.get('detail', '')
                    if title == 'รุ่น' and detail:
                        product.model = detail
                    elif 'กว้าง' in title and detail:
                        width = re.search(r'([\d.]+)', detail)
                        if width:
                            width_val = width.group(1)
                    elif 'ยาว' in title and detail:
                        depth = re.search(r'([\d.]+)', detail)
                        if depth:
                            depth_val = depth.group(1)
                    elif 'สูง' in title and detail:
                        height = re.search(r'([\d.]+)', detail)
                        if height:
                            height_val = height.group(1)

                # Build dimensions from extracted values
                dims = [d for d in [width_val, depth_val, height_val] if d]
                if dims:
                    product.dimensions = ' x '.join(dims) + ' cm'

                # Get description from htmlContent
                html_contents = ast_data.get('htmlContent', [])
                for hc in html_contents:
                    if hc.get('title') == 'คุณสมบัติเด่น' and hc.get('detail'):
                        # Strip HTML tags
                        desc = re.sub(r'<[^>]+>', ' ', hc.get('detail', ''))
                        desc = re.sub(r'\s+', ' ', desc).strip()
                        if desc and len(desc) > 10:
                            product.description = desc[:500]  # Limit length
                            break

        # 2. Try JSON-LD extraction
        json_ld_data = self._extract_json_ld(html_content)

        if json_ld_data:
            if not product.name:
                product.name = json_ld_data.get('name')
            if not product.description:
                product.description = json_ld_data.get('description')

            brand_value = json_ld_data.get('brand')
            if brand_value:
                if isinstance(brand_value, dict):
                    brand_value = brand_value.get('name')
                if brand_value:
                    product.brand = self._sanitize_brand_field(str(brand_value))

            sku_value = json_ld_data.get('sku')
            if sku_value:
                product.sku = self._sanitize_sku_field(str(sku_value))

            offers = json_ld_data.get('offers', {})
            if isinstance(offers, dict):
                price = offers.get('price')
                if price:
                    try:
                        product.current_price = float(price)
                    except (ValueError, TypeError):
                        pass

            image = json_ld_data.get('image')
            if image:
                if isinstance(image, list):
                    product.images = image
                elif isinstance(image, str):
                    product.images = [image]

        # 2. Extract product name from Global House specific patterns
        if not product.name:
            name_patterns = [
                r'<h1[^>]*class="[^"]*product[^"]*title[^"]*"[^>]*>(.*?)</h1>',
                r'<h1[^>]*class="[^"]*pdp-title[^"]*"[^>]*>(.*?)</h1>',
                r'<div[^>]*class="[^"]*product-title[^"]*"[^>]*>(.*?)</div>',
                r'<h1[^>]*>(.*?)</h1>',
            ]
            for pattern in name_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    name = self._clean_text(match.group(1))
                    if name and len(name) > 3 and 'global house' not in name.lower():
                        product.name = name
                        break

        # 3. Extract price from Global House specific patterns
        if not product.current_price:
            price_patterns = [
                # GlobalHouse 2024 patterns - sale price in red text-3xl
                r'<span[^>]*class="[^"]*text-3xl[^"]*text-red[^"]*"[^>]*>฿?([\d,]+)</span>',
                r'<span[^>]*class="[^"]*text-red[^"]*text-3xl[^"]*"[^>]*>฿?([\d,]+)</span>',
                # Font-bold price pattern
                r'<span[^>]*class="[^"]*font-bold[^"]*text-3xl[^"]*"[^>]*>฿?([\d,]+)</span>',
                # Generic large price display
                r'<span[^>]*class="[^"]*text-(?:2|3)xl[^"]*"[^>]*>฿?([\d,]+)</span>',
                # Legacy patterns
                r'<span[^>]*class="[^"]*price[^"]*final[^"]*"[^>]*>(.*?)</span>',
                r'<span[^>]*class="[^"]*selling-price[^"]*"[^>]*>(.*?)</span>',
                r'<div[^>]*class="[^"]*product-price[^"]*"[^>]*>.*?([฿\d,\.]+).*?</div>',
                r'ราคา[:\s]*([฿]?[\d,]+\.?\d*)',
            ]
            for pattern in price_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    price_text = self._clean_text(match.group(1))
                    price = PriceParser.parse_price(price_text)
                    if price and price > 0:
                        product.current_price = price
                        break

        # 4. Extract original price
        if not product.original_price:
            orig_patterns = [
                # GlobalHouse 2024 pattern - line-through for original price
                r'<span[^>]*class="[^"]*line-through[^"]*"[^>]*>฿?([\d,]+)</span>',
                # Thai word for original price
                r'ราคาเดิม.*?฿?([\d,]+)',
                # Legacy patterns
                r'<span[^>]*class="[^"]*price[^"]*original[^"]*"[^>]*>(.*?)</span>',
                r'<span[^>]*class="[^"]*was-price[^"]*"[^>]*>(.*?)</span>',
                r'<del[^>]*>(.*?)</del>',
                r'ราคาปกติ[:\s]*([฿]?[\d,]+\.?\d*)',
            ]
            for pattern in orig_patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    price_text = self._clean_text(match.group(1))
                    price = PriceParser.parse_price(price_text)
                    if price and price > 0:
                        product.original_price = price
                        break

        # 5. Extract SKU from URL pattern: /product/BRAND-NAME-i.SKU
        if url and not product.sku:
            # Global House URL pattern: /product/MAZUMA-...-i.8852163012022
            sku_match = re.search(r'-i\.(\d+)(?:\?|$)', url)
            if sku_match:
                potential_sku = sku_match.group(1)
                if self._is_valid_sku(potential_sku):
                    product.sku = potential_sku

        # 6. Extract brand from HTML or product name if not found
        if not product.brand:
            # Try HTML patterns first
            brand_patterns = [
                r'<span[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</span>',
                r'<a[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</a>',
                r'ยี่ห้อ[:\s]*([^\n<]+)',
                r'แบรนด์[:\s]*([^\n<]+)',
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    brand = self._clean_text(match.group(1))
                    if brand:
                        product.brand = self._sanitize_brand_field(brand)
                        break

            # Try extracting from URL (first word is usually brand)
            if not product.brand and url:
                url_brand_match = re.search(r'/product/([A-Za-z0-9]+)-', url)
                if url_brand_match:
                    potential_brand = url_brand_match.group(1)
                    if len(potential_brand) >= 2:
                        product.brand = potential_brand

        # 7. Extract category from breadcrumb (GlobalHouse specific)
        # Look for the last breadcrumb-link before the product title
        breadcrumb_matches = re.findall(r'<a[^>]*data-slot="breadcrumb-link"[^>]*title="([^"]+)"', html_content)
        if breadcrumb_matches:
            # Get the last category (most specific), but not if it's the home or generic pages
            for cat in reversed(breadcrumb_matches):
                if cat and cat not in ['หน้าแรก', 'หมวดหมู่', 'สินค้า'] and len(cat) > 2:
                    product.category = cat
                    break

        # 8. Extract color from product name (สีขาว, สีดำ, etc.)
        if not product.color and product.name:
            color_match = re.search(r'สี(\S+)', product.name)
            if color_match:
                product.color = 'สี' + color_match.group(1)

        # 9. Extract images from Next.js image srcset
        if not product.images:
            # Look for image URLs from the image-gbh.com CDN
            img_matches = re.findall(r'https://www\.image-gbh\.com/uploads/[^"&\s]+\.(?:jpg|jpeg|png)', html_content)
            if img_matches:
                # Remove duplicates and limit
                seen = set()
                unique_images = []
                for img in img_matches:
                    if img not in seen:
                        seen.add(img)
                        unique_images.append(img)
                        if len(unique_images) >= 10:
                            break
                product.images = unique_images

        # 10. Don't use base class volume/dimensions extraction - it gives garbage for GlobalHouse
        # GlobalHouse product specs are loaded dynamically via JavaScript
        # Clear any incorrectly extracted values
        if product.volume and len(str(product.volume)) < 3:
            product.volume = None
        if product.dimensions and len(str(product.dimensions)) < 5:
            product.dimensions = None

        product.retailer = "Global House"
        return product

    def _extract_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON-LD data from HTML."""
        try:
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.finditer(pattern, html_content, re.DOTALL)

            for match in matches:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return data
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return None


def get_extractor(url: str) -> ProductExtractor:
    """Get the appropriate extractor for the given URL."""
    domain = urlparse(url).netloc.lower()

    if 'thaiwatsadu.com' in domain:
        return ThaiWatsaduExtractor(url)
    elif 'homepro.co.th' in domain:
        return HomeProExtractor(url)
    elif 'boonthavorn.com' in domain:
        return BoonthavornExtractor(url)
    elif 'dohome.co.th' in domain:
        return DoHomeExtractor(url)
    elif 'megahome.co.th' in domain:
        return MegaHomeExtractor(url)
    elif 'globalhouse.co.th' in domain:
        return GlobalHouseExtractor(url)
    else:
        return ProductExtractor(url)

