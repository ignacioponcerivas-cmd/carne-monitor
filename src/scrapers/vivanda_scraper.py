import logging
from typing import List

from playwright.sync_api import Page

from src.models.product import Product
from src.scrapers.base_scraper import BaseScraper
from src.utils.helpers import parse_price, parse_unit, price_per_kg

logger = logging.getLogger(__name__)


class VivandaScraper(BaseScraper):
    """Scraper para Vivanda (vivanda.com.pe) — motor VTEX."""

    def scrape_category(self, page: Page, category: str, path: str) -> List[Product]:
        url = self.base_url + path
        products: List[Product] = []

        if not self._navigate(page, url):
            return products

        try:
            page.wait_for_selector(".vtex-product-summary-2-x-container", timeout=15000)
        except Exception:
            logger.warning(f"[Vivanda] No se encontraron productos en {url}")
            return products

        items = page.query_selector_all(".vtex-product-summary-2-x-container")
        for item in items:
            try:
                name_el = item.query_selector(".vtex-product-summary-2-x-productBrand")
                price_el = item.query_selector(".vtex-product-price-1-x-sellingPriceValue")
                unit_el = item.query_selector(".vtex-product-summary-2-x-quantityStockKeepingUnit")
                link_el = item.query_selector("a")
                img_el = item.query_selector("img")

                name = name_el.inner_text().strip() if name_el else "Sin nombre"
                raw_price = price_el.inner_text().strip() if price_el else ""
                raw_unit = unit_el.inner_text().strip() if unit_el else "und"
                url_product = self.base_url + link_el.get_attribute("href") if link_el else url
                image_url = img_el.get_attribute("src") if img_el else None

                price = parse_price(raw_price)
                unit = parse_unit(raw_unit)
                ppkg = price_per_kg(price, unit) if price else None

                if name and price:
                    products.append(
                        Product(
                            name=name,
                            price=price,
                            unit=unit,
                            category=category,
                            site=self.site_name,
                            url=url_product,
                            image_url=image_url,
                            price_per_kg=ppkg,
                        )
                    )
            except Exception as exc:
                logger.debug(f"[Vivanda] Error parseando item: {exc}")

        return products
