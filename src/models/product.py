from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    name: str
    price: float
    unit: str
    category: str
    site: str
    url: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None
    price_per_kg: Optional[float] = None
    in_stock: bool = True
    # Fresqui-only fields
    cost_price: Optional[float] = None
    margin: Optional[float] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
