from mongoengine import (
    Document, EmbeddedDocument, StringField, ReferenceField, FloatField,
    IntField, DateTimeField, ListField, EmbeddedDocumentField,
)
from datetime import datetime
from UOM.models import UOM

class Category(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    meta = {'collection': 'categories'}

    def __str__(self):
        return self.name


class Subcategory(Document):
    name = StringField(required=True)
    category = ReferenceField(Category, required=True)

    meta = {'collection': 'subcategories'}

    def __str__(self):
        return f"{self.name} ({self.category.name})"

from Location.models import Warehouse
from mysite.models import Supplier,Farmer


class WarehouseStock(EmbeddedDocument):
    """
    One product can be received into several warehouses, at different
    quantities and different landed costs (a second purchase might come in
    cheaper/pricier than the first) — so stock is tracked per warehouse
    instead of as a single scalar on Product. Only GRNConfirmView writes to
    this (see api/views.py); nothing else should touch quantity_available.
    """
    warehouse = ReferenceField(Warehouse, required=True)
    quantity_available = IntField(default=0, min_value=0)
    # Cost this product actually landed at in this warehouse (from the last
    # confirmed GRN there) — distinct from Product.price_per_unit, which is
    # just the catalog/reference price used while it's still a PO line item.
    price_per_unit = FloatField(required=False)


class Product(Document):
    name = StringField(required=True)
    sku = StringField(required=True, unique=True)  # stock keeping unit
    category = ReferenceField(Category, required=True)
    subcategory = ReferenceField(Subcategory, required=True)
    uom = ReferenceField(UOM, required=True)  # Example: KG, LTR, etc. (or link to UOM model)
    # Reference/catalog price only — used for PO planning before anything is
    # ever received. Actual per-warehouse landed cost lives in stock[].price_per_unit.
    price_per_unit = FloatField(required=True)
    # Per-warehouse quantities — see WarehouseStock. A product created fresh
    # (before any GRN) has an empty list: it exists nowhere yet.
    stock = ListField(EmbeddedDocumentField(WarehouseStock))
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    supplier = ReferenceField(Supplier, required=False)
    farmer = ReferenceField(Farmer, required=False)

    meta = {'collection': 'products', 'strict': False}

    def get_stock(self, warehouse):
        """The WarehouseStock line for a given warehouse, or None if never received there."""
        if not warehouse:
            return None
        for line in self.stock:
            if line.warehouse and line.warehouse.id == warehouse.id:
                return line
        return None

    def receive_stock(self, warehouse, quantity, unit_price=None):
        """Adds received quantity to this warehouse's line, creating it if needed. Does not save()."""
        line = self.get_stock(warehouse)
        if not line:
            line = WarehouseStock(warehouse=warehouse, quantity_available=0)
            self.stock.append(line)
        line.quantity_available += quantity
        if unit_price is not None:
            line.price_per_unit = unit_price
        return line

    @property
    def total_quantity(self):
        return sum(line.quantity_available for line in self.stock)

    def __str__(self):
        return f"{self.name} ({self.sku})"
