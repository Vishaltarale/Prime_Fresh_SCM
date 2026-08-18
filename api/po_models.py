"""
Purchase Order module — entirely new, no prior equivalent existed anywhere in
the app (confirmed by audit). Workflow: Draft -> Sent (emailed to supplier
with a response token) -> Awaiting Approval (supplier submitted fixed
pricing) -> Confirmed/Rejected (staff decision). A Confirmed PO then feeds
GRN creation, and GRN receipts roll up cumulative received/loss quantities
back onto the PO so a PO can span multiple partial-shipment GRNs.

Payments and refunds are modeled as one append-only history list per PO
(kind='Payment' or 'Refund') rather than the separate po_payments/po_refunds
collections sketched in the request — a single auditable log is simpler and
still gives full traceability (nothing is ever deleted, refunds are just
negative-direction entries with their own reason/actor/timestamp), and it's
the same pattern GRN/Order already use (one document, embedded history).
"""
import secrets
from datetime import datetime

from mongoengine import (
    Document, EmbeddedDocument, StringField, FloatField, IntField,
    ReferenceField, ListField, EmbeddedDocumentField, DateTimeField, BooleanField,
)

from product_Items.models import Product
from Location.models import Warehouse
from mysite.models import Supplier


class POItem(EmbeddedDocument):
    product = ReferenceField(Product, required=True)
    ordered_qty = IntField(required=True, min_value=1)
    proposed_price = FloatField(required=True, min_value=0)
    confirmed_price = FloatField(required=False)
    # Cumulative rollup from all GRNs recorded against this PO — updated
    # whenever a GRN linked to this PO is saved, so the PO always reflects
    # "how much has arrived so far" without re-summing GRNs on every read.
    received_qty = IntField(default=0)
    loss_qty = IntField(default=0)

    @property
    def remaining_qty(self):
        return max(self.ordered_qty - self.received_qty - self.loss_qty, 0)

    @property
    def line_total_confirmed(self):
        return self.ordered_qty * (self.confirmed_price or 0)

    @property
    def line_total_received(self):
        return self.received_qty * (self.confirmed_price or 0)


class PurchaseOrder(Document):
    STATUS = ('Draft', 'Sent', 'Awaiting Approval', 'Confirmed', 'Rejected')

    po_number = StringField(required=True, unique=True)
    supplier = ReferenceField(Supplier, required=True)
    warehouse = ReferenceField(Warehouse, required=True)
    items = ListField(EmbeddedDocumentField(POItem))
    status = StringField(choices=STATUS, default='Draft')

    response_token = StringField()
    notes = StringField()
    created_by = StringField()
    approved_by = StringField()

    created_at = DateTimeField(default=datetime.utcnow)
    sent_at = DateTimeField()
    responded_at = DateTimeField()
    confirmed_at = DateTimeField()

    meta = {
        'collection': 'purchase_orders',
        'ordering': ['-created_at'],
        'strict': False,
    }

    def generate_response_token(self):
        self.response_token = secrets.token_urlsafe(32)

    @property
    def proposed_total(self):
        return sum(i.ordered_qty * i.proposed_price for i in self.items)

    @property
    def confirmed_total(self):
        return sum(i.ordered_qty * (i.confirmed_price or 0) for i in self.items)

    @property
    def received_total(self):
        """What we actually owe the supplier — received qty × confirmed price, not ordered qty."""
        return sum(i.received_qty * (i.confirmed_price or 0) for i in self.items)


class POPaymentEntry(EmbeddedDocument):
    kind = StringField(choices=('Payment', 'Refund'), required=True)
    amount = FloatField(required=True, min_value=0.01)
    method = StringField()  # free-text reference/method note, e.g. "Bank transfer #123"
    reason = StringField()  # required in practice for refunds
    recorded_by = StringField()
    date = DateTimeField(default=datetime.utcnow)


class POPaymentRecord(Document):
    """One payment-tracking document per PO; the running total lives in `history`."""

    po = ReferenceField(PurchaseOrder, required=True, unique=True)
    history = ListField(EmbeddedDocumentField(POPaymentEntry))

    meta = {'collection': 'po_payments'}

    @property
    def total_amount(self):
        return self.po.received_total

    @property
    def amount_paid(self):
        paid = sum(h.amount for h in self.history if h.kind == 'Payment')
        refunded = sum(h.amount for h in self.history if h.kind == 'Refund')
        return paid - refunded

    @property
    def balance(self):
        return self.total_amount - self.amount_paid

    @property
    def status(self):
        if self.total_amount <= 0:
            return 'Unpaid'
        if self.amount_paid <= 0:
            return 'Unpaid'
        if self.amount_paid >= self.total_amount:
            return 'Fully Paid'
        return 'Partially Paid'
