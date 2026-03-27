"""
Matching entre productos Fresqui y competencia.
Un producto competidor es relevante si está en la misma categoría
y comparte al menos una keyword distintiva con un producto Fresqui.
"""
import re
import unicodedata
from typing import Dict, List, Set

from src.models.product import Product

# Palabras que NO aportan información de matching
_STOPWORDS: Set[str] = {
    # Gramática
    "de", "la", "el", "los", "las", "con", "sin", "por", "para", "del",
    "al", "un", "una", "y", "o", "a", "en", "que", "del", "sus",
    # Abreviaciones comunes en carnes
    "c/", "s/", "x", "xkg", "xkilo",
    # Unidades / pesos
    "kg", "gr", "g", "ml", "lt", "cc", "paq", "paquete",
    "caja", "pack", "bolsa", "bandeja", "pieza", "unidad", "und",
    # Palabras genéricas que aparecen en toda la categoría
    # (huevo/huevos se mantienen como keywords válidas para esa categoría)
    "pollo", "res", "carne", "cerdo", "porcino", "vacuno",
    "embutido", "embutidos",
    # Adjetivos genéricos
    "fresco", "fresca", "nacional", "natural", "organico",
    "especial", "simple", "clasico", "regular",
    "premium", "arg", "usa",
    # Números y marcas frecuentes
    "san", "metro", "wong", "plaza", "vea", "tottus",
}

# Frases multi-palabra que deben mantenerse juntas
_PHRASES: List[str] = [
    "baby ribs", "lomo fino", "asado de tira", "bisteck de tapa",
    "bisteck de pechuga", "filete de pechuga", "filete de pierna",
    "pierna con encuentro", "pollo entero", "chicken strips",
    "bife ancho", "bife angosto", "bife lomo", "molida de bisteck",
    "chuleta de lomo", "chuleta pierna", "lomito fino",
    "chicharron de cerdo", "chicharron pechuga",
    "bondiola de cerdo", "panceta",
]


def _normalize(text: str) -> str:
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _keywords(name: str) -> Set[str]:
    norm = _normalize(name)
    result: Set[str] = set()

    # Check multi-word phrases first
    for phrase in _PHRASES:
        if phrase in norm:
            result.add(phrase)

    # Individual words ≥ 4 chars not in stopwords
    for word in norm.split():
        if len(word) >= 4 and word not in _STOPWORDS:
            result.add(word)

    return result


def build_fresqui_index(fresqui: List[Product]) -> Dict[str, Set[str]]:
    """
    Returns {category: set_of_all_keywords} built from the Fresqui catalog.
    Used to filter competitor products.
    """
    index: Dict[str, Set[str]] = {}
    for p in fresqui:
        kws = _keywords(p.name)
        index.setdefault(p.category, set()).update(kws)
    return index


def is_competitor_match(
    product: Product,
    index: Dict[str, Set[str]],
) -> bool:
    """
    True if `product` (competitor) shares at least one keyword
    with any Fresqui product in the same category.
    """
    cat_kws = index.get(product.category)
    if not cat_kws:
        return False
    prod_kws = _keywords(product.name)
    return bool(prod_kws & cat_kws)
