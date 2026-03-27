from src.scrapers.wong_scraper import WongScraper
from src.scrapers.metro_scraper import MetroScraper
from src.scrapers.plazavea_scraper import PlazaVeaScraper

SCRAPER_MAP = {
    "wong":     WongScraper,
    "metro":    MetroScraper,
    "plazavea": PlazaVeaScraper,
}

__all__ = ["WongScraper", "MetroScraper", "PlazaVeaScraper", "SCRAPER_MAP"]
