import json
from app.config import CATALOG_PATH
from app.models import Product

_catalog_cache = None


def load_catalog():
    global _catalog_cache
    if _catalog_cache is None:
        with open(CATALOG_PATH, "r") as f:
            raw = json.load(f)
        _catalog_cache = [Product(**item) for item in raw]
    return _catalog_cache


def list_products():
    return [p.model_dump() for p in load_catalog()]


def get_product(product_id):
    for p in load_catalog():
        if p.id == product_id:
            return p
    return None
