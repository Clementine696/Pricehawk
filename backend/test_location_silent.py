"""Test GlobalHouse location scraping with stderr suppression to avoid Unicode errors"""
import sys
import os
import io
import asyncio

# Suppress stderr to avoid Unicode encoding errors from crawl4ai
class SilentStderr:
    def write(self, text):
        # Silently ignore all stderr output to prevent Unicode errors
        pass

    def flush(self):
        pass

# Replace stderr before importing crawl4ai
original_stderr = sys.stderr
sys.stderr = SilentStderr()

# Add scraper to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper-url', 'adws'))

from adw_modules.crawl4ai_wrapper import Crawl4AIWrapper

async def test_location_scraping():
    """Test location-based scraping for GlobalHouse"""

    test_url = "https://globalhouse.co.th/product/HUMMER-%E0%B9%80%E0%B8%81%E0%B8%A5%E0%B8%B5%E0%B8%A2%E0%B8%A7%E0%B9%80%E0%B8%A3%E0%B9%88%E0%B8%87-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-TM10-%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94-38-i.2422005400599"
    test_location = "เทพ"

    print("=" * 80)
    print("Testing GlobalHouse Location Scraping")
    print("=" * 80)
    print(f"URL: {test_url[:80]}...")
    print(f"Location: {test_location}")
    print()

    wrapper = Crawl4AIWrapper()

    try:
        print("[1/3] Initializing browser...")
        await wrapper.initialize()

        print(f"[2/3] Scraping with location '{test_location}'...")
        # Wait for location selection JavaScript to complete
        wait_for = "() => document.body.innerText.includes('SUCCESS: Location selection complete') || document.body.innerText.includes('[LOCATION ERROR]')"

        result = await wrapper.scrape_url(
            url=test_url,
            wait_for=wait_for,
            gbh_location=test_location
        )

        print(f"[3/3] Processing results...")
        print()

        if result.success and result.html:
            print(f"✅ Scraping successful!")
            print(f"HTML length: {len(result.html)} characters")
            print()

            # Check for location selection logs in HTML
            if '[LOCATION]' in result.html:
                print("📍 Location selection logs found in HTML:")
                import re
                log_lines = re.findall(r'\[LOCATION[^\]]*\][^\<]*', result.html)
                for line in log_lines[:20]:  # Show first 20 log lines
                    print(f"  {line}")
                print()

            # Save HTML for inspection
            output_file = "debug_location_html.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.html)
            print(f"📄 HTML saved to: {output_file}")
            print()

            # Check for price - try multiple patterns
            import re
            price_patterns = [
                r'<span[^>]*class="[^"]*text-3xl[^"]*text-red[^"]*"[^>]*>฿?([\d,]+)</span>',
                r'<span[^>]*class="[^"]*text-red[^"]*text-3xl[^"]*"[^>]*>฿?([\d,]+)</span>',
                r'<span[^>]*class="[^"]*font-bold[^"]*text-3xl[^"]*"[^>]*>฿?([\d,]+)</span>',
                r'<span[^>]*class="[^"]*text-3xl[^"]*"[^>]*>฿?([\d,]+)</span>',
                r'฿([\d,]+)',
            ]
            price_found = False
            for pattern in price_patterns:
                match = re.search(pattern, result.html)
                if match:
                    price = match.group(1)
                    print(f"💰 Price found: ฿{price} (pattern: {pattern[:50]}...)")
                    price_found = True
                    break

            if not price_found:
                print("⚠️ Price not found in HTML with any pattern")

        else:
            print(f"❌ Scraping failed!")
            print(f"Error: {result.error_message}")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await wrapper.close()

if __name__ == "__main__":
    # Set console encoding for Thai characters
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    asyncio.run(test_location_scraping())
