from mongoengine import Document, StringField

class OfficeLocation(Document):
    office_name = StringField(required=True)
    address = StringField(required=True)
    city = StringField(required=True)
    state = StringField(required=True)
    pincode = StringField(required=True)
    status = StringField(required=True, choices=['Pending', 'Approve'], default='Pending')

    meta = {'collection': 'office_locations'}

class Warehouse(Document):
    warehouse_name = StringField(required=True, unique=True)
    address = StringField(required=True)
    city = StringField(required=True)
    state = StringField(required=True)
    pincode = StringField(required=True)
    status = StringField(required=True, choices=['Pending', 'Approve'], default='Pending')

    meta = {
        'collection': 'warehouses',
        'ordering': ['warehouse_name']
    }

    def __str__(self):
        return self.warehouse_name