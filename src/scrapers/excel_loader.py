"""Carga los productos propios de Fresqui desde el Excel de precios."""
import logging
import re
from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.models.product import Product

logger = logging.getLogger(__name__)

EXCEL_PATH = Path(__file__).parent.parent.parent / "docs" / "excel pesos.xlsx"

CAT_MAP = {
    "RES":         "res",
    "RES PREMIUM": "res",
    "POLLO":       "pollo",
    "CERDO":       "cerdo",
    "HUEVOS":      "huevos",
    "PROCESADOS":  "embutidos",
}


def _parse_unit(presentacion: str) -> str:
    if not presentacion or pd.isna(presentacion):
        return "und"
    p = str(presentacion).lower()
    if "kg" in p:
        return "kg"
    if "gr" in p:
        return "g"
    # Caja x30, Caja x15, Caja x4…
    m = re.search(r"x\s*(\d+)", p)
    if m:
        return f"x{m.group(1)}"
    return "und"


def _clean_name(raw: str) -> str:
    """Remove PREMIUM/ARG/USA suffixes and extra spaces."""
    name = str(raw).strip()
    name = re.sub(r"\s*(PREMIUM|ARG|USA)\s*", " ", name, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", name).strip()


def load_fresqui_products() -> List[Product]:
    if not EXCEL_PATH.exists():
        logger.warning(f"Excel no encontrado: {EXCEL_PATH}")
        return []

    try:
        df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    except Exception as exc:
        logger.error(f"Error leyendo Excel: {exc}")
        return []

    products: List[Product] = []

    for _, row in df.iterrows():
        raw_cat = str(row.get("Cat.", "")).strip().upper()
        category = CAT_MAP.get(raw_cat)
        if not category:
            continue

        raw_name = row.get("Producto")
        if pd.isna(raw_name):
            continue
        name = _clean_name(raw_name)

        # Precio de venta al público (PV pieza)
        pv_pieza = row.get("PV pieza")
        pv_kg    = row.get("PV/kg")
        costo    = row.get("Costo pieza")
        margen   = row.get("Margen")

        if pd.isna(pv_pieza) and pd.isna(pv_kg):
            continue

        price = round(float(pv_pieza), 2) if not pd.isna(pv_pieza) else round(float(pv_kg), 2)
        ppkg  = round(float(pv_kg), 2) if not pd.isna(pv_kg) else None
        cost  = round(float(costo), 2) if not pd.isna(costo) else None
        mgn   = round(float(margen), 4) if not pd.isna(margen) else None

        raw_unit = row.get("Presentación") or row.get("Presentaci\xf3n", "")
        unit = _parse_unit(raw_unit)

        raw_sku = row.get("ID")
        sku: Optional[str] = None
        if not pd.isna(raw_sku) and str(raw_sku) != "Fresqui":
            sku = str(int(raw_sku)) if isinstance(raw_sku, float) else str(raw_sku)

        products.append(Product(
            name=name,
            price=price,
            unit=unit,
            category=category,
            site="Fresqui",
            url="",
            sku=sku,
            price_per_kg=ppkg,
            cost_price=cost,
            margin=mgn,
        ))

    logger.info(f"Fresqui: {len(products)} productos cargados desde Excel")
    return products
