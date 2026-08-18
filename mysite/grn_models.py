from mongoengine import (
    Document, StringField, DateTimeField, FloatField,
    IntField, ReferenceField, ListField, EmbeddedDocument,
    EmbeddedDocumentField
)
from datetime import datetime
from product_Items.models import Product
from Location.models import Warehouse
from mysite.models import Supplier, Farmer
from api.po_models import PurchaseOrder


class GRNItem(EmbeddedDocument):
    """A single line item inside a GRN."""
    product      = ReferenceField(Product, required=True)
    ordered_qty  = IntField(required=True, min_value=0)
    received_qty = IntField(required=True, min_value=0)
    loss_qty     = IntField(default=0, min_value=0)
    loss_reason  = StringField(choices=('', 'Damaged', 'Short-shipped', 'Lost', 'Other'), default='')
    unit_price   = FloatField(required=True, min_value=0)
    uom          = StringField()
    remarks      = StringField()

    @property
    def line_total(self):
        return self.received_qty * self.unit_price


class GRN(Document):
    """Goods Receipt Note — records stock arriving at a warehouse."""

    GRN_STATUS = ('Draft', 'Confirmed', 'Rejected')
    SOURCE_TYPE = ('Supplier', 'Farmer')

    grn_number    = StringField(required=True, unique=True)
    grn_date      = DateTimeField(default=datetime.utcnow)
    source_type   = StringField(choices=SOURCE_TYPE, required=True)
    supplier      = ReferenceField(Supplier, required=False)
    farmer        = ReferenceField(Farmer,   required=False)
    # Required for Supplier-sourced GRNs (goods must be received against a
    # Confirmed Purchase Order); Farmer-sourced GRNs stay ad-hoc — POs were
    # never part of the farmer workflow.
    purchase_order = ReferenceField(PurchaseOrder, required=False)
    warehouse     = ReferenceField(Warehouse, required=True)
    items         = ListField(EmbeddedDocumentField(GRNItem))
    total_amount  = FloatField(default=0.0)
    status        = StringField(choices=GRN_STATUS, default='Draft')
    received_by   = StringField()   # session email of the logged-in user
    notes         = StringField()
    created_at    = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'grns',
        'ordering': ['-created_at'],
        'strict': False,
    }

    def recalculate_total(self):
        self.total_amount = sum(
            item.received_qty * item.unit_price for item in self.items
        )

    def __str__(self):
        return self.grn_number
