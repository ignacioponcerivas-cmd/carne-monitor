import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.utils.helpers import parse_price, parse_unit, price_per_kg


class TestParsePrice:
    def test_soles_format(self):
        assert parse_price("S/ 12.90") == 12.90

    def test_soles_dot_format(self):
        assert parse_price("S/. 5.50") == 5.50

    def test_integer_price(self):
        assert parse_price("S/ 8") == 8.0

    def test_price_with_text(self):
        assert parse_price("S/ 23.90 x kg") == 23.90

    def test_empty_string(self):
        assert parse_price("") is None

    def test_none(self):
        assert parse_price(None) is None


class TestParseUnit:
    def test_kg(self):
        assert parse_unit("x Kg") == "kg"

    def test_gramos(self):
        assert parse_unit("500 gr") == "g"

    def test_unidad(self):
        assert parse_unit("Unidad") == "und"

    def test_docena(self):
        assert parse_unit("docena") == "docena"

    def test_pack(self):
        assert parse_unit("Pack x 6") == "pack"


class TestPricePerKg:
    def test_already_kg(self):
        assert price_per_kg(20.0, "kg") == 20.0

    def test_grams(self):
        assert price_per_kg(10.0, "g", 500) == 20.0

    def test_und_returns_none(self):
        assert price_per_kg(5.0, "und") is None
