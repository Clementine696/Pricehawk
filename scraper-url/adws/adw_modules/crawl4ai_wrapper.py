"""
Crawl4AI wrapper module for providing consistent interface and error handling.

This module wraps the crawl4ai library to provide:
- Scraping configuration management
- URL validation and preprocessing
- Content extraction methods
- Error handling for network issues and anti-bot measures
- Output formatting functions
"""

import asyncio
import json
import re
import time
import urllib.parse
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
    try:
        from crawl4ai.crawler_strategy import CrawlerRunConfig
    except ImportError:
        try:
            from crawl4ai import CrawlerRunConfig
        except ImportError:
            CrawlerRunConfig = None
    try:
        from crawl4ai.llm_config import LLMConfig
    except ImportError:
        try:
            from crawl4ai.extraction_strategy import LLMConfig
        except ImportError:
            LLMConfig = None

    from crawl4ai.chunking_strategy import RegexChunking
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    AsyncWebCrawler = None
    LLMExtractionStrategy = None
    JsonCssExtractionStrategy = None
    RegexChunking = None
    LLMConfig = None
    CrawlerRunConfig = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration for web scraping operations."""
    max_concurrent: int = 3
    delay_between_requests: float = 1.0
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (compatible; Crawl4AI/1.0)"
    headless: bool = True
    verbose: bool = False
    retry_attempts: int = 3
    retry_delay: float = 2.0

    # Browser launch retry settings
    browser_launch_retries: int = 3
    browser_launch_retry_delay: float = 2.0

    # Anti-bot measures
    respect_robots_txt: bool = True
    use_browser: bool = True
    simulate_user: bool = True

    # Content filtering
    min_content_length: int = 100
    max_content_length: int = 1000000  # 1MB

    # Output options
    include_links: bool = True
    include_images: bool = True
    include_metadata: bool = True


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    url: str
    success: bool
    content: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    links: List[str] = None
    images: List[str] = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    timestamp: float = 0
    status_code: Optional[int] = None
    extracted_content: Optional[str] = None

    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.images is None:
            self.images = []
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp == 0:
            self.timestamp = time.time()


class Crawl4AIWrapper:
    """Wrapper class for crawl4ai functionality."""

    def __init__(self, config: ScrapingConfig = None):
        """Initialize the wrapper with configuration.

        Args:
            config: Scraping configuration. If None, uses defaults.
        """
        self.config = config or ScrapingConfig()

        if not CRAWL4AI_AVAILABLE:
            raise ImportError(
                "crawl4ai is not installed. Install it with: "
                "pip install crawl4ai"
            )

        self.crawler = None
        self._current_mode = None  # Track current mode: 'browser' or 'text'
        self._browser_reinit_attempts = 0  # Track reinitialization attempts during scraping

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _cleanup_browser(self):
        """Private method for consistent browser cleanup across the class."""
        if self.crawler:
            try:
                await self.crawler.close()
                logger.debug("Browser cleanup successful")
            except Exception as e:
                # Ignore errors during cleanup - browser may already be closed
                logger.debug(f"Browser cleanup note (may be already closed): {e}")
            finally:
                self.crawler = None
                self._current_mode = None

    def _is_browser_alive(self) -> bool:
        """Check if the browser instance is still valid and alive.

        Returns:
            True if browser appears to be alive, False otherwise.
        """
        if self.crawler is None:
            return False

        # Check if crawler has browser context attributes that indicate it's alive
        try:
            # For crawl4ai, check if the crawler object exists and has expected attributes
            if hasattr(self.crawler, 'browser_context') and self.crawler.browser_context is None:
                return False
            if hasattr(self.crawler, 'browser') and self.crawler.browser is None:
                return False
            # If we can access the crawler without exception, assume it's alive
            return True
        except Exception as e:
            logger.debug(f"Browser state check failed: {e}")
            return False

    async def initialize(self, force_text_mode: bool = False):
        """Initialize the crawler instance with retry logic.

        Args:
            force_text_mode: If True, skip browser mode and use text mode directly.
        """
        # Clean up any existing browser first
        await self._cleanup_browser()

        last_error = None

        # Try browser mode if requested and not forcing text mode
        if self.config.use_browser and not force_text_mode:
            for attempt in range(self.config.browser_launch_retries):
                try:
                    # Ensure clean state before retry
                    await self._cleanup_browser()

                    self.crawler = AsyncWebCrawler(
                        headless=self.config.headless,
                        verbose=self.config.verbose,
                        user_agent=self.config.user_agent,
                    )
                    await self.crawler.start()
                    self._current_mode = 'browser'
                    logger.info(f"Crawl4AI crawler initialized with browser (attempt {attempt + 1})")
                    return
                except Exception as browser_err:
                    last_error = browser_err
                    error_str = str(browser_err)

                    # Check for specific browser closure errors
                    is_browser_closed_error = (
                        "Target page, context or browser has been closed" in error_str or
                        "BrowserType.launch" in error_str or
                        "Browser closed" in error_str or
                        "Connection closed" in error_str
                    )

                    if is_browser_closed_error:
                        logger.warning(
                            f"Browser launch failed (attempt {attempt + 1}/{self.config.browser_launch_retries}): {browser_err}"
                        )
                    else:
                        logger.warning(f"Browser mode failed (attempt {attempt + 1}): {browser_err}")

                    # Ensure cleanup before retry
                    await self._cleanup_browser()

                    # Add delay before retry with exponential backoff
                    if attempt < self.config.browser_launch_retries - 1:
                        delay = self.config.browser_launch_retry_delay * (2 ** attempt)
                        logger.debug(f"Waiting {delay}s before browser launch retry...")
                        await asyncio.sleep(delay)

            # All browser mode attempts failed, fall back to text mode
            logger.warning(f"Browser mode failed after {self.config.browser_launch_retries} attempts, falling back to text mode")

        # Text mode fallback - use crawler without browser features
        try:
            await self._cleanup_browser()

            self.crawler = AsyncWebCrawler(
                headless=self.config.headless,
                verbose=self.config.verbose,
                user_agent=self.config.user_agent,
            )
            await self.crawler.start()
            self._current_mode = 'text'
            logger.info("Crawl4AI crawler initialized in text mode (no browser)")
        except Exception as e:
            logger.error(f"Failed to initialize Crawl4AI crawler in text mode: {e}")
            await self._cleanup_browser()
            # Re-raise the original browser error if text mode also fails
            if last_error:
                raise last_error
            raise

    async def close(self):
        """Close the crawler instance safely."""
        await self._cleanup_browser()
        logger.info("Crawl4AI crawler closed successfully")

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate and normalize URL.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, normalized_url_or_error)
        """
        if not url or not isinstance(url, str):
            return False, "URL must be a non-empty string"

        url = url.strip()
        if not url:
            return False, "URL cannot be empty"

        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                return False, "Invalid URL format"
            return True, url
        except Exception as e:
            return False, f"URL parsing error: {e}"

    def is_ecommerce_url(self, url: str) -> bool:
        """Check if a URL belongs to supported e-commerce retailers.

        Args:
            url: URL to check

        Returns:
            True if the URL belongs to a supported e-commerce retailer, False otherwise
        """
        try:
            # Extract domain from URL
            parsed = urllib.parse.urlparse(url.lower())
            domain = parsed.netloc.lower()

            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]

            # List of supported e-commerce retailers
            supported_retailers = {
                'thaiwatsadu.com',
                'homepro.co.th',
                'dohome.co.th',
                'boonthavorn.com',
                'globalhouse.co.th',
                'megahome.co.th'
            }

            return domain in supported_retailers
        except Exception as e:
            logger.warning(f"Failed to check e-commerce URL {url}: {e}")
            return False

    def _is_browser_closed_error(self, error: Exception) -> bool:
        """Check if an exception indicates the browser was closed.

        Args:
            error: The exception to check.

        Returns:
            True if this appears to be a browser closure error.
        """
        error_str = str(error)
        return (
            "Target page, context or browser has been closed" in error_str or
            "BrowserType.launch" in error_str or
            "Browser closed" in error_str or
            "Connection closed" in error_str or
            "Browser has been closed" in error_str or
            "page.goto: Target closed" in error_str
        )

    async def scrape_url(
        self,
        url: str,
        extraction_strategy: Optional[Any] = None,
        wait_for: Optional[str] = None,
        css_selector: Optional[str] = None
    ) -> ScrapingResult:
        """Scrape a single URL.

        Args:
            url: URL to scrape
            extraction_strategy: Optional extraction strategy
            wait_for: Optional JavaScript condition to wait for
            css_selector: Optional CSS selector to wait for

        Returns:
            ScrapingResult with scraped data
        """
        is_valid, normalized_url_or_error = self.validate_url(url)
        if not is_valid:
            return ScrapingResult(
                url=url,
                success=False,
                error_message=normalized_url_or_error
            )

        url = normalized_url_or_error

        # Check if browser is alive, reinitialize if needed
        if not self._is_browser_alive():
            logger.debug("Browser not alive, reinitializing...")
            await self.initialize()

        result = ScrapingResult(url=url, success=False)
        max_browser_reinit = 2  # Maximum number of browser reinitialization attempts per URL

        for attempt in range(self.config.retry_attempts):
            try:
                # Add delay between requests (except first attempt)
                if attempt > 0:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

                logger.info(f"Scraping URL: {url} (attempt {attempt + 1})")

                # Determine if this is an e-commerce URL that needs scrolling
                is_ecommerce = self.is_ecommerce_url(url)

                # Enhanced JS code for e-commerce sites - scroll to load lazy content
                # Wrapped in async IIFE for proper execution
                js_scroll_code = """
(async () => {
    // Function to scroll down the page to load lazy content
    async function scrollToBottom() {
        const scrollHeight = document.body.scrollHeight;
        const viewportHeight = window.innerHeight;
        let currentPosition = 0;

        while (currentPosition < scrollHeight) {
            currentPosition += viewportHeight * 0.8;
            window.scrollTo(0, currentPosition);
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        // Scroll to middle of page where specs usually are
        window.scrollTo(0, scrollHeight * 0.5);
        await new Promise(resolve => setTimeout(resolve, 500));

        // Scroll back to top
        window.scrollTo(0, 0);
        await new Promise(resolve => setTimeout(resolve, 300));
    }

    // Function to click "Read More" buttons to expand content
    async function clickReadMoreButtons() {
        // Thai Watsadu specific button
        const readMoreBtn = document.getElementById('readmorePdp');
        if (readMoreBtn) {
            readMoreBtn.click();
            await new Promise(resolve => setTimeout(resolve, 800));
        }

        // HomePro specific - click specification tab to load dimensions/volume
        const homeproSpecTab = document.getElementById('product-specification-tab');
        if (homeproSpecTab) {
            homeproSpecTab.click();
            await new Promise(resolve => setTimeout(resolve, 800));
        }

        // DoHome specific - click "ข้อมูลจำเพาะ" (Specifications) tab
        const dohomeButtons = document.querySelectorAll('button');
        for (const btn of dohomeButtons) {
            const h2 = btn.querySelector('h2');
            if (h2 && h2.textContent.includes('ข้อมูลจำเพาะ')) {
                btn.click();
                await new Promise(resolve => setTimeout(resolve, 800));
                break;
            }
        }

        // Boonthavorn specific - click "ข้อมูลจำเพาะ" (Specifications) tab
        // The tab is an h5 element with class horizontalTab-tabListItem
        const boonthavornTabs = document.querySelectorAll('h5[class*="horizontalTab-tabListItem"], [class*="horizontalTab"] span, [class*="horizontalTabs"] h5');
        for (const tab of boonthavornTabs) {
            if (tab.textContent && tab.textContent.includes('ข้อมูลจำเพาะ')) {
                // Scroll to the tab first
                tab.scrollIntoView({ behavior: 'instant', block: 'center' });
                await new Promise(resolve => setTimeout(resolve, 500));
                // Try multiple click methods for React components
                tab.click();
                tab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                await new Promise(resolve => setTimeout(resolve, 1500));
                break;
            }
        }

        // Generic read more buttons
        const selectors = [
            'button[class*="read-more"]',
            'button[class*="show-more"]',
            '.read-more',
            '.show-more',
            '[data-action="expand"]'
        ];

        for (const selector of selectors) {
            try {
                const buttons = document.querySelectorAll(selector);
                for (const btn of buttons) {
                    if (btn && btn.offsetParent !== null) {
                        btn.click();
                        await new Promise(resolve => setTimeout(resolve, 300));
                    }
                }
            } catch (e) {}
        }
    }

    // Wait for initial page load
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Scroll the page to load lazy content
    await scrollToBottom();

    // Click any "Read More" buttons to expand hidden content
    await clickReadMoreButtons();

    // Scroll again after clicking
    await scrollToBottom();

    // Final wait for content to render
    await new Promise(resolve => setTimeout(resolve, 1000));
})();
                """ if is_ecommerce else """
(async () => {
    await new Promise(resolve => setTimeout(resolve, 1500));
})();
                """

                # Perform the crawl using CrawlerRunConfig if available (v0.7.x+)
                if CrawlerRunConfig is not None and self.config.use_browser:
                    run_config = CrawlerRunConfig(
                        word_count_threshold=self.config.min_content_length,
                        extraction_strategy=extraction_strategy,
                        bypass_cache=False,
                        js_code=js_scroll_code,
                        wait_for=wait_for or "() => document.readyState === 'complete' && document.body && document.body.innerText.length > 100",
                        css_selector=css_selector or "body",
                        simulate_user=self.config.simulate_user,
                        override_navigator=True,
                    )
                    crawl_result = await self.crawler.arun(url=url, config=run_config)
                else:
                    # Fallback for older versions or non-browser mode
                    crawl_result = await self.crawler.arun(
                        url=url,
                        word_count_threshold=self.config.min_content_length,
                        extraction_strategy=extraction_strategy,
                        bypass_cache=False,
                        js_code=js_scroll_code if self.config.use_browser else None,
                        wait_for=wait_for or ("""
                        () => document.readyState === 'complete' &&
                        document.body && document.body.innerText.length > 100
                        """ if self.config.use_browser else None),
                        css_selector=css_selector or ("""
                        body
                        """ if self.config.use_browser else None),
                        simulate_user=self.config.simulate_user,
                        override_navigator=True,
                    )

                if crawl_result.success:
                    result.success = True
                    result.content = crawl_result.cleaned_html or crawl_result.html
                    result.markdown = str(crawl_result.markdown) if crawl_result.markdown else None
                    result.html = crawl_result.html
                    result.status_code = getattr(crawl_result, 'status_code', 200)
                    result.extracted_content = getattr(crawl_result, 'extracted_content', None)

                    # Extract links
                    if self.config.include_links and crawl_result.links:
                        try:
                            result.links = [link.get('href', '') for link in crawl_result.links
                                          if link and hasattr(link, 'get') and link.get('href')]
                        except (TypeError, AttributeError):
                            result.links = []

                    # Extract images
                    if self.config.include_images and crawl_result.media:
                        try:
                            result.images = [media.get('src', '') for media in crawl_result.media
                                          if media and hasattr(media, 'get') and media.get('src') and media.get('type') == 'image']
                        except (TypeError, AttributeError):
                            result.images = []

                    # Extract metadata
                    if self.config.include_metadata:
                        # Enhanced metadata for new structured output
                        domain = self.get_domain_from_url(url)
                        content_type = self.detect_content_type(url, result.content, result.metadata)

                        result.metadata = {
                            'title': getattr(crawl_result, 'title', ''),
                            'description': getattr(crawl_result, 'description', ''),
                            'language': getattr(crawl_result, 'language', ''),
                            'status_code': result.status_code,
                            'url': url,
                            'word_count': len(result.content.split()) if result.content else 0,
                            # New fields for structured output
                            'domain': domain,
                            'content_type': content_type,
                            'scraped_at': result.timestamp,
                            'extraction_method': 'crawl4ai',
                            'links_count': len(result.links) if result.links else 0,
                            'images_count': len(result.images) if result.images else 0,
                        }

                    logger.info(f"Successfully scraped {url}")
                    break
                else:
                    error_msg = getattr(crawl_result, 'error_message', 'Unknown error')
                    result.error_message = f"Crawl failed: {error_msg}"
                    logger.warning(f"Failed to scrape {url}: {error_msg}")

            except Exception as e:
                result.error_message = f"Scraping error: {str(e)}"
                logger.error(f"Error scraping {url} (attempt {attempt + 1}): {e}")

                # Check if this is a browser closure error
                if self._is_browser_closed_error(e):
                    if self._browser_reinit_attempts < max_browser_reinit:
                        self._browser_reinit_attempts += 1
                        logger.warning(
                            f"Browser closed during scraping, reinitializing "
                            f"(reinit attempt {self._browser_reinit_attempts}/{max_browser_reinit})..."
                        )
                        try:
                            # Try to reinitialize browser
                            await self.initialize()
                            # Don't count this as a retry attempt - continue loop
                            continue
                        except Exception as reinit_err:
                            logger.error(f"Failed to reinitialize browser: {reinit_err}")
                            # Fall back to text mode if browser keeps failing
                            if self._current_mode != 'text':
                                logger.warning("Attempting to fall back to text mode...")
                                try:
                                    await self.initialize(force_text_mode=True)
                                    continue
                                except Exception as text_mode_err:
                                    logger.error(f"Text mode fallback also failed: {text_mode_err}")
                    else:
                        logger.warning(
                            f"Max browser reinitialization attempts ({max_browser_reinit}) reached for this URL"
                        )

                if attempt == self.config.retry_attempts - 1:
                    # Final attempt failed
                    break

        # Reset reinit counter after completing URL processing
        self._browser_reinit_attempts = 0
        return result

    async def scrape_urls(
        self,
        urls: List[str],
        extraction_strategy: Optional[Any] = None
    ) -> List[ScrapingResult]:
        """Scrape multiple URLs with concurrency control.

        Args:
            urls: List of URLs to scrape
            extraction_strategy: Optional extraction strategy

        Returns:
            List of ScrapingResult objects
        """
        if not urls:
            return []

        results = []

        # Process URLs in batches to control concurrency
        batch_size = self.config.max_concurrent

        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]

            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(batch_size)

            async def scrape_with_semaphore(url: str) -> ScrapingResult:
                async with semaphore:
                    result = await self.scrape_url(url, extraction_strategy)
                    # Add delay between requests
                    if self.config.delay_between_requests > 0:
                        await asyncio.sleep(self.config.delay_between_requests)
                    return result

            # Process batch concurrently
            batch_tasks = [scrape_with_semaphore(url) for url in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Handle exceptions in results
            for url, batch_result in zip(batch, batch_results):
                if isinstance(batch_result, Exception):
                    results.append(ScrapingResult(
                        url=url,
                        success=False,
                        error_message=f"Batch processing error: {str(batch_result)}"
                    ))
                else:
                    results.append(batch_result)

            logger.info(f"Completed batch {i//batch_size + 1}/{(len(urls) + batch_size - 1)//batch_size}")

        return results

    def create_json_extraction_strategy(self, schema: Dict[str, Any]) -> Any:
        """Create a JSON CSS extraction strategy.

        Args:
            schema: JSON schema for extraction

        Returns:
            JsonCssExtractionStrategy instance
        """
        if not JsonCssExtractionStrategy:
            raise ImportError("JsonCssExtractionStrategy not available")

        return JsonCssExtractionStrategy(schema, verbose=self.config.verbose)

    def create_llm_extraction_strategy(
        self,
        instruction: str,
        provider: str = "openai",
        api_token: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create an LLM extraction strategy.

        Args:
            instruction: Extraction instruction for the LLM
            provider: LLM provider (openai, huggingface, etc.)
            api_token: API token for the provider
            **kwargs: Additional arguments for the strategy (e.g. base_url, model)

        Returns:
            LLMExtractionStrategy instance
        """
        if not LLMExtractionStrategy:
            raise ImportError("LLMExtractionStrategy not available")

        # Create LLMConfig with provider, token, and extra args
        # We pass kwargs (like base_url, model) to LLMConfig
        llm_config = LLMConfig(provider=provider, api_token=api_token, **kwargs)

        return LLMExtractionStrategy(
            llm_config=llm_config,
            instruction=instruction,
            verbose=self.config.verbose
        )

    def format_results(self, results: List[ScrapingResult], format_type: str = "json") -> str:
        """Format scraping results for output.

        Args:
            results: List of ScrapingResult objects
            format_type: Output format ('json', 'csv', 'markdown')

        Returns:
            Formatted string

        Note:
            If any of the results contain e-commerce URLs from supported retailers
            and format_type is 'csv', the format will be automatically forced to 'json'
            to ensure proper structured data handling for e-commerce content.
        """
        # Check if any results contain e-commerce URLs
        has_ecommerce_urls = any(self.is_ecommerce_url(result.url) for result in results)

        # Force JSON format for e-commerce URLs if CSV was requested
        if has_ecommerce_urls and format_type.lower() == "csv":
            print("Warning: E-commerce URLs detected. Forcing JSON output format instead of CSV for proper structured data handling.")
            format_type = "json"

        if format_type.lower() == "json":
            return json.dumps([asdict(result) for result in results], indent=2)

        elif format_type.lower() == "csv":
            import csv
            import io

            if not results:
                return ""

            output = io.StringIO()

            # Write header
            fieldnames = ['url', 'success', 'content_length', 'links_count',
                         'images_count', 'status_code', 'error_message']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            # Write rows
            for result in results:
                writer.writerow({
                    'url': result.url,
                    'success': result.success,
                    'content_length': len(result.content) if result.content else 0,
                    'links_count': len(result.links),
                    'images_count': len(result.images),
                    'status_code': result.status_code or '',
                    'error_message': result.error_message or '',
                })

            return output.getvalue()

        elif format_type.lower() == "markdown":
            if not results:
                return "# No Results\n"

            output = ["# Scraping Results\n"]
            output.append(f"Total URLs processed: {len(results)}")
            output.append(f"Successful: {sum(1 for r in results if r.success)}")
            output.append(f"Failed: {sum(1 for r in results if not r.success)}\n")

            for result in results:
                output.append(f"## {result.url}")
                output.append(f"**Status:** {'✅ Success' if result.success else '❌ Failed'}")

                if result.success:
                    if result.metadata.get('title'):
                        output.append(f"**Title:** {result.metadata['title']}")
                    if result.content:
                        output.append(f"**Content Length:** {len(result.content)} characters")
                    if result.links:
                        output.append(f"**Links Found:** {len(result.links)}")
                    if result.images:
                        output.append(f"**Images Found:** {len(result.images)}")
                    if result.markdown:
                        preview = result.markdown[:200] + "..." if len(result.markdown) > 200 else result.markdown
                        output.append(f"**Content Preview:**\n{preview}")
                else:
                    output.append(f"**Error:** {result.error_message}")

                output.append("")  # Empty line between results

            return "\n".join(output)

        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def get_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name as string
        """
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"Failed to extract domain from {url}: {e}")
            return "unknown_domain"

    def detect_content_type(self, url: str, content: str = None, metadata: Dict = None) -> str:
        """Detect content type based on URL, content, and metadata.

        Args:
            url: URL that was scraped
            content: Raw content (optional)
            metadata: Additional metadata (optional)

        Returns:
            Detected content type as string
        """
        if metadata is None:
            metadata = {}

        url_lower = url.lower()

        # Check URL patterns first
        if any(pattern in url_lower for pattern in ['/product', '/item', '/shop', '/buy', '/cart']):
            return 'products'
        elif any(pattern in url_lower for pattern in ['/article', '/blog', '/news', '/post', '/story']):
            return 'articles'
        elif any(pattern in url_lower for pattern in ['/doc', '/documentation', '/guide', '/help', '/wiki']):
            return 'documentation'
        elif any(pattern in url_lower for pattern in ['/api', '/endpoint', '/service']):
            return 'api'
        elif any(pattern in url_lower for pattern in ['/forum', '/discussion', '/thread', '/comment']):
            return 'forum'
        elif any(pattern in url_lower for pattern in ['/video', '/watch', '/play', '/stream']):
            return 'video'

        # Check metadata if available
        title = str(metadata.get('title', '')).lower()
        description = str(metadata.get('description', '')).lower()

        if any(keyword in title + description for keyword in ['product', 'buy', 'price', 'shop', 'cart', 'purchase']):
            return 'products'
        elif any(keyword in title + description for keyword in ['article', 'blog', 'news', 'post', 'story', 'published']):
            return 'articles'
        elif any(keyword in title + description for keyword in ['documentation', 'guide', 'help', 'manual', 'tutorial']):
            return 'documentation'

        # Analyze content if available
        if content:
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in ['price', 'cart', 'checkout', 'buy now', 'add to cart']):
                return 'products'
            elif any(keyword in content_lower for keyword in ['article', 'published', 'author', 'posted on']):
                return 'articles'
            elif any(keyword in content_lower for keyword in ['documentation', 'guide', 'tutorial', 'step by step']):
                return 'documentation'

        # Additional heuristics based on common patterns
        if any(site in domain for site in ['amazon', 'ebay', 'shopify', 'woocommerce'] for domain in [self.get_domain_from_url(url)]):
            return 'products'
        elif any(site in domain for site in ['wikipedia', 'wiki', 'docs'] for domain in [self.get_domain_from_url(url)]):
            return 'documentation'

        # Default fallback
        return 'general'

    def enhance_result_for_organization(self, result: ScrapingResult) -> ScrapingResult:
        """Enhance a scraping result with organization metadata.

        Args:
            result: ScrapingResult to enhance

        Returns:
            Enhanced ScrapingResult
        """
        if not result.metadata:
            result.metadata = {}

        # Add organization-specific metadata
        result.metadata.update({
            'domain': result.metadata.get('domain', self.get_domain_from_url(result.url)),
            'content_type': result.metadata.get('content_type', self.detect_content_type(result.url, result.content, result.metadata)),
            'organization_timestamp': result.timestamp,
            'result_id': f"{result.url}_{int(result.timestamp)}",
            'has_content': bool(result.content and len(result.content.strip()) > 100),
            'has_links': bool(result.links and len(result.links) > 0),
            'has_images': bool(result.images and len(result.images) > 0),
        })

        return result


