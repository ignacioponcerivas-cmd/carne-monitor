"""Filtra productos usando las keywords del Excel y config/keywords.json."""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "keywords.json"
_keywords: Optional[dict] = None


def _load() -> dict:
    global _keywords
    if _keywords is None:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _keywords = json.load(f)
    return _keywords


def is_relevant(name: str, category: str) -> bool:
    """
    Devuelve True si el nombre del producto pertenece a la categoría dada
    y no está en la lista de exclusión global.
    """
    cfg = _load()
    name_lower = name.lower()

    # Rechazar si contiene palabra excluida globalmente
    for excl in cfg.get("global_exclude", []):
        if excl.lower() in name_lower:
            return False

    # Aceptar si contiene al menos una keyword de la categoría
    for kw in cfg.get(category, []):
        if kw.lower() in name_lower:
            return True

    return False
