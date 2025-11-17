from mongoengine import Document, StringField, DateField, FloatField, ListField, ReferenceField, EmbeddedDocument, EmbeddedDocumentField, IntField
import datetime
from Users.models import User1
from django.contrib.auth.models import User
from product_Items.models import Category,Subcategory
from Location.models import Warehouse

class ProductItem(EmbeddedDocument):
    product_name = StringField(required=True)
    sku = StringField(required=True)  # removed unique=True (not valid for embedded)
    category = ReferenceField(Category, required=True)
    subcategory = ReferenceField(Subcategory, required=True)
    quantity = IntField(required=True)
    price = FloatField(required=True)
    uom = StringField(required=True)

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

class TCProductItem(EmbeddedDocument):
    product_name = StringField(required=True)
    sku = StringField(required=True)
    category = ReferenceField(Category, required=True)
    subcategory = ReferenceField(Subcategory, required=True)
    quantity = IntField(required=True)
    price = FloatField(required=True)
    uom = StringField(required=True)
    gst = FloatField(required=True, default=0.0)
    total = FloatField(required=True)


class TransportChallan(Document):
    order = ReferenceField(Order, required=True)
    custoomer_name = StringField(required=True)
    delevery_address = StringField()
    warehouse = ReferenceField(Warehouse)
    orderstatus = StringField(choices=["Processing", "Created", "Cancelled"], default="Processing")
    challan_date = DateField(default=datetime.date.today)
    items = ListField(EmbeddedDocumentField(TCProductItem))
    created_by = StringField()
    transport_details = StringField()
    vehicle_number = StringField()
    driver_name = StringField()
    driver_contact = StringField()
    dispatch_date = DateField(null=True)
    transportation_bill = FloatField()  
    subtotal_amount = FloatField()
    gst_amount = FloatField()
    total_amount = FloatField()

    meta = {"collection": "TransportChallans"}

class TCResponse(Document):
    challan = ReferenceField(TransportChallan, required=True)
    customer = StringField(required=True)
    message = StringField()
    attachments = ListField(StringField())  # Store file paths or URLs
    received_at = DateField(default=datetime.date.today)
    

    meta = {"collection": "TCResponses"}

class BillItem(EmbeddedDocument):   
    product_name = StringField()
    sku = StringField()
    category = ReferenceField(Category, null=True)
    subcategory = ReferenceField(Subcategory, null=True)
    quantity = IntField(default=0)
    price = FloatField(default=0.0)
    uom = StringField()
    gst = FloatField(default=0.0)
    total = FloatField(default=0.0)


class FinalCustomerBill(Document):
    challan = ReferenceField("TransportChallan", required=True)
    response = ReferenceField("TCResponse", required=True)
    customer_name = StringField()
    delevery_address = StringField()   # ⚠️ spelling matches your code
    warehouse = ReferenceField(Warehouse)
    orderstatus = StringField(default="Created")
    bill_date = DateField()
    items = ListField(EmbeddedDocumentField(BillItem))   # ✅ critical
    created_by = StringField()
    transport_details = StringField()
    vehicle_number = StringField()
    driver_name = StringField()
    driver_contact = StringField()
    dispatch_date = DateField()
    transportation_bill = FloatField(default=0.0)
    subtotal_amount = FloatField(default=0.0)
    gst_amount = FloatField(default=0.0)
    total_amount = FloatField(default=0.0)
    created_at = DateField(default=datetime.datetime.utcnow)

    meta = {"collection": "FinalCustomerBills"}
