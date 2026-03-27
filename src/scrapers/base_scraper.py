import time
import logging
import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Callable

from playwright.sync_api import sync_playwright, Page

from src.models.product import Product

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all retail scrapers using Playwright."""

    def __init__(self, site_config: dict, headless: bool = True, delay: float = 2.0):
        self.site_config = site_config
        self.headless = headless
        self.delay = delay
        self.site_name = site_config["name"]
        self.base_url = site_config["base_url"]
        self.categories = site_config["categories"]
        self._stop_event: Optional[threading.Event] = None
        self._progress_callback: Optional[Callable] = None

    def scrape_all(self) -> List[Product]:
        all_products: List[Product] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="es-PE",
            )
            page = context.new_page()
            for category, path in self.categories.items():
                if self._stop_event and self._stop_event.is_set():
                    break
                logger.info(f"[{self.site_name}] Scraping: {category}")
                if self._progress_callback:
                    self._progress_callback(self.site_name, category, 0, "running")
                try:
                    products = self.scrape_category(page, category, path)
                    logger.info(f"[{self.site_name}] {category}: {len(products)} productos")
                    all_products.extend(products)
                    if self._progress_callback:
                        self._progress_callback(self.site_name, category, len(products), "done")
                except Exception as exc:
                    logger.error(f"[{self.site_name}] Error en {category}: {exc}")
                    if self._progress_callback:
                        self._progress_callback(self.site_name, category, 0, "error")
                time.sleep(self.delay)
            browser.close()
        return all_products

    @abstractmethod
    def scrape_category(self, page: Page, category: str, path: str) -> List[Product]:
        raise NotImplementedError

    def _navigate(self, page: Page, url: str, wait: str = "networkidle") -> bool:
        """Navigate and wait for full JS render."""
        try:
            page.goto(url, wait_until=wait, timeout=30000)
            # Let JS finish rendering
            page.wait_for_timeout(3000)
            # Scroll to trigger lazy-loaded products
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
            page.wait_for_timeout(2000)
            return True
        except Exception as exc:
            logger.warning(f"Navigation failed for {url}: {exc}")
            return False
