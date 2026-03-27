import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.product import Product


class TestProduct:
    def test_to_dict_has_all_fields(self):
        p = Product(
            name="Pollo entero",
            price=12.90,
            unit="kg",
            category="pollo",
            site="Wong",
            url="https://wong.pe/pollo",
        )
        d = p.to_dict()
        assert d["name"] == "Pollo entero"
        assert d["price"] == 12.90
        assert d["in_stock"] is True
        assert "scraped_at" in d

    def test_from_dict_roundtrip(self):
        p = Product(
            name="Huevo rosado",
            price=8.50,
            unit="docena",
            category="huevo",
            site="Metro",
            url="https://metro.pe/huevo",
        )
        p2 = Product.from_dict(p.to_dict())
        assert p2.name == p.name
        assert p2.price == p.price
