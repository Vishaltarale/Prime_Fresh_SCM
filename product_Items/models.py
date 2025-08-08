from mongoengine import Document, StringField, ReferenceField, FloatField, IntField, DateTimeField
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
class Product(Document):
    name = StringField(required=True)
    sku = StringField(required=True, unique=True)  # stock keeping unit
    category = ReferenceField(Category, required=True)
    subcategory = ReferenceField(Subcategory, required=True)
    uom = ReferenceField(UOM, required=True)  # Example: KG, LTR, etc. (or link to UOM model)
    warehouse = ReferenceField(Warehouse)
    price_per_unit = FloatField(required=True)
    quantity_available = IntField(default=0)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    supplier = ReferenceField(Supplier, required=False)
    farmer = ReferenceField(Farmer, required=False)

    meta = {'collection': 'products'}

    def __str__(self):
        return f"{self.name} ({self.sku})"
