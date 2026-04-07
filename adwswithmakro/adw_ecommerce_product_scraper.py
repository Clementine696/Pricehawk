#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pydantic",
#   "python-dotenv",
#   "click",
#   "rich",
#   "crawl4ai",
# ]
# ///
"""
E-commerce Product Data Scraper

This AI Developer Workflow (ADW) script extracts structured product data from e-commerce websites
and outputs it in the specified JSON format with comprehensive product fields including pricing,
discount calculations, and physical attributes.

Usage:
    # Single product URL scraping
    ./adws/adw_ecommerce_product_scraper.py --url https://www.thaiwatsadu.com/th/sku/60363373

    # Batch scraping from file
    ./adws/adw_ecommerce_product_scraper.py --urls-file products.txt --output-file products.json

    # With custom configuration
    ./adws/adw_ecommerce_product_scraper.py --url https://example.com/product --max-concurrent 5 --delay 2.0

    # Test mode for validation
    ./adws/adw_ecommerce_product_scraper.py --url https://example.com/product --test
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.progress import Progress, TaskID, BarColumn, TextColumn

# Fix Windows encoding issues
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Force Rich to use ANSI mode (not legacy Win32 console) so Unicode chars don't crash
    os.environ['TERM'] = 'xterm-256color'
    os.environ['COLORTERM'] = 'truecolor'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Add the parent directory to the path so we can import adw_modules as a package
sys.path.insert(0, os.path.dirname(__file__))

from adw_modules.crawl4ai_wrapper import (
    Crawl4AIWrapper,
    ScrapingConfig,
    ScrapingResult,
    create_simple_config,
)
from adw_modules.product_extractor import get_extractor
from adw_modules.product_schemas import ProductData, validate_product_data

def print_status_panel(
    console,
    action: str,
    adw_id: str,
    phase: str = None,
    status: str = "info",
    url: str = None
):
    """Print a status panel with timestamp and context."""
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Choose color based on status
    if status == "success":
        border_style = "green"
        icon = "✅"
    elif status == "error":
        border_style = "red"
        icon = "❌"
    elif status == "warning":
        border_style = "yellow"
        icon = "⚠️"
    else:
        border_style = "cyan"
        icon = "🔄"

    # Build title with context
    title_parts = [f"[{timestamp}]", adw_id[:6]]
    if phase:
        title_parts.append(phase)
    if url and len(url) > 30:
        title_parts.append(url[:30] + "...")
    elif url:
        title_parts.append(url)
    title = " | ".join(title_parts)

    content = f"{icon} {action}"

    console.print(
        Panel(
            content,
            title=f"[bold {border_style}]{title}[/bold {border_style}]",
            border_style=border_style,
            padding=(0, 1),
        )
    )


def create_output_directory_structure(base_output_folder: str, adw_id: str, organization_type: str = "date") -> str:
    """Create organized output directory structure following ADW patterns.

    Args:
        base_output_folder: Base output folder path
        adw_id: ADW ID for tracking
        organization_type: How to organize subdirectories ("date" or "job-id")

    Returns:
        Path to the created output directory
    """
    try:
        # Validate base folder path
        base_path = Path(base_output_folder)

        # Create base directory if it doesn't exist
        base_path.mkdir(parents=True, exist_ok=True)

        # Check write permissions
        if not os.access(base_path, os.W_OK):
            raise click.ClickException(f"Base output folder is not writable: {base_output_folder}")

        # Create organized subdirectory
        if organization_type == "date":
            # Date-based organization: YYYY-MM-DD
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = base_path / date_str / adw_id
        else:
            # Job-ID based organization
            output_dir = base_path / adw_id

        # Create the full directory structure
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create standard subdirectories
        subdirs = ['raw', 'processed', 'logs', 'assets']
        for subdir in subdirs:
            (output_dir / subdir).mkdir(exist_ok=True)

        return str(output_dir)

    except Exception as e:
        raise click.ClickException(f"Failed to create output directory structure: {e}")


def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from a text file."""
    try:
        if not os.path.exists(file_path):
            raise click.ClickException(f"File not found: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise click.ClickException(f"File not readable: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            urls = []
            line_num = 0
            # Check if file is CSV
            is_csv = file_path.lower().endswith('.csv')
            
            for line in f:
                line_num += 1
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                # Handle CSV format
                if is_csv:
                    # Skip header row if it contains 'url' or 'link'
                    if line_num == 1 and ('url' in line.lower() or 'link' in line.lower()):
                        continue
                        
                    # Split by comma and take the last part as URL (assuming format: name,url)
                    parts = line.split(',')
                    if len(parts) > 1:
                        url = parts[-1].strip()
                    else:
                        url = line
                else:
                    url = line

                if url:
                    if not (url.startswith('http://') or url.startswith('https://')):
                        # Only raise error if it's not a CSV header we missed
                        if not (is_csv and line_num == 1):
                            raise click.ClickException(f"Invalid URL at line {line_num} in {file_path}: {url}")
                        continue
                    urls.append(url)
        return urls
    except UnicodeDecodeError:
        raise click.ClickException(f"File encoding error in {file_path}. Please use UTF-8 encoding.")
    except Exception as e:
        raise click.ClickException(f"Failed to load URLs from {file_path}: {e}")


async def extract_product_data(url: str, wrapper: Crawl4AIWrapper, adw_id: str, console: Console, config: ScrapingConfig = None) -> Optional[ProductData]:
    """Extract product data from a single URL."""
    try:
        # Determine specific wait conditions per retailer
        css_selector = None
        wait_for = None

        if 'boonthavorn.com' in url:
            # Boonthavorn is React SPA - wait for actual price content (not shimmer placeholders)
            # Must wait for price element AND no shimmer loading indicators
            wait_for = "() => { const hasPrice = document.body.innerText.includes('฿') || document.body.innerText.includes('บาท'); const noShimmer = !document.querySelector('[class*=\"shimmer\"]') || document.querySelectorAll('[class*=\"shimmer\"]').length < 3; return hasPrice && noShimmer; }"
        elif 'homepro.co.th' in url:
            # HomePro needs to wait for price element to load (React SPA)
            # Use AND: both price element AND ฿ symbol must be present
            wait_for = "() => document.querySelector('[class*=\"price\"]') !== null && document.body.innerText.includes('฿')"
        elif 'globalhouse.co.th' in url:
            # GlobalHouse: wait for price (฿) to appear — don't wait for readyState 'complete'
            # because some pages have variant/related-product sections that load forever (shimmer).
            # The price loads quickly via API; once ฿ appears the product data is ready.
            wait_for = "() => document.body.innerText.includes('฿')"
        elif 'hardwarehouse.co.th' in url:
            # Wait for the product detail heading — only present on product pages, not catalog/home
            wait_for = "() => document.querySelector('[class*=\"p-title-main\"]') !== null && document.body.innerText.includes('฿')"

        # SPECIAL CASE: Makro — use Playwright to set postal code 10200 then grab __NEXT_DATA__
        if 'makro.pro' in url:
            from adw_modules.crawl4ai_wrapper import ScrapingResult
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as _pw:
                    _browser = await _pw.chromium.launch(headless=True)
                    _ctx = await _browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='th-TH',
                    )
                    _page = await _ctx.new_page()
                    await _page.goto(url, wait_until='domcontentloaded', timeout=30000)

                    # Dismiss cookie consent dialog if present
                    try:
                        await _page.wait_for_selector('.MuiDialog-root', state='visible', timeout=8000)
                        print(f"[SCRAPER] Makro: cookie dialog visible, dismissing...", flush=True, file=sys.stderr)
                        # Click the accept/confirm button inside the dialog
                        _cookie_btn = _page.locator('.MuiDialog-root button').first
                        await _cookie_btn.click(timeout=5000)
                        await _page.wait_for_selector('.MuiDialog-root', state='hidden', timeout=10000)
                        print(f"[SCRAPER] Makro: cookie dialog dismissed", flush=True, file=sys.stderr)
                    except Exception as _ce:
                        print(f"[SCRAPER] Makro: no cookie dialog or already dismissed ({_ce})", flush=True, file=sys.stderr)

                    # Click the postal/branch button (.css-1qnhlef)
                    try:
                        await _page.wait_for_selector('.css-1qnhlef', state='visible', timeout=8000)
                        await _page.evaluate("document.querySelector('.css-1qnhlef').click()")
                        print(f"[SCRAPER] Makro: clicked postal button", flush=True, file=sys.stderr)
                        await _page.wait_for_timeout(1500)
                    except Exception as _pe:
                        print(f"[SCRAPER] Makro: postal button not found ({_pe})", flush=True, file=sys.stderr)

                    # Find postal input and set value to 10200
                    try:
                        # Wait for any input inside the postal dialog
                        await _page.wait_for_function(
                            "() => { const inp = document.querySelector('input[class*=\"r-141fyjm\"]') || document.querySelector('input[placeholder*=\"ไปรษณีย์\"]'); return inp !== null; }",
                            timeout=8000
                        )
                        await _page.wait_for_timeout(300)

                        # Focus the input and type using Playwright keyboard (triggers React key events)
                        _input_focused = await _page.evaluate("""() => {
                            const input = document.querySelector('input[class*="r-141fyjm"]') ||
                                          document.querySelector('input[placeholder*="ไปรษณีย์"]');
                            if (!input) return false;
                            // Clear existing value
                            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            nativeSetter.call(input, '');
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.focus();
                            return true;
                        }""")
                        print(f"[SCRAPER] Makro: focused postal input: {_input_focused}", flush=True, file=sys.stderr)

                        if _input_focused:
                            # Type each character — triggers keydown/keypress/keyup + React synthetic events
                            _postal_input = _page.locator('input[class*="r-141fyjm"]').first
                            await _postal_input.press_sequentially('10200', delay=80)
                            print(f"[SCRAPER] Makro: typed 10200 into postal input", flush=True, file=sys.stderr)
                            await _page.wait_for_timeout(2500)

                        # Click first dropdown result: the clickable ancestor div of span.css-1jxf684 containing '10200'
                        _clicked_result = await _page.evaluate("""() => {
                            // Find spans containing exactly '10200' (postal code results)
                            const spans = Array.from(document.querySelectorAll('span.css-1jxf684'));
                            const match = spans.find(s => s.textContent.trim() === '10200');
                            if (!match) return 'no span found';
                            // Walk up to the clickable ancestor (has r-1loqt21 cursor:pointer class)
                            let el = match;
                            for (let i = 0; i < 8; i++) {
                                if (!el) break;
                                if (el.className && el.className.includes('r-1loqt21')) {
                                    el.click();
                                    return 'clicked row: ' + el.textContent.trim().slice(0, 80);
                                }
                                el = el.parentElement;
                            }
                            // Fallback: click the span itself
                            match.click();
                            return 'clicked span: ' + match.textContent.trim();
                        }""")
                        print(f"[SCRAPER] Makro: dropdown result click: {_clicked_result}", flush=True, file=sys.stderr)
                        await _page.wait_for_timeout(1500)

                        # Reload page so __NEXT_DATA__ gets the location-specific price
                        if 'no ' not in _clicked_result:
                            await _page.reload(wait_until='domcontentloaded')
                            await _page.wait_for_timeout(3000)
                            print(f"[SCRAPER] Makro: reloaded page with new store location", flush=True, file=sys.stderr)

                    except Exception as _inp_err:
                        print(f"[SCRAPER] Makro: postal input interaction failed ({_inp_err})", flush=True, file=sys.stderr)

                    # Wait for __NEXT_DATA__ to be present then grab page HTML
                    try:
                        await _page.wait_for_function(
                            "() => { const s = document.getElementById('__NEXT_DATA__'); return s && s.textContent.includes('displayPrice'); }",
                            timeout=15000
                        )
                    except Exception:
                        pass

                    _html = await _page.content()
                    await _browser.close()

                result = ScrapingResult(url=url, success=True, html=_html, content=_html)
                print(f"[SCRAPER] Makro: Playwright OK, HTML={len(_html)} chars", flush=True, file=sys.stderr)
            except Exception as _makro_err:
                result = ScrapingResult(url=url, success=False, error_message=str(_makro_err))
                print(f"[SCRAPER] Makro: Playwright FAILED: {_makro_err}", flush=True, file=sys.stderr)

        # SPECIAL CASE: HardwareWarehouse — use plain requests (Playwright triggers anti-bot redirect)
        elif 'hardwarehouse.co.th' in url:
            import requests as _requests
            from adw_modules.crawl4ai_wrapper import ScrapingResult
            _hw_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
            }
            try:
                _resp = _requests.get(url, headers=_hw_headers, timeout=30)
                result = ScrapingResult(url=url, success=True, html=_resp.text, content=_resp.text)
                print(f"[SCRAPER] HardwareWarehouse: requests OK, HTML={len(_resp.text)} chars", flush=True, file=sys.stderr)
            except Exception as hw_err:
                result = ScrapingResult(url=url, success=False, error_message=str(hw_err))
                print(f"[SCRAPER] HardwareWarehouse: requests FAILED: {hw_err}", flush=True, file=sys.stderr)
        else:
            # Use shared wrapper for all other retailers
            result = await wrapper.scrape_url(url, css_selector=css_selector, wait_for=wait_for)

        # GlobalHouse: If Playwright timed out, fall back to requests (gets name/SKU/images, no price)
        if 'globalhouse.co.th' in url and (not result.success or not result.html or len(result.html) < 500):
            print(f"[SCRAPER] GlobalHouse: Playwright failed/timed out, falling back to requests...", flush=True, file=sys.stderr)
            import requests as _requests
            from adw_modules.crawl4ai_wrapper import ScrapingResult
            _gbh_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            try:
                _resp = _requests.get(url, headers=_gbh_headers, timeout=30)
                result = ScrapingResult(url=url, success=True, html=_resp.text, content=_resp.text)
                print(f"[SCRAPER] GlobalHouse fallback: requests OK, HTML={len(_resp.text)} chars (price may be missing)", flush=True, file=sys.stderr)
            except Exception as _gbh_err:
                print(f"[SCRAPER] GlobalHouse fallback: requests FAILED: {_gbh_err}", flush=True, file=sys.stderr)

        # HomePro: Retry once if we get empty page (execution context destroyed)
        if 'homepro.co.th' in url and result.success and result.html and len(result.html) < 100:
            print(f"[SCRAPER] WARNING: HomePro: Empty page detected ({len(result.html)} chars), retrying once...", flush=True, file=sys.stderr)
            print(f"[SCRAPER] This happens when page navigation destroys execution context during wait_for", flush=True, file=sys.stderr)

            import asyncio
            await asyncio.sleep(5)

            print(f"[SCRAPER] HomePro RETRY: Adding 25s initial delay...", flush=True, file=sys.stderr)
            await asyncio.sleep(25)
            print(f"[SCRAPER] HomePro RETRY: Now attempting scrape...", flush=True, file=sys.stderr)

            result = await wrapper.scrape_url(url, css_selector=css_selector, wait_for=wait_for)

            if result.success and result.html and len(result.html) > 100:
                print(f"[SCRAPER] Retry succeeded! HTML length: {len(result.html)}", flush=True, file=sys.stderr)
            else:
                print(f"[SCRAPER] Retry still failed. HTML length: {len(result.html) if result.html else 0}", flush=True, file=sys.stderr)

        # HomePro: Validate captured page state
        if 'homepro.co.th' in url and result.success and result.html:
            import re
            body_match = re.search(r'<body[^>]*>', result.html)
            if body_match:
                body_tag = body_match.group(0)
                print(f"[SCRAPER] HomePro: Captured page body tag: {body_tag}", flush=True, file=sys.stderr)
                if 'home-page' in body_tag:
                    print(f"[SCRAPER] WARNING: Page still in home-page state! This should not happen.", flush=True, file=sys.stderr)
                elif 'product-page' in body_tag or 'pdp-' in body_tag:
                    print(f"[SCRAPER] Page correctly in product-page state", flush=True, file=sys.stderr)
                else:
                    print(f"[SCRAPER] WARNING: UNKNOWN page state (not home-page or product-page)", flush=True, file=sys.stderr)

        print(f"[SCRAPER] Scrape result - Success: {result.success}", flush=True, file=sys.stderr)
        if result.success:
            print(f"[SCRAPER] HTML length: {len(result.html) if result.html else 0}", flush=True, file=sys.stderr)
            print(f"[SCRAPER] Content length: {len(result.content) if result.content else 0}", flush=True, file=sys.stderr)

            if 'homepro.co.th' in url and result.html and len(result.html) < 500:
                print(f"[SCRAPER] WARNING: EMPTY PAGE: HomePro HTML only {len(result.html)} chars - wait_for passed but page is blank!", flush=True, file=sys.stderr)

        if not result.success:
            print_status_panel(console, f"Failed to scrape: {result.error_message}", adw_id, "extraction", "error", url)
            return None

        html_length = len(result.html) if result.html else 0
        content_length = len(result.content) if result.content else 0
        print_status_panel(console, f"Extracted HTML: {html_length} chars, Content: {content_length} chars", adw_id, "extraction", "success", url)

        # DEBUG: For HomePro, check if key elements are present
        if 'homepro.co.th' in url and result.html:
            has_json_ld = 'application/ld+json' in result.html
            has_price_element = 'price' in result.html.lower()
            has_product_name = '<h1' in result.html
            print(f"[HomePro DEBUG] HTML analysis:", flush=True, file=sys.stderr)
            print(f"  Has JSON-LD: {has_json_ld}", flush=True, file=sys.stderr)
            print(f"  Has price element: {has_price_element}", flush=True, file=sys.stderr)
            print(f"  Has H1 tag: {has_product_name}", flush=True, file=sys.stderr)

        # Get appropriate extractor for the URL
        extractor = get_extractor(url)
        print(f"[SCRAPER] Using extractor: {type(extractor).__name__}", flush=True, file=sys.stderr)

        # Extract product data
        print(f"[SCRAPER] Starting extraction...", flush=True, file=sys.stderr)
        product = extractor.extract_from_html(result.html or result.content, url)
        print(f"[SCRAPER] Extraction complete. Product returned: {product is not None}", flush=True, file=sys.stderr)

        if product:
            print(f"[SCRAPER] Product extracted successfully:", flush=True, file=sys.stderr)
            print(f"    Name: {product.name}", flush=True, file=sys.stderr)
            print(f"    Price: {product.current_price}", flush=True, file=sys.stderr)
        else:
            print(f"[SCRAPER] Extraction returned None!", flush=True, file=sys.stderr)

        # Generic Retry: If price extraction failed, retry for non-HardwareWarehouse retailers
        # GlobalHouse: max 2 retries (Playwright times out, falls back to requests; 1 extra attempt)
        extraction_attempt = 1
        max_extraction_retries = 2 if 'globalhouse.co.th' in url else 3

        while extraction_attempt <= max_extraction_retries and 'hardwarehouse.co.th' not in url:
            if not product or not product.current_price:
                print(f"[SCRAPER DEBUG] Extraction completed for: {url}", flush=True, file=sys.stderr)
                print(f"  Name: {product.name if product else None}", flush=True, file=sys.stderr)
                print(f"  Price: {product.current_price if product else None}", flush=True, file=sys.stderr)

                if extraction_attempt < max_extraction_retries:
                    print(f"[SCRAPER] WARNING: Price not found (attempt {extraction_attempt}/{max_extraction_retries}), retrying...", flush=True, file=sys.stderr)

                    import asyncio
                    retry_delay = 5
                    print(f"[SCRAPER] RETRY: Waiting {retry_delay}s before re-scraping...", flush=True, file=sys.stderr)
                    await asyncio.sleep(retry_delay)

                    print(f"[SCRAPER] RETRY: Re-scraping page (attempt {extraction_attempt + 1})...", flush=True, file=sys.stderr)
                    result = await wrapper.scrape_url(url, css_selector=css_selector, wait_for=wait_for)

                    # GlobalHouse retry fallback: if Playwright timed out again, use requests
                    if 'globalhouse.co.th' in url and (not result.success or not result.html or len(result.html) < 500):
                        print(f"[SCRAPER] GlobalHouse RETRY: Playwright timed out again, using requests fallback...", flush=True, file=sys.stderr)
                        import requests as _requests
                        from adw_modules.crawl4ai_wrapper import ScrapingResult
                        _gbh_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                        try:
                            _resp = _requests.get(url, headers=_gbh_headers, timeout=30)
                            result = ScrapingResult(url=url, success=True, html=_resp.text, content=_resp.text)
                        except Exception as _e:
                            print(f"[SCRAPER] GlobalHouse RETRY requests also failed: {_e}", flush=True, file=sys.stderr)

                    if result.success and result.html:
                        print(f"[SCRAPER] RETRY: Scrape successful, HTML length: {len(result.html)}", flush=True, file=sys.stderr)
                        product = extractor.extract_from_html(result.html or result.content, url)

                        if product and product.current_price:
                            print(f"[SCRAPER] RETRY SUCCEEDED! Got Price={product.current_price}", flush=True, file=sys.stderr)
                            break
                        else:
                            print(f"[SCRAPER] RETRY: Price still not found", flush=True, file=sys.stderr)
                    else:
                        print(f"[SCRAPER] RETRY: Scrape failed: {result.error_message if result else 'No result'}", flush=True, file=sys.stderr)

                    extraction_attempt += 1
                else:
                    print(f"[SCRAPER] All {max_extraction_retries} extraction attempts failed!", flush=True, file=sys.stderr)
                    break
            else:
                break

        if product:
            print_status_panel(console, f"Successfully extracted: {product.name[:50]}...", adw_id, "extraction", "success", url)
            print(f"[SCRAPER] Returning product object", flush=True, file=sys.stderr)
            return product
        else:
            print(f"[SCRAPER] EXTRACTION FAILED - Returning None for {url}", flush=True, file=sys.stderr)
            print_status_panel(console, "Failed to extract product data", adw_id, "extraction", "error", url)
            return None

    except Exception as e:
        print_status_panel(console, f"Extraction error: {str(e)}", adw_id, "extraction", "error", url)
        return None


