"""Test GlobalHouse location scraping with detailed step-by-step logging"""
import sys
import os
import asyncio

# Suppress stderr to avoid Unicode encoding errors from crawl4ai
class SilentStderr:
    def write(self, text):
        pass
    def flush(self):
        pass

original_stderr = sys.stderr
sys.stderr = SilentStderr()

# Add scraper to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper-url', 'adws'))

from adw_modules.crawl4ai_wrapper import Crawl4AIWrapper

async def test_location_with_state_logging():
    """Test location-based scraping with detailed state information"""

    test_url = "https://globalhouse.co.th/product/HUMMER-%E0%B9%80%E0%B8%81%E0%B8%A5%E0%B8%B5%E0%B8%A2%E0%B8%A7%E0%B9%80%E0%B8%A3%E0%B9%88%E0%B8%87-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-TM10-%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94-38-i.2422005400599"
    test_location = "เทพ"

    print("=" * 80)
    print("GlobalHouse Location Selection - Detailed State Logging")
    print("=" * 80)
    print(f"URL: {test_url[:80]}...")
    print(f"Location: {test_location}")
    print()

    wrapper = Crawl4AIWrapper()

    try:
        print("STATE 1: Initializing browser...")
        print("-" * 80)
        await wrapper.initialize()
        print("✓ Browser initialized")
        print()

        print("STATE 2: Starting scrape with location selection JavaScript...")
        print("-" * 80)
        wait_for = "() => document.body.innerText.includes('SUCCESS: Location selection complete') || document.body.innerText.includes('[LOCATION ERROR]')"

        print(f"  - Target location: {test_location}")
        print(f"  - Wait condition: SUCCESS or ERROR message")
        print(f"  - Timeout: 180 seconds")
        print()

        result = await wrapper.scrape_url(
            url=test_url,
            wait_for=wait_for,
            gbh_location=test_location
        )

        print("STATE 3: Scraping complete, analyzing results...")
        print("-" * 80)

        if not result.success:
            print(f"✗ Scraping failed: {result.error_message}")
            return False

        print(f"✓ HTML received: {len(result.html)} characters")
        print()

        # Extract and display all location logs
        print("STATE 4: Location selection process logs...")
        print("-" * 80)

        import re
        log_lines = re.findall(r'\[LOCATION[^\]]*\][^\<]*', result.html)

        if not log_lines:
            print("✗ No location logs found in HTML!")
            return False

        for i, line in enumerate(log_lines, 1):
            # Color code based on log type
            if '[LOCATION ERROR]' in line:
                print(f"  {i}. 🔴 {line}")
            elif 'SUCCESS' in line:
                print(f"  {i}. 🟢 {line}")
            elif 'Step' in line:
                print(f"  {i}. 🔵 {line}")
            else:
                print(f"  {i}. ⚪ {line}")
        print()

        # Check final state
        print("STATE 5: Checking final state...")
        print("-" * 80)

        if 'SUCCESS: Location selection complete' in result.html:
            print("✓ Location selection: SUCCESS")
        elif '[LOCATION ERROR]' in result.html:
            print("✗ Location selection: FAILED")
            # Find the error
            error_logs = [line for line in log_lines if '[LOCATION ERROR]' in line]
            if error_logs:
                print(f"  Error: {error_logs[-1]}")
            return False
        else:
            print("? Location selection: UNKNOWN (no success/error marker)")
            return False
        print()

        # Extract price
        print("STATE 6: Extracting price from HTML...")
        print("-" * 80)

        price_patterns = [
            (r'฿\s*([\d,]+)', 'Baht symbol + number'),
            (r'<span[^>]*class="[^"]*text-3xl[^"]*"[^>]*>฿?([\d,]+)</span>', 'text-3xl span'),
        ]

        price_found = False
        for pattern, desc in price_patterns:
            match = re.search(pattern, result.html)
            if match:
                price = match.group(1)
                print(f"✓ Price found: ฿{price}")
                print(f"  Pattern: {desc}")
                price_found = True
                break

        if not price_found:
            print("✗ Price not found in HTML")
            return False
        print()

        print("STATE 7: Final verification...")
        print("-" * 80)
        print("✓ All states completed successfully!")
        print(f"✓ Final price for location '{test_location}': ฿{price}")
        print()

        # Save HTML for inspection
        output_file = f"debug_location_{test_location}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.html)
        print(f"📄 Full HTML saved to: {output_file}")

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print(f"✗ EXCEPTION at current state")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await wrapper.close()

if __name__ == "__main__":
    # Set console encoding for Thai characters
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    success = asyncio.run(test_location_with_state_logging())

    print()
    print("=" * 80)
    if success:
        print("🎉 TEST PASSED - All states completed successfully")
    else:
        print("❌ TEST FAILED - See logs above for details")
    print("=" * 80)

    sys.exit(0 if success else 1)
