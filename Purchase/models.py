from datetime import datetime
from mongoengine import (
    Document, StringField, ReferenceField, FloatField, FileField,
    IntField, DateTimeField, ListField, EmbeddedDocumentField,EmbeddedDocument
)

from UOM.models import UOM
from product_Items.models import Category, Subcategory
from Location.models import Warehouse
from mysite.models import Supplier, Farmer
 # Ensure this is an EmbeddedDocument if used here


class ProductItem(EmbeddedDocument):
    product_name = StringField(required=True)
    sku = StringField()
    category = ReferenceField(Category, required=True)
    subcategory = ReferenceField(Subcategory, required=True)
    quantity = IntField(required=True)
    price = FloatField(required=True)
    uom = StringField(required=True)
    warehouse = ReferenceField(Warehouse)
    description = StringField()
    gst_amount = FloatField(default=18.0)  # GST percentage for this product
    gst_value = FloatField(default=0.0)    # Actual GST amount for this line
    line_total = FloatField(default=0.0)   # Total for this line (quantity * price)
    subtotal = FloatField(default=0.0)  

class RFQProduct(Document):
    warehouse = ReferenceField(Warehouse)
    created_at = DateTimeField(default=datetime.utcnow)
    supplier = ReferenceField(Supplier, required=False)
    farmer = ReferenceField(Farmer, required=False)
    items = ListField(EmbeddedDocumentField(ProductItem))
    total_amount = FloatField()
    status = StringField(choices=["Pending", "Completed", "Cancelled"], default="Pending")
    created_by = StringField(required=True)

    meta = {'collection': 'RFQProducts'}    

    def __str__(self):
        return f"RFQ-{str(self.id)}"


class RFQResponse(Document):
    rfq = ReferenceField(RFQProduct, required=True, reverse_delete_rule=2)  
    sender_email = StringField(required=True)
    message = StringField()
    received_at = DateTimeField(default=datetime.utcnow)
    attachments =ListField(StringField()) 
    created_by = StringField(required=True)


    #PURCHASE ORDER MAIL
class PurchaseOrder(Document):
    rfq = ReferenceField(RFQResponse, required=False)
    supplier = ReferenceField(Supplier, required=False)
    farmer = ReferenceField(Farmer, required=False)
    warehouse = ReferenceField(Warehouse, required=False)
    items = ListField(EmbeddedDocumentField(ProductItem))
    status = StringField(choices=('Pending','Shipped','Received','Cancelled'), default='Pending')
    subtotal = FloatField(default=0.0)           # Add this field
    gst_amount = FloatField(default=0.0)         # Add this field
    total_amount = FloatField(default=0.0)       # Grand total
    created_at = DateTimeField(default=datetime.utcnow)
    received_at = DateTimeField(required=False)
    tracking_number = StringField()
    notes = StringField()
    created_by = StringField(required=True)

class GRN(Document):
    purchase_order = ReferenceField('PurchaseOrder', required=True)
    supplier = ReferenceField('Supplier', required=False)
    farmer = ReferenceField('Farmer', required=False)
    warehouse = ReferenceField('Warehouse', required=False)
    items = ListField(EmbeddedDocumentField(ProductItem))
    total_amount = FloatField()
    tracking_number = StringField()
    received_at = DateTimeField(default=datetime.utcnow)
    created_at = DateTimeField(default=datetime.utcnow)
    notes = StringField()
    created_by = StringField()  # Optional: to track user

    meta = {
        'collection': 'GRN',
        'ordering': ['-created_at']
    }