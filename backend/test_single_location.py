"""
Test script to scrape a single GlobalHouse product with location selection
"""
import sys
import os
import asyncio

# Add the scraper directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper-url', 'adws'))

from adw_modules.product_extractor import ProductDataExtractor

async def test_single_location():
    """Test scraping a single product with location selection"""

    # Test product from database
    test_url = "https://globalhouse.co.th/product/PROTX-%E0%B8%A1%E0%B8%B8%E0%B9%89%E0%B8%87%E0%B8%A5%E0%B8%A7%E0%B8%94%E0%B8%AD%E0%B8%B0%E0%B8%A5%E0%B8%B9%E0%B8%A1%E0%B8%B4%E0%B9%80%E0%B8%99%E0%B8%B5%E0%B8%A2%E0%B8%A1-42-%E0%B8%99%E0%B8%B4%E0%B9%89%E0%B8%A7-x-10%E0%B9%80%E0%B8%A1%E0%B8%95%E0%B8%A3-Dia-0.21mm-18x16%E0%B8%95%E0%B8%A3.%E0%B8%99%E0%B8%B4%E0%B9%89%E0%B8%A7-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-4TCS0034210AL-i.5922007040610"
    test_location = "นครปฐม"  # Nakhon Pathom

    print("=" * 80)
    print("Testing GlobalHouse Location Selection")
    print("=" * 80)
    print(f"Product: PROTX มุ้งลวดอะลูมิเนียม")
    print(f"SKU: 5922007040610")
    print(f"Location: {test_location}")
    print(f"URL: {test_url[:100]}...")
    print()

    # Initialize extractor
    extractor = ProductDataExtractor()

    try:
        print("[1/3] Extracting product data with location selection...")
        product_data = await extractor.extract_product_data(
            url=test_url,
            gbh_location=test_location
        )

        if product_data:
            print("\n✅ SUCCESS! Product data extracted:")
            print("=" * 80)
            print(f"Name: {product_data.get('name', 'N/A')}")
            print(f"SKU: {product_data.get('sku', 'N/A')}")
            print(f"Brand: {product_data.get('brand', 'N/A')}")
            print(f"Price: {product_data.get('price', 'N/A')} THB")
            print(f"Original Price: {product_data.get('original_price', 'N/A')} THB")
            print(f"In Stock: {product_data.get('in_stock', 'Unknown')}")
            print(f"Category: {product_data.get('category', 'N/A')}")
            print(f"Images: {len(product_data.get('images', []))} images")
            print("=" * 80)

            # Show first image URL
            if product_data.get('images'):
                print(f"\nFirst image: {product_data['images'][0][:100]}...")

            print("\n✅ Test PASSED - Location selection worked!")
            return True
        else:
            print("\n❌ FAILED - No product data extracted")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set console encoding to UTF-8 for Thai characters
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    success = asyncio.run(test_single_location())
    sys.exit(0 if success else 1)
