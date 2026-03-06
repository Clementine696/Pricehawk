#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for GlobalHouse pattern tracking
"""

import sys
import os
import asyncio

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'backslashreplace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'backslashreplace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'scraper-url'))

from adws.adw_modules.product_extractor import GlobalHouseExtractor
from adws.adw_modules.crawl4ai_wrapper import Crawl4AIWrapper, create_simple_config


async def test_gbh():
    """Test GlobalHouse pattern tracking"""
    url = 'https://globalhouse.co.th/product/NEOBOND-%E0%B8%8B%E0%B8%B4%E0%B8%A5%E0%B8%B4%E0%B9%82%E0%B8%84%E0%B8%99%E0%B9%81%E0%B8%AB%E0%B9%89%E0%B8%87%E0%B9%80%E0%B8%A3%E0%B9%87%E0%B8%A7-Neobond-Fast-300-ml.-%E0%B8%AA%E0%B8%B5%E0%B8%82%E0%B8%B2%E0%B8%A7-i.8852863000695'
    
    print("="*80)
    print("GLOBALHOUSE PATTERN TRACKING TEST")
    print("="*80)
    print(f"\nURL: {url[:80]}...")
    
    config = create_simple_config(
        max_concurrent=1,
        delay_between_requests=2.0,
        timeout=60,
        headless=True,
        verbose=False,
        retry_attempts=2,
        retry_delay=5.0,
        use_browser=True,
    )
    
    async with Crawl4AIWrapper(config) as wrapper:
        print("\n[1/3] Scraping HTML...", end=" ", flush=True)
        result = await wrapper.scrape_url(url)
        
        if not result or not result.html or len(result.html) < 1000:
            print("[FAIL]")
            return False
        
        print(f"[OK] ({len(result.html):,} chars)")
        
        print("[2/3] Extracting product data...", end=" ", flush=True)
        extractor = GlobalHouseExtractor(url)
        product = extractor.extract_from_html(result.html, url)
        
        if not product:
            print("[FAIL]")
            return False
        
        print("[OK]")
        
        print("[3/3] Checking pattern tracking...", end=" ", flush=True)
        
        if not hasattr(product, 'extraction_metadata') or not product.extraction_metadata:
            print("[FAIL] - No extraction_metadata")
            return False
        
        pattern = product.extraction_metadata.get('price_pattern')
        if not pattern:
            print("[FAIL] - No price_pattern in metadata")
            print(f"      Available keys: {list(product.extraction_metadata.keys())}")
            return False
        
        print("[OK]")
        
        # Show results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"Name: {product.name}")
        print(f"SKU: {product.sku}")
        print(f"Price: {product.current_price} THB")
        print(f"Pattern: {pattern}")
        print("\n[PASS] GlobalHouse pattern tracking is working correctly!")
        print("="*80)
        
        return True


if __name__ == '__main__':
    result = asyncio.run(test_gbh())
    sys.exit(0 if result else 1)
