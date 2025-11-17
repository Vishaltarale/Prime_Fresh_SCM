from django.db import models
from mongoengine import Document, StringField, EmailField,ReferenceField


# Create your models here.
class User1(Document):
    full_name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True)
    password = StringField(required=True)
    role = StringField(choices=['Customer','Admin', 'Inventory_Manager', 'Purchase_Manager','Sales_Manager', 'Warehouse_Manager', 'Accountant'], required=True)

    meta = {
        'collection': 'user1'
    }