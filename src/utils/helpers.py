import re
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse_price(raw: str) -> Optional[float]:
    """Extract numeric price from strings like 'S/ 12.90', 'S/. 5.50 x kg'."""
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.,]", "", raw).replace(",", ".")
    # Handle cases like "12.90.00" -> keep last two decimals
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def parse_unit(raw: str) -> str:
    """Normalize unit strings."""
    raw_lower = raw.lower()
    if "kg" in raw_lower:
        return "kg"
    if "gr" in raw_lower or "g" in raw_lower:
        return "g"
    if "und" in raw_lower or "unidad" in raw_lower:
        return "und"
    if "docena" in raw_lower:
        return "docena"
    if "pack" in raw_lower or "paq" in raw_lower:
        return "pack"
    return raw.strip()


def price_per_kg(price: float, unit: str, quantity: float = 1.0) -> Optional[float]:
    """Compute price per kg if possible."""
    if unit == "kg":
        return round(price / quantity, 2) if quantity else price
    if unit == "g":
        return round(price / (quantity / 1000), 2) if quantity else None
    return None


def retry_with_delay(func, retries: int = 3, delay: float = 2.0):
    """Simple retry wrapper."""
    for attempt in range(retries):
        try:
            return func()
        except Exception as exc:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed: {exc}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