def generate_summary_stats(products: List[ProductData]) -> Dict[str, Any]:
    """Generate summary statistics from extracted products."""
    total = len(products)
    if total == 0:
        return {"total_products": 0}

    # Pricing statistics
    products_with_current_price = [p for p in products if p.current_price is not None]
    products_with_original_price = [p for p in products if p.original_price is not None]
    products_with_discount = [p for p in products if p.has_discount]

    price_stats = {}
    if products_with_current_price:
        current_prices = [p.current_price for p in products_with_current_price]
        price_stats = {
            "min_price": min(current_prices),
            "max_price": max(current_prices),
            "avg_price": sum(current_prices) / len(current_prices),
            "products_with_pricing": len(products_with_current_price),
        }

    discount_stats = {}
    if products_with_discount:
        discount_amounts = [p.discount_amount for p in products_with_discount]
        discount_percents = [p.discount_percent for p in products_with_discount]
        discount_stats = {
            "products_with_discount": len(products_with_discount),
            "min_discount_amount": min(discount_amounts),
            "max_discount_amount": max(discount_amounts),
            "avg_discount_amount": sum(discount_amounts) / len(discount_amounts),
            "min_discount_percent": min(discount_percents),
            "max_discount_percent": max(discount_percents),
            "avg_discount_percent": sum(discount_percents) / len(discount_percents),
        }

    # Field completeness
    field_stats = {}
    fields = ['name', 'brand', 'model', 'sku', 'category', 'volume', 'dimensions', 'material', 'color', 'description']
    for field in fields:
        count = sum(1 for p in products if getattr(p, field) is not None and getattr(p, field) != '')
        field_stats[field] = count

    # Retailer distribution
    retailers = {}
    for product in products:
        retailer = product.retailer or "Unknown"
        retailers[retailer] = retailers.get(retailer, 0) + 1

    return {
        "total_products": total,
        "price_statistics": price_stats,
        "discount_statistics": discount_stats,
        "field_completeness": field_stats,
        "retailer_distribution": retailers,
        "processing_time": datetime.now().isoformat(),
    }


