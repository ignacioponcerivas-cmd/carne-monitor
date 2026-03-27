"""Thread-safe scraper runner que emite eventos de progreso a los WebSocket listeners."""
import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.product import Product
from src.scrapers import SCRAPER_MAP
from src.scrapers.excel_loader import load_fresqui_products
from src.utils.product_matcher import build_fresqui_index, is_competitor_match

logger = logging.getLogger(__name__)


class ScraperRunner:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._products: List[Product] = []
        self._fresqui: List[Product] = []          # siempre disponibles
        self._status: Dict[str, Any] = {
            "state": "idle",
            "progress": {},
            "started_at": None,
            "finished_at": None,
            "sites": [],
            "categories": [],
        }
        self._listeners: List[asyncio.Queue] = []
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Cargar Fresqui al iniciar (sin browser, es instantáneo)
        self._fresqui = load_fresqui_products()
        self._fresqui_index = build_fresqui_index(self._fresqui)

    # ------------------------------------------------------------------ #
    # WebSocket listener management
    # ------------------------------------------------------------------ #
    def add_listener(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._listeners.append(queue)

    def remove_listener(self, queue: asyncio.Queue) -> None:
        with self._lock:
            if queue in self._listeners:
                self._listeners.remove(queue)

    def _emit(self, event: dict) -> None:
        msg = json.dumps(event, ensure_ascii=False)
        if self._loop and not self._loop.is_closed():
            for q in list(self._listeners):
                asyncio.run_coroutine_threadsafe(q.put(msg), self._loop)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_status(self) -> dict:
        with self._lock:
            return {
                **self._status,
                "products_count": len(self._products) + len(self._fresqui),
                "is_running": bool(self._thread and self._thread.is_alive()),
            }

    def get_products(self) -> List[dict]:
        """
        Devuelve: todos los productos Fresqui + solo los competidores
        que coincidan con algún producto Fresqui (misma categoría + keyword).
        """
        with self._lock:
            matched = [
                p for p in self._products
                if is_competitor_match(p, self._fresqui_index)
            ]
            return [p.to_dict() for p in self._fresqui + matched]

    def reload_fresqui(self) -> int:
        """Recarga el Excel y reconstruye el índice de matching."""
        self._fresqui = load_fresqui_products()
        self._fresqui_index = build_fresqui_index(self._fresqui)
        return len(self._fresqui)

    def start(
        self,
        config: dict,
        sites: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        headless: bool = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> bool:
        if self._thread and self._thread.is_alive():
            return False

        self._loop = loop
        self._stop_event.clear()
        self._products = []         # limpiar scrapeados anteriores, Fresqui se mantiene

        target_sites      = sites      or [k for k, v in config["sites"].items() if v.get("enabled")]
        target_categories = categories or config["categories"]

        progress: Dict[str, Dict] = {
            site: {cat: {"state": "pending", "count": 0} for cat in target_categories}
            for site in target_sites
        }

        with self._lock:
            self._status = {
                "state": "running",
                "progress": progress,
                "started_at": datetime.now().isoformat(),
                "finished_at": None,
                "sites": target_sites,
                "categories": target_categories,
            }

        self._thread = threading.Thread(
            target=self._run,
            args=(config, target_sites, target_categories, headless),
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()

    # ------------------------------------------------------------------ #
    # Internal scraping loop
    # ------------------------------------------------------------------ #
    def _run(self, config: dict, sites: List[str], categories: List[str], headless: bool) -> None:
        scraping_cfg = config["scraping"]

        for site_key in sites:
            if self._stop_event.is_set():
                break

            site_cfg = dict(config["sites"][site_key])
            site_cfg["categories"] = {k: v for k, v in site_cfg["categories"].items() if k in categories}

            scraper_cls = SCRAPER_MAP.get(site_key)
            if not scraper_cls:
                logger.warning(f"No scraper for: {site_key}")
                continue

            self._emit({"type": "site_start", "site": site_key, "name": site_cfg["name"]})
            logger.info(f"Starting scraper: {site_cfg['name']}")

            scraper = scraper_cls(
                site_config=site_cfg,
                headless=headless,
                delay=scraping_cfg["delay_between_requests"],
            )
            scraper._stop_event = self._stop_event
            scraper._progress_callback = self._make_callback(site_key)

            try:
                products = scraper.scrape_all()
                with self._lock:
                    self._products.extend(products)
                self._emit({"type": "site_done", "site": site_key, "count": len(products)})
            except Exception as exc:
                logger.error(f"Error scraping {site_key}: {exc}")
                self._emit({"type": "site_error", "site": site_key, "error": str(exc)})

        final_state = "stopped" if self._stop_event.is_set() else "done"
        with self._lock:
            self._status["state"] = final_state
            self._status["finished_at"] = datetime.now().isoformat()
            total = len(self._products) + len(self._fresqui)

        self._emit({"type": "finished", "state": final_state, "total": total})

    def _make_callback(self, site_key: str):
        """Returns a progress callback bound to a specific site_key."""
        def callback(site_name: str, category: str, count: int, state: str) -> None:
            with self._lock:
                site_data = self._status["progress"].get(site_key, {})
                if category in site_data:
                    site_data[category] = {"state": state, "count": count}
            self._emit({"type": "progress", "site": site_name, "category": category,
                        "count": count, "state": state})
        return callback
