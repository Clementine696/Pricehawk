#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Pattern Tracking for All Retailers

Tests if extraction_metadata['price_pattern'] is properly populated
for all 6 retailers.
"""

import sys
import os
import asyncio

# Fix Windows console encoding for emoji/unicode
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'backslashreplace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'backslashreplace')

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'scraper-url'))

from adws.adw_modules.product_extractor import (
    ThaiWatsaduExtractor,
    HomeProExtractor,
    MegaHomeExtractor,
    BoonthavornExtractor,
    DoHomeExtractor,
    GlobalHouseExtractor
)
from adws.adw_modules.crawl4ai_wrapper import (
    Crawl4AIWrapper,
    create_simple_config,
)


# Test URLs from pattern.txt
TEST_URLS = {
    'TWD': {
        'Base': 'https://www.thaiwatsadu.com/th/sku/60272160',
        'Pack_1': 'https://www.thaiwatsadu.com/th/sku/60178098',
        'Pack_2': 'https://thaiwatsadu.com/th/sku/60221854',
        'Coupon': 'https://thaiwatsadu.com/th/sku/60405778',
    },
    'HP': {
        'Base': 'https://www.homepro.co.th/p/202830',
        'Pack': 'https://www.homepro.co.th/p/275187',
    },
    'MGH': {
        'Base': 'https://www.megahome.co.th/p/202830',
        'Pack': 'https://www.megahome.co.th/p/1200351',
    },
    'BTV': {
        'Base': 'https://www.boonthavorn.com/hafele-1016246',
    },
    'GBH': {
        'Base': 'https://globalhouse.co.th/product/NEOBOND-%E0%B8%8B%E0%B8%B4%E0%B8%A5%E0%B8%B4%E0%B9%82%E0%B8%84%E0%B8%99%E0%B9%81%E0%B8%AB%E0%B9%89%E0%B8%87%E0%B9%80%E0%B8%A3%E0%B9%87%E0%B8%A7-Neobond-Fast-300-ml.-%E0%B8%AA%E0%B8%B5%E0%B8%82%E0%B8%B2%E0%B8%A7-i.8852863000695',
    },
    'DH': {
        'Base': 'https://www.dohome.co.th/th/yale-door-bolt-4-inch-ba90704snp2-2-10128149.html',
    }
}

# Extractor mapping
EXTRACTORS = {
    'TWD': ThaiWatsaduExtractor,
    'HP': HomeProExtractor,
    'MGH': MegaHomeExtractor,
    'BTV': BoonthavornExtractor,
    'GBH': GlobalHouseExtractor,
    'DH': DoHomeExtractor,
}


async def test_url(retailer_id: str, test_name: str, url: str, wrapper: Crawl4AIWrapper):
    """Test a single URL and print pattern tracking results"""
    print(f"\n{'='*80}")
    print(f"Testing: {retailer_id} - {test_name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    try:
        # Scrape HTML
        print("Scraping HTML...", end=" ", flush=True)
        result = await wrapper.scrape_url(url)
        
        if not result or not result.html or len(result.html) < 1000:
            print("[FAIL] - HTML too short or empty")
            return False
        
        html = result.html
        print(f"[OK] ({len(html):,} chars)")
        
        # Extract product data
        print("Extracting product data...", end=" ", flush=True)
        extractor_class = EXTRACTORS[retailer_id]
        extractor = extractor_class(url)
        product = extractor.extract_from_html(html, url)
        
        if not product:
            print("[FAIL] - No product data extracted")
            return False
        
        print("[OK]")
        
        # Check results
        print(f"\nResults:")
        print(f"  Name: {product.name[:60] if product.name else 'N/A'}...")
        print(f"  SKU: {product.sku or 'N/A'}")
        print(f"  Price: B{product.current_price:,.2f}" if product.current_price else "  Price: N/A")
        print(f"  Original Price: B{product.original_price:,.2f}" if product.original_price else "  Original Price: N/A")
        
        # THE KEY TEST: Check extraction_metadata
        print(f"\nPattern Tracking:")
        if hasattr(product, 'extraction_metadata') and product.extraction_metadata:
            price_pattern = product.extraction_metadata.get('price_pattern')
            if price_pattern:
                print(f"  [PASS] price_pattern: {price_pattern}")
                return True
            else:
                print(f"  [WARN] extraction_metadata exists but price_pattern is empty")
                print(f"      metadata keys: {list(product.extraction_metadata.keys())}")
                return False
        else:
            print(f"  [FAIL] extraction_metadata NOT FOUND or empty")
            return False
            
    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_tests():
    """Run all tests"""
    print("="*80)
    print("PATTERN TRACKING TEST")
    print("Testing extraction_metadata['price_pattern'] for all retailers")
    print("="*80)
    
    # Create scraping configuration
    config = create_simple_config(
        max_concurrent=1,  # Sequential for reliability
        delay_between_requests=2.0,
        timeout=60,
        headless=True,
        verbose=False,
        retry_attempts=2,
        retry_delay=5.0,
        use_browser=True,
    )
    
    results = {}
    total_tests = 0
    passed_tests = 0
    
    async with Crawl4AIWrapper(config) as wrapper:
        for retailer_id, urls in TEST_URLS.items():
            results[retailer_id] = {}
            for test_name, url in urls.items():
                total_tests += 1
                success = await test_url(retailer_id, test_name, url, wrapper)
                results[retailer_id][test_name] = success
                if success:
                    passed_tests += 1
                
                # Small delay between tests
                await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for retailer_id, tests in results.items():
        passed = sum(1 for v in tests.values() if v)
        total = len(tests)
        status = "[PASS]" if passed == total else "[WARN]" if passed > 0 else "[FAIL]"
        print(f"{status} {retailer_id}: {passed}/{total} tests passed")
        
        for test_name, success in tests.items():
            icon = "  +" if success else "  -"
            print(f"  {icon} {test_name}")
    
    print(f"\n{'='*80}")
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("ALL TESTS PASSED!")
        return 0
    elif passed_tests > 0:
        print("SOME TESTS FAILED")
        return 1
    else:
        print("ALL TESTS FAILED")
        return 2


def main():
    """Entry point"""
    return asyncio.run(run_tests())


if __name__ == '__main__':
    sys.exit(main())