@click.command()
@click.option(
    "--url",
    help="Single product URL to scrape"
)
@click.option(
    "--urls-file",
    type=click.Path(exists=True),
    help="File containing list of product URLs to scrape (one per line)"
)
@click.option(
    "--output-file",
    default=None,
    help="Output file path for scraped product data (defaults to retailer_name.json)"
)
@click.option(
    "--output-folder",
    type=click.Path(),
    help="Base output folder for organized results (creates date/job-ID subdirectories)"
)
@click.option(
    "--organization",
    type=click.Choice(["date", "job-id"]),
    default="date",
    help="How to organize output subdirectories when using --output-folder"
)
@click.option(
    "--adw-id",
    help="ADW ID for tracking (auto-generated if not provided)"
)
@click.option(
    "--max-concurrent",
    type=int,
    default=2,
    help="Maximum concurrent requests (default: 2, recommended for stability)"
)
@click.option(
    "--delay",
    type=float,
    default=1.0,
    help="Delay between requests in seconds"
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Request timeout in seconds"
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Run browser in headless mode"
)
@click.option(
    "--verbose/--no-verbose",
    default=False,
    help="Enable verbose output"
)
@click.option(
    "--retry-attempts",
    type=int,
    default=3,
    help="Number of retry attempts for failed requests"
)
@click.option(
    "--retry-delay",
    type=float,
    default=2.0,
    help="Delay between retries in seconds"
)
@click.option(
    "--use-browser/--no-browser",
    default=True,
    help="Use browser for scraping (handles JavaScript)"
)
@click.option(
    "--test",
    is_flag=True,
    help="Run in test mode with minimal output"
)
@click.option(
    "--no-incremental-save",
    is_flag=True,
    help="Disable incremental saving (saves only at the end, reduces memory and I/O)"
)
@click.option(
    "--proxy",
    default=None,
    help="Proxy URL for HomePro only (e.g. http://user:pass@host:port). Other retailers are unaffected."
)
def main(
    url: Optional[str],
    urls_file: Optional[str],
    output_file: Optional[str],
    output_folder: Optional[str],
    organization: str,
    adw_id: Optional[str],
    max_concurrent: int,
    delay: float,
    timeout: int,
    headless: bool,
    verbose: bool,
    retry_attempts: int,
    retry_delay: float,
    use_browser: bool,
    test: bool,
    no_incremental_save: bool,
    proxy: Optional[str],
):
    """E-commerce product data scraper."""

    console = Console()

    # Generate ADW ID if not provided
    if not adw_id:
        import uuid
        adw_id = str(uuid.uuid4())[:8]

    # Validate input arguments
    input_sources = [url, urls_file]
    active_sources = [source for source in input_sources if source is not None]

    if len(active_sources) == 0:
        raise click.ClickException("Either --url or --urls-file must be provided")

    if len(active_sources) > 1:
        raise click.ClickException("Cannot specify both --url and --urls-file")

    # Determine URLs to scrape
    if url:
        urls = [url]
        source_description = f"single URL: {url}"
    else:  # urls_file
        urls = load_urls_from_file(urls_file)
        source_description = f"URLs file: {urls_file}"

    if not urls:
        raise click.ClickException("No URLs found to scrape")

    # Handle output directory structure
    if output_folder:
        # Create organized output directory structure
        output_dir = create_output_directory_structure(output_folder, adw_id, organization)
        # Use custom filename or default to combined.json
        output_filename = output_file if output_file else "combined.json"
        output_file_full_path = os.path.join(output_dir, output_filename)
        base_output_folder = output_dir
    else:
        # Use legacy ADW structure or results folder
        if output_file:
            # Custom output file specified
            output_file_full_path = output_file
            output_dir = os.path.dirname(output_file) or "./results"
        else:
            # No output file specified - will use retailer-based naming in results folder
            output_dir = "./results"
            output_file_full_path = os.path.join(output_dir, "combined.json")
        
        os.makedirs(output_dir, exist_ok=True)
        base_output_folder = output_dir

    # Parse proxy into homepro_proxy dict if provided
    homepro_proxy_config = None
    if proxy:
        # crawl4ai expects {"server": "http://host:port", "username": "...", "password": "..."}
        # but also accepts a plain URL string via the server field
        homepro_proxy_config = {"server": proxy}

    # Check if any URLs are HomePro and reduce max_concurrent automatically
    homepro_urls = [u for u in urls if 'homepro.co.th' in u.lower()]
    if homepro_urls and max_concurrent > 1:
        original_max_concurrent = max_concurrent
        max_concurrent = 1  # Force sequential scraping for HomePro stability
        print(f"\n[HOMEPRO AUTO-ADJUST] Detected {len(homepro_urls)} HomePro URLs out of {len(urls)} total", flush=True, file=sys.stderr)
        print(f"[HOMEPRO AUTO-ADJUST] Reducing max_concurrent: {original_max_concurrent} -> 1", flush=True, file=sys.stderr)
        print(f"[HOMEPRO AUTO-ADJUST] HomePro React pages require sequential scraping for stability\n", flush=True, file=sys.stderr)

    # Create scraping configuration
    config = create_simple_config(
        max_concurrent=max_concurrent,
        delay_between_requests=delay,
        timeout=timeout,
        headless=headless,
        verbose=verbose,
        retry_attempts=retry_attempts,
        retry_delay=retry_delay,
        use_browser=use_browser,
        homepro_proxy=homepro_proxy_config,
    )

    # Display configuration
    config_table = Table(show_header=False, box=None, padding=(0, 1))
    config_table.add_column(style="bold cyan")
    config_table.add_column()

    config_table.add_row("ADW ID", adw_id)
    config_table.add_row("Products to scrape", str(len(urls)))
    config_table.add_row("Input source", source_description)
    config_table.add_row("Output file", output_file_full_path)

    if output_folder:
        config_table.add_row("Base output folder", output_folder)
        config_table.add_row("Organization", organization)

    config_table.add_row("Max concurrent", str(max_concurrent))
    config_table.add_row("Delay (seconds)", str(delay))
    config_table.add_row("Timeout (seconds)", str(timeout))
    config_table.add_row("Use browser", str(use_browser))
    config_table.add_row("Headless", str(headless))

    console.print(
        Panel(
            config_table,
            title=f"[bold blue]🛍️  E-commerce Product Scraper Configuration[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # Prepare for scraping
    products = []
    summary_stats = {}
    error_message = None

    try:
        # Initialize the wrapper
        print_status_panel(console, "Initializing crawl4ai wrapper", adw_id, "init")

        wrapper = Crawl4AIWrapper(config)

        async def run_scraping():
            """Run the product scraping process."""
            async with wrapper:
                if len(urls) == 1:
                    # Single product scraping
                    print_status_panel(console, f"Scraping {urls[0]}", adw_id, "scraping", urls[0])
                    product = await extract_product_data(urls[0], wrapper, adw_id, console, config)
                    return [product] if product else []
                else:
                    # Batch scraping with progress indicator
                    console.print(f"[bold cyan]Scraping {len(urls)} products...[/bold cyan]")
                    console.print()

                    with Progress() as progress:
                        task_id = progress.add_task("Scraping products...", total=len(urls))

                        products = []
                        semaphore = asyncio.Semaphore(max_concurrent)

                        async def scrape_with_semaphore(url: str) -> Optional[ProductData]:
                            async with semaphore:
                                try:
                                    # HomePro: cap at 25s (20s crawler + 5s buffer)
                                    # GlobalHouse: 70s (1 retry × 30s asyncio + 30s requests fallback + buffer)
                                    # Other sites: timeout + 10s buffer
                                    if 'homepro.co.th' in url:
                                        per_url_timeout = 25
                                    elif 'globalhouse.co.th' in url:
                                        per_url_timeout = 75  # 30s Playwright + 5s delay + 30s retry + buffer
                                    else:
                                        per_url_timeout = timeout + 10
                                    product = await asyncio.wait_for(
                                        extract_product_data(url, wrapper, adw_id, console, config),
                                        timeout=per_url_timeout
                                    )
                                except asyncio.TimeoutError:
                                    per_url_timeout = 25 if 'homepro.co.th' in url else timeout + 10
                                    console.print(f"[red]Timeout scraping {url} (>{per_url_timeout}s) - skipping[/red]")
                                    return None
                                # Add delay between requests
                                if delay > 0:
                                    await asyncio.sleep(delay)
                                return product

                        # Process URLs in chunks with browser restart between chunks
                        # Strategy: Process 10 URLs concurrently (with max_concurrent limit), then restart browser
                        urls_per_chunk = 10  # Process 10 URLs, then restart browser
                        urls_processed = 0

                        for i in range(0, len(urls), urls_per_chunk):
                            url_chunk = urls[i:i + urls_per_chunk]

                            # Process this chunk with concurrency control (respects semaphore)
                            tasks = [scrape_with_semaphore(url) for url in url_chunk]

                            # Wait for all tasks in this chunk to complete
                            for future in asyncio.as_completed(tasks):
                                try:
                                    result = await future
                                    if result:
                                        products.append(result)

                                        # Incremental save - separate files per retailer (only if enabled)
                                        if not no_incremental_save:
                                            try:
                                                # Group products by retailer
                                                from collections import defaultdict
                                                products_by_retailer = defaultdict(list)
                                                for p in products:
                                                    retailer_name = p.retailer.lower().replace(' ', '_') if p.retailer else 'unknown'
                                                    products_by_retailer[retailer_name].append(p.to_dict())

                                                # Save each retailer to a separate file
                                                output_dir = os.path.dirname(output_file_full_path)
                                                os.makedirs(output_dir, exist_ok=True)

                                                for retailer_name, retailer_products in products_by_retailer.items():
                                                    retailer_file = os.path.join(output_dir, f"{retailer_name}.json")
                                                    with open(retailer_file, 'w', encoding='utf-8') as f:
                                                        json.dump(retailer_products, f, ensure_ascii=False, indent=2)
                                            except Exception as e:
                                                console.print(f"[yellow]Warning: Failed to save incremental results: {e}[/yellow]")

                                    urls_processed += 1
                                    progress.advance(task_id)

                                except Exception as e:
                                    console.print(f"[red]Error in scraping task: {str(e)}[/red]")
                                    progress.advance(task_id)

                            # Restart browser BETWEEN chunks (after all tasks in chunk complete)
                            if i + urls_per_chunk < len(urls):
                                console.print(f"[yellow]🔄 Restarting browser after {urls_processed} URLs to free resources...[/yellow]")
                                await wrapper.restart()
                                # Add delay after restart to let system stabilize
                                await asyncio.sleep(3)
                                console.print(f"[green]✅ Browser restarted successfully[/green]")

                    # Save file immediately after scraping
                    if products:
                        try:
                            import sys
                            from collections import defaultdict
                            products_by_retailer = defaultdict(list)
                            for p in products:
                                retailer_name = p.retailer.lower().replace(' ', '_') if p.retailer else 'unknown'
                                products_by_retailer[retailer_name].append(p.to_dict())
                            
                            output_dir = os.path.dirname(output_file_full_path) or "./results"
                            os.makedirs(output_dir, exist_ok=True)
                            
                            if output_file:
                                # Save all products to the specified file
                                all_products_dict = [p.to_dict() for p in products]
                                print(f"\n💾 Saving {len(all_products_dict)} products...")
                                sys.stdout.flush()
                                with open(output_file_full_path, 'w', encoding='utf-8') as f:
                                    json.dump(all_products_dict, f, ensure_ascii=False, indent=2)
                                print(f"✅ File saved: {output_file_full_path}")
                                sys.stdout.flush()
                            else:
                                # Save separate file per retailer
                                for retailer_name, retailer_products in products_by_retailer.items():
                                    retailer_file = os.path.join(output_dir, f"{retailer_name}.json")
                                    with open(retailer_file, 'w', encoding='utf-8') as f:
                                        json.dump(retailer_products, f, ensure_ascii=False, indent=2)
                                print(f"✅ Saved {len(products_by_retailer)} retailer files")
                                sys.stdout.flush()
                        except Exception as e:
                            print(f"❌ Failed to save results: {e}")
                            sys.stdout.flush()
                    
                    return products

        # Run the scraping
        print_status_panel(console, "Starting product scraping process", adw_id, "scraping")
        products = asyncio.run(run_scraping())

        print_status_panel(console, "Completed product scraping process", adw_id, "scraping", "success")

        # Generate summary statistics
        summary_stats = generate_summary_stats(products)

        # Display results summary
        console.print()
        console.print(Rule("[bold yellow]Product Scraping Results Summary[/bold yellow]"))
        console.print()

        summary_table = Table()
        summary_table.add_column("Metric", style="bold cyan")
        summary_table.add_column("Value", style="bold")

        summary_table.add_row("Total Products", str(summary_stats["total_products"]))
        summary_table.add_row("Successfully Extracted", str(len(products)))

        if summary_stats.get("price_statistics"):
            price_stats = summary_stats["price_statistics"]
            summary_table.add_row("Products with Pricing", str(price_stats["products_with_pricing"]))
            if price_stats["products_with_pricing"] > 0:
                summary_table.add_row("Price Range", f"{price_stats['min_price']:.2f} - {price_stats['max_price']:.2f}")
                summary_table.add_row("Average Price", f"{price_stats['avg_price']:.2f}")

        if summary_stats.get("discount_statistics"):
            discount_stats = summary_stats["discount_statistics"]
            summary_table.add_row("Products with Discount", str(discount_stats["products_with_discount"]))
            if discount_stats["products_with_discount"] > 0:
                summary_table.add_row("Avg Discount", f"{discount_stats['avg_discount_percent']:.1f}%")

        console.print(summary_table)

        # Group products by retailer
        from collections import defaultdict
        products_by_retailer = defaultdict(list)
        for product in products:
            retailer_name = product.retailer.lower().replace(' ', '_') if product.retailer else 'unknown'
            products_by_retailer[retailer_name].append(product.to_dict())

        # Save results
        output_dir = os.path.dirname(output_file_full_path) or "./results"
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        # If custom output file was specified, save to that file only
        if output_file:
            # Save all products to the specified file
            all_products_dict = [p.to_dict() for p in products]
            print_status_panel(console, f"Saving {len(all_products_dict)} products to {output_file_full_path}", adw_id, "output")
            with open(output_file_full_path, 'w', encoding='utf-8') as f:
                json.dump(all_products_dict, f, ensure_ascii=False, indent=2)
            saved_files.append(("all", output_file_full_path, len(all_products_dict)))
        else:
            # No custom output file - save separate file per retailer
            for retailer_name, retailer_products in products_by_retailer.items():
                retailer_file = os.path.join(output_dir, f"{retailer_name}.json")
                print_status_panel(console, f"Saving {len(retailer_products)} {retailer_name} products to {retailer_file}", adw_id, "output")
                with open(retailer_file, 'w', encoding='utf-8') as f:
                    json.dump(retailer_products, f, ensure_ascii=False, indent=2)
                saved_files.append((retailer_name, retailer_file, len(retailer_products)))
        
        if output_file:
            print_status_panel(console, f"Saved all products to {output_file_full_path}", adw_id, "output", "success")
        else:
            print_status_panel(console, f"Saved {len(saved_files)} retailer files to {output_dir}", adw_id, "output", "success")

        # Display final output info
        console.print()
        if output_folder:
            # Display organized output structure
            output_info = (
                f"[bold cyan]Products Extracted:[/bold cyan] {len(products)}\n"
                f"[bold cyan]Base Output Folder:[/bold cyan] {output_folder}\n"
                f"[bold cyan]Organization:[/bold cyan] {organization}\n"
                f"[bold cyan]Job Directory:[/bold cyan] {base_output_folder}\n"
                f"[bold cyan]Results File:[/bold cyan] {output_file_full_path}\n"
                f"[bold cyan]Success Rate:[/bold cyan] {(len(products)/len(urls)*100):.1f}%"
            )
        else:
            # Display legacy structure
            output_info = (
                f"[bold cyan]Products Extracted:[/bold cyan] {len(products)}\n"
                f"[bold cyan]Output File:[/bold cyan] {output_file_full_path}\n"
                f"[bold cyan]ADW Directory:[/bold cyan] {output_dir}\n"
                f"[bold cyan]Success Rate:[/bold cyan] {(len(products)/len(urls)*100):.1f}%"
            )

        console.print(
            Panel(
                output_info,
                title="[bold green]✅ E-commerce Product Scraping Complete[/bold green]",
                border_style="green",
            )
        )

        # Exit with appropriate code
        if len(products) == 0:
            sys.exit(1)  # All extractions failed
        elif len(products) < len(urls):
            sys.exit(2)  # Some extractions failed
        else:
            sys.exit(0)  # All extractions succeeded

    except KeyboardInterrupt:
        print_status_panel(console, "Scraping interrupted by user", adw_id, "scraping", "warning")
        sys.exit(130)

    except Exception as e:
        error_message = str(e)
        print_status_panel(console, f"Scraping failed: {error_message}", adw_id, "scraping", "error")
        sys.exit(1)


if __name__ == "__main__":
    main()
