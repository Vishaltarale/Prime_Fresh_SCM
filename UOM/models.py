from mongoengine import Document, StringField, ReferenceField, FloatField

class UOM(Document):
    name = StringField(required=True, unique=True)  # e.g., KG, LTR, BOX
    description = StringField()                     # e.g., Kilogram, Litre

    meta = {
        'collection': 'uoms'
    }

    def __str__(self):
        return self.name

class UOMConversionMatrix(Document):
    from_uom = ReferenceField(UOM, required=True)
    to_uom = ReferenceField(UOM, required=True)
    factor = FloatField(required=True)  # e.g., 1 BOX = 10 KG → factor = 10

    meta = {'collection': 'conversion_matrix'}