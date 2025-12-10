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


async def extract_product_data(url: str, wrapper: Crawl4AIWrapper, adw_id: str, console: Console) -> Optional[ProductData]:
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
            wait_for = "() => document.querySelector('[class*=\"price\"]') !== null && document.body.innerText.includes('฿')"

        # Scrape the URL
        result = await wrapper.scrape_url(url, css_selector=css_selector, wait_for=wait_for)

        if not result.success:
            print_status_panel(console, f"Failed to scrape: {result.error_message}", adw_id, "extraction", "error", url)
            return None

        print_status_panel(console, f"Extracted {len(result.content) if result.content else 0} characters", adw_id, "extraction", "success", url)

        # Get appropriate extractor for the URL
        extractor = get_extractor(url)
        
        # Extract product data
        product = extractor.extract_from_html(result.html or result.content, url)
        
        # LLM Fallback Logic - TEMPORARILY DISABLED due to LLMConfig ForwardRef issue in crawl4ai
        # The primary extraction with JSON-LD and Quick Info parsing should be sufficient
        # TODO: Re-enable once LLMConfig import issue is resolved
        # if not product or not product.name or not product.current_price:
        #     api_key = "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"
        #     if api_key:
        #         print_status_panel(console, "Primary extraction incomplete. Attempting LLM fallback (OpenRouter)...", adw_id, "extraction", "warning", url)
        #         # ... (LLM fallback code commented out)

        if product:
            print_status_panel(console, f"Successfully extracted: {product.name[:50]}...", adw_id, "extraction", "success", url)
            return product
        else:
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
    default="products.json",
    help="Output file path for scraped product data"
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
    default=3,
    help="Maximum concurrent requests"
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
def main(
    url: Optional[str],
    urls_file: Optional[str],
    output_file: str,
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
        output_file_full_path = os.path.join(output_dir, output_file)
        base_output_folder = output_dir
    else:
        # Use legacy ADW structure
        output_dir = f"./agents/{adw_id}/ecommerce_scraper"
        os.makedirs(output_dir, exist_ok=True)
        output_file_full_path = output_file
        base_output_folder = output_dir

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
                    product = await extract_product_data(urls[0], wrapper, adw_id, console)
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
                                    product = await extract_product_data(url, wrapper, adw_id, console)
                                    # Add delay between requests
                                    if delay > 0:
                                        await asyncio.sleep(delay)
                                    return product
                                finally:
                                    # Update progress regardless of success/failure
                                    progress.advance(task_id)

                        # Process all URLs concurrently
                        tasks = [scrape_with_semaphore(url) for url in urls]
                        
                        # Use as_completed to process results as they finish
                        for future in asyncio.as_completed(tasks):
                            try:
                                result = await future
                                if result:
                                    products.append(result)
                                    
                                    # Incremental save - separate files per retailer
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
                                        
                                progress.advance(task_id)
                            except Exception as e:
                                console.print(f"[red]Error in scraping task: {str(e)}[/red]")
                                progress.advance(task_id)

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

        # Save results - separate file per retailer
        output_dir = os.path.dirname(output_file_full_path)
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        for retailer_name, retailer_products in products_by_retailer.items():
            retailer_file = os.path.join(output_dir, f"{retailer_name}.json")
            print_status_panel(console, f"Saving {len(retailer_products)} {retailer_name} products to {retailer_file}", adw_id, "output")
            with open(retailer_file, 'w', encoding='utf-8') as f:
                json.dump(retailer_products, f, ensure_ascii=False, indent=2)
            saved_files.append((retailer_name, retailer_file, len(retailer_products)))
        
        print_status_panel(console, f"Saved {len(saved_files)} retailer files to {output_dir}", adw_id, "output", "success")
        
        print_status_panel(console, f"Results saved to {output_file_full_path}", adw_id, "output", "success")

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