# Convenience functions for common use cases
async def scrape_single_url(
    url: str,
    config: ScrapingConfig = None,
    extraction_strategy: Optional[Any] = None
) -> ScrapingResult:
    """Scrape a single URL with default configuration.

    Args:
        url: URL to scrape
        config: Optional scraping configuration
        extraction_strategy: Optional extraction strategy

    Returns:
        ScrapingResult object
    """
    wrapper = Crawl4AIWrapper(config or ScrapingConfig())
    async with wrapper:
        return await wrapper.scrape_url(url, extraction_strategy)


async def scrape_multiple_urls(
    urls: List[str],
    config: ScrapingConfig = None,
    extraction_strategy: Optional[Any] = None
) -> List[ScrapingResult]:
    """Scrape multiple URLs with default configuration.

    Args:
        urls: List of URLs to scrape
        config: Optional scraping configuration
        extraction_strategy: Optional extraction strategy

    Returns:
        List of ScrapingResult objects
    """
    wrapper = Crawl4AIWrapper(config or ScrapingConfig())
    async with wrapper:
        return await wrapper.scrape_urls(urls, extraction_strategy)


def create_simple_config(**kwargs) -> ScrapingConfig:
    """Create a ScrapingConfig with common customizations.

    Args:
        **kwargs: Configuration parameters to override

    Returns:
        ScrapingConfig instance
    """
    defaults = {
        'max_concurrent': 3,
        'delay_between_requests': 1.0,
        'timeout': 30,
        'verbose': False,
    }
    defaults.update(kwargs)
    return ScrapingConfig(**defaults)