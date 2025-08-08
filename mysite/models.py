from django.db import models # used to verify the supplier in the SCM system
from mongoengine import Document, StringField, IntField, FloatField, DateField, EmailField ,BooleanField

class Student(Document):
    name = StringField(required=True)
    age = IntField()

    meta = {
        'collection': 'practice'  
    }

class admin1(Document):
    username = StringField(required=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)

    meta = {
        'collection': 'admin1'  
    }

class FruitInventory(Document):
    product_name = StringField(required=True, choices=["Apple", "Orange"])
    batch_id = StringField(required=True, unique=True)
    quantity_kg = FloatField(required=True)
    unit_price = FloatField(required=True)
    arrival_date = DateField()
    expiry_date = DateField()
    storage_location = StringField()
    status = StringField(choices=["Available", "Low Stock", "Out of Stock"])
    quality_grade = StringField(choices=["A", "B", "C"])

    meta = {
        'collection': 'products'  
    }

class Employee(Document):
    full_name = StringField(required=True, max_length=100)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True, max_length=15)
    role = StringField(required=True, choices=['Admin', 'Inventory Officer', 'Warehouse Manager'])
    joining_date = DateField(required=True)
    address = StringField()

    meta = {
        'collection': 'employees',
        'ordering': ['-joining_date']
    }

    def __str__(self):
        return f"{self.full_name} ({self.role})"

#FARMER
class Farmer(Document):
    full_name = StringField(required=True, max_length=100)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True, max_length=15)
    address = StringField(required=True)
    village = StringField(required=True)
    district = StringField(required=True)
    state = StringField(required=True)
    registration_date = DateField(required=True)
    verified = BooleanField(default=False)  # SCM use: mark farmer as verified supplier

    meta = {
        'collection': 'farmers',
    }

    def __str__(self):
        return f"{self.full_name} ({self.village}, {self.district})"
    
#SUPPLIER
class Supplier(Document):
    supplier_name = StringField(required=True, max_length=100)
    company_name = StringField(required=True, max_length=100)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True, max_length=15)
    address = StringField(required=True)
    state = StringField(required=True)
    district = StringField(required=True)
    registration_date = DateField(required=True)
    verified = BooleanField(default=False)  # used to verify the supplier in the SCM system

    meta = {
        'collection': 'suppliers',
        'ordering': ['-registration_date']
    }

    def __str__(self):
        return f"{self.supplier_name} - {self.company_name}"

#Customer
class Customer(Document):
    full_name = StringField(required=True, max_length=100)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True, max_length=15)
    address = StringField(required=True)
    city = StringField(required=True)
    state = StringField(required=True)
    registration_date = DateField(required=True)

    meta = {
        'collection': 'customers',
        'ordering': ['-registration_date']
    }

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"