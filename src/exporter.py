import json
import logging
import os
from datetime import datetime
from typing import List

import pandas as pd

from src.models.product import Product

logger = logging.getLogger(__name__)


def export_csv(products: List[Product], output_dir: str = "data") -> str:
    """Export products to a timestamped CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"productos_{timestamp}.csv")
    df = pd.DataFrame([p.to_dict() for p in products])
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"CSV exportado: {path} ({len(products)} productos)")
    return path


def export_json(products: List[Product], output_dir: str = "data") -> str:
    """Export products to a timestamped JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"productos_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in products], f, ensure_ascii=False, indent=2)
    logger.info(f"JSON exportado: {path} ({len(products)} productos)")
    return path


def print_summary(products: List[Product]) -> None:
    """Print a summary table grouped by site and category."""
    if not products:
        print("No se encontraron productos.")
        return

    df = pd.DataFrame([p.to_dict() for p in products])
    print("\n" + "=" * 60)
    print(f"RESUMEN: {len(products)} productos encontrados")
    print("=" * 60)

    summary = (
        df.groupby(["site", "category"])
        .agg(total=("name", "count"), precio_min=("price", "min"), precio_max=("price", "max"))
        .reset_index()
    )
    print(summary.to_string(index=False))
    print("=" * 60 + "\n")
