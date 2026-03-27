"""
Carne Scraper — Retail de carnes, pollo, cerdo y huevo en Peru
Sitios: Wong, Metro, Plaza Vea, Tottus, Vivanda
"""
import argparse
import json
import logging
import os
import sys
from typing import List

from src.models.product import Product
from src.scrapers import SCRAPER_MAP
from src.exporter import export_csv, export_json, print_summary
from src.utils.helpers import setup_logging


def load_config(config_path: str = "config/sites.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run(
    sites: List[str] | None = None,
    categories: List[str] | None = None,
    headless: bool = True,
    output_format: str = "csv",
    output_dir: str = "data",
) -> List[Product]:
    config = load_config()
    scraping_cfg = config["scraping"]
    all_products: List[Product] = []

    target_sites = sites or [k for k, v in config["sites"].items() if v.get("enabled")]
    target_categories = categories or config["categories"]

    for site_key in target_sites:
        if site_key not in config["sites"]:
            logging.warning(f"Sitio desconocido: {site_key}")
            continue

        site_cfg = config["sites"][site_key]

        # Filtrar categorías si se especificaron
        if categories:
            site_cfg = dict(site_cfg)
            site_cfg["categories"] = {
                k: v for k, v in site_cfg["categories"].items() if k in target_categories
            }

        scraper_cls = SCRAPER_MAP.get(site_key)
        if not scraper_cls:
            logging.warning(f"No hay scraper para: {site_key}")
            continue

        scraper = scraper_cls(
            site_config=site_cfg,
            headless=headless,
            delay=scraping_cfg["delay_between_requests"],
        )

        logging.info(f"Iniciando scraping: {site_cfg['name']}")
        products = scraper.scrape_all()
        all_products.extend(products)

    if all_products:
        if output_format in ("csv", "both"):
            export_csv(all_products, output_dir)
        if output_format in ("json", "both"):
            export_json(all_products, output_dir)

    print_summary(all_products)
    return all_products


def main():
    parser = argparse.ArgumentParser(
        description="Scraper de precios de carnes en retail peruano"
    )
    parser.add_argument(
        "--sites",
        nargs="+",
        choices=list(SCRAPER_MAP.keys()),
        help="Sitios a scrapear (default: todos)",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["pollo", "carne", "cerdo", "huevo"],
        help="Categorías a scrapear (default: todas)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Mostrar el navegador (útil para depurar)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "both"],
        default="csv",
        help="Formato de exportación (default: csv)",
    )
    parser.add_argument(
        "--output",
        default="data",
        help="Directorio de salida (default: data/)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    run(
        sites=args.sites,
        categories=args.categories,
        headless=not args.no_headless,
        output_format=args.format,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
