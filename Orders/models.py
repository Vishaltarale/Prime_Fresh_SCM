from mongoengine import Document, StringField, DateField, FloatField, ListField, ReferenceField, EmbeddedDocument, EmbeddedDocumentField, IntField
import datetime
from Users.models import User1
from django.contrib.auth.models import User

class ProductItem(EmbeddedDocument):
    product_name = StringField(required=True)
    quantity = IntField(required=True)
    price = FloatField(required=True)
    uom = StringField(required=True) 


from Location.models import Warehouse
class Order(Document):
    customer_name = StringField(required=True)
    order_date = DateField(default=datetime.date.today)
    status = StringField(choices=["Pending", "Processing", "Completed", "Cancelled"], default="Pending")
    items = ListField(EmbeddedDocumentField(ProductItem))
    total_amount = FloatField()
    payment_status = StringField(choices=["Paid", "Unpaid"], default="Unpaid")
    delivery_address = StringField()
    created_by = StringField()
    warehouse = ReferenceField(Warehouse)
    meta = {"collection": "Orders"}
