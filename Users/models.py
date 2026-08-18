from django.db import models
from mongoengine import Document, StringField, EmailField


# Create your models here.
class User1(Document):
    full_name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True)
    password = StringField(required=True)
    role = StringField(required=True, choices=['Admin', 'Inventory Officer', 'Warehouse Manager'], default='Inventory Officer')

    meta = {
        'collection': 'user1',
        'strict': False,
    }