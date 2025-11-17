from mongoengine import Document, StringField, ReferenceField, FloatField, IntField, DateTimeField,ListField,EmbeddedDocumentField,EmbeddedDocument
from datetime import datetime
from UOM.models import UOM
from Location.models import Warehouse
from mysite.models import Supplier,Farmer

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
    
class main_product(Document):
    name = StringField(required=True)
    category = ReferenceField(Category, required=True)
    sku = StringField(required=True, unique=True)
    
    meta = {
        "collection": "main_product"
    }
    
class ProductItems(EmbeddedDocument):
    product_name = StringField(required=True)
    sku = StringField(required=True)  # removed unique=True (not valid for embedded)
    category = ReferenceField(Category, required=True)
    subcategory = ReferenceField(Subcategory, required=True)
    quantity = IntField(required=True)
    price = FloatField(required=True)
    uom = StringField(required=True)
    warehouse = ReferenceField(Warehouse)
    description = StringField()

class Product(Document):
    warehouse = ReferenceField(Warehouse)
    created_at = DateTimeField(default=datetime.utcnow)
    supplier = ReferenceField(Supplier, required=False)
    farmer = ReferenceField(Farmer, required=False)
    items = ListField(EmbeddedDocumentField(ProductItems))
    total_amount = FloatField()

    meta = {'collection': 'Products'}

    def __str__(self):
        return f"{self.name} ({self.sku})"

