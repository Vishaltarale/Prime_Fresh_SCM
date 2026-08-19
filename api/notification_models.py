from datetime import datetime
from mongoengine import Document, StringField, ListField, ReferenceField, DateTimeField, BooleanField

from .models import STAFF_ROLES
from Location.models import Warehouse
from product_Items.models import Product


class Notification(Document):
    """
    A staff-facing alert — low stock, or a status change on a PO/GRN. Not
    per-user: `target_roles` says who should see it (the "purchase
    department" — Admin/Inventory Officer/Warehouse Manager), and `read_by`
    tracks which of those users have dismissed it individually, so the same
    alert can be unread for one manager and read for another.
    """
    CATEGORY = ('low_stock', 'po_status', 'grn_status', 'payment_status', 'general')
    SEVERITY = ('info', 'warning', 'critical')

    category = StringField(choices=CATEGORY, required=True, default='general')
    severity = StringField(choices=SEVERITY, default='info')
    title = StringField(required=True)
    message = StringField(required=True)
    target_roles = ListField(StringField(), default=list(STAFF_ROLES))
    read_by = ListField(StringField())  # emails of users who've read/dismissed it

    # Optional context links, used for de-duplication (low stock) and for the
    # frontend to deep-link back to the relevant screen.
    warehouse = ReferenceField(Warehouse, required=False)
    product = ReferenceField(Product, required=False)
    po_id = StringField(required=False)
    grn_id = StringField(required=False)

    # Low-stock alerts are "live" — resolved automatically once stock is
    # replenished above the threshold, instead of piling up forever.
    resolved = BooleanField(default=False)

    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'notifications',
        'ordering': ['-created_at'],
        'strict': False,
    }
