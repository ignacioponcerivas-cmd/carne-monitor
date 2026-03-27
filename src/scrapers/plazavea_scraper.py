import logging
import json
from typing import List

from playwright.sync_api import Page

from src.models.product import Product
from src.scrapers.base_scraper import BaseScraper
from src.utils.helpers import parse_unit, price_per_kg
from src.utils.keyword_filter import is_relevant

logger = logging.getLogger(__name__)

_PAGE_SIZE = 49


class PlazaVeaScraper(BaseScraper):
    """
    Scraper para Plaza Vea — usa la API REST VTEX interna.
    No requiere parsear HTML; obtiene JSON directamente desde el browser.
    """

    def scrape_all(self) -> List[Product]:
        """Override para usar una sola instancia de browser para todas las categorías."""
        all_products: List[Product] = []
        from playwright.sync_api import sync_playwright

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
            # Cargar la home para establecer cookies/sesión
            try:
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(2000)
            except Exception:
                pass

            for category, query in self.categories.items():
                if self._stop_event and self._stop_event.is_set():
                    break
                logger.info(f"[Plaza Vea] Scraping: {category}")
                if self._progress_callback:
                    self._progress_callback(self.site_name, category, 0, "running")
                try:
                    products = self._fetch_category(page, category, query)
                    logger.info(f"[Plaza Vea] {category}: {len(products)} productos")
                    all_products.extend(products)
                    if self._progress_callback:
                        self._progress_callback(self.site_name, category, len(products), "done")
                except Exception as exc:
                    logger.error(f"[Plaza Vea] Error en {category}: {exc}")
                    if self._progress_callback:
                        self._progress_callback(self.site_name, category, 0, "error")
                import time; time.sleep(self.delay)
            browser.close()
        return all_products

    def _fetch_category(self, page: Page, category: str, query: str) -> List[Product]:
        products: List[Product] = []
        offset = 0

        while True:
            api_url = (
                f"/api/catalog_system/pub/products/search/{query}"
                f"?_from={offset}&_to={offset + _PAGE_SIZE - 1}"
            )
            try:
                raw = page.evaluate(f"""async () => {{
                    const r = await fetch("{api_url}");
                    if (!r.ok) return null;
                    return await r.json();
                }}""")
            except Exception as exc:
                logger.warning(f"[Plaza Vea] API fetch error: {exc}")
                break

            if not raw:
                break

            for item in raw:
                try:
                    name  = item.get("productName", "")
                    link  = item.get("linkText", "")
                    url_p = f"{self.base_url}/{link}/p"

                    vtex_item = (item.get("items") or [{}])[0]
                    seller    = (vtex_item.get("sellers") or [{}])[0]
                    offer     = seller.get("commertialOffer", {})
                    price     = offer.get("Price") or offer.get("ListPrice")
                    avail     = offer.get("AvailableQuantity", 0)

                    raw_unit = vtex_item.get("measurementUnit", "un")
                    unit     = parse_unit(raw_unit)
                    img_list = vtex_item.get("images", [])
                    image_url = img_list[0].get("imageUrl") if img_list else None

                    if not name or not price:
                        continue
                    if not is_relevant(name, category):
                        logger.debug(f"[Plaza Vea] Filtrado: '{name}'")
                        continue

                    ppkg = price_per_kg(price, unit) if price else None
                    products.append(Product(
                        name=name, price=round(price, 2), unit=unit, category=category,
                        site=self.site_name, url=url_p, image_url=image_url,
                        price_per_kg=ppkg, in_stock=(avail > 0),
                    ))
                except Exception as exc:
                    logger.debug(f"[Plaza Vea] Error parseando item: {exc}")

            if len(raw) < _PAGE_SIZE:
                break
            offset += _PAGE_SIZE

        return products

    # Not used but required by ABC
    def scrape_category(self, page: Page, category: str, path: str) -> List[Product]:
        return self._fetch_category(page, category, path)
