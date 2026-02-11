"""
Test script for GlobalHouse location-based price scraping
"""
import os
import sys
import asyncio
import io

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add scraper module to path
scraper_path = os.path.join(os.path.dirname(__file__), 'scraper-url', 'adws')
sys.path.insert(0, scraper_path)

from adw_modules.crawl4ai_wrapper import Crawl4AIWrapper, ScrapingConfig
from adw_modules.product_extractor import get_extractor

async def test_location_scraping():
    """Test scraping a GlobalHouse product with location selection"""

    # Test product URL
    url = "https://www.globalhouse.co.th/product/กลอนดิจิตอล-C.HITECH-ล็อกนิ้วโคลด์-รุ่น-CK-5-พร้อมดีดตั้ง-1.GP660907-000010"

    # Test with different locations
    locations = [
        "นครปฐม",  # Nakhon Pathom
        "ขอนแก่น",  # Khon Kaen
    ]

    # Create scraper config
    config = ScrapingConfig(
        timeout=60,
        headless=True,
        verbose=True
    )

    print("=" * 60)
    print("Testing GlobalHouse Location-Based Price Scraping")
    print("=" * 60)
    print(f"Product URL: {url[:80]}...")
    print()

    async with Crawl4AIWrapper(config) as wrapper:
        for location in locations:
            print(f"\n📍 Testing Location: {location}")
            print("-" * 60)

            try:
                # Scrape with location
                result = await wrapper.scrape_url(
                    url,
                    wait_for="() => document.readyState === 'complete' && document.body && document.body.innerText.length > 500",
                    gbh_location=location
                )

                if result.success and result.html:
                    print(f"✓ Scrape successful! HTML length: {len(result.html)}")

                    # Save HTML for debugging
                    debug_file = f"debug_{location.replace(' ', '_')}.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(result.html)
                    print(f"  Debug HTML saved to: {debug_file}")

                    # Check if location modal is still open
                    if 'ตรวจสอบสาขา' in result.html or 'เลือกช้อปที่สาขานี้' in result.html:
                        print("  ⚠️  Warning: Location modal might still be open")

                    # Extract product data
                    extractor = get_extractor(url)
                    product = extractor.extract_from_html(result.html, url)

                    if product:
                        print(f"✓ Product extracted successfully!")
                        print(f"  Name: {product.name}")
                        print(f"  SKU: {product.sku}")
                        print(f"  Current Price: ฿{product.current_price}" if product.current_price else "  Price: N/A")
                        print(f"  Original Price: ฿{product.original_price}" if product.original_price else "")
                    else:
                        print("✗ Failed to extract product data")
                else:
                    print(f"✗ Scrape failed: {result.error_message}")

            except Exception as e:
                print(f"✗ Error: {e}")

            print()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_location_scraping())
