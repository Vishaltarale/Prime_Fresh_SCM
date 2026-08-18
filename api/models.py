from datetime import datetime
from mongoengine import Document, StringField, EmailField, DateTimeField
from django.contrib.auth.hashers import make_password, check_password

STAFF_ROLES = ('Admin', 'Inventory Officer', 'Warehouse Manager')
EXTERNAL_ROLES = ('Customer', 'Supplier', 'Farmer')
ROLE_CHOICES = STAFF_ROLES + EXTERNAL_ROLES


class User(Document):
    """Consolidated auth user for the new API (replaces mysite.admin1 and Users.User1)."""

    full_name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    phone = StringField()
    password = StringField(required=True)  # stores a hashed password
    role = StringField(required=True, choices=ROLE_CHOICES, default='Inventory Officer')
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'api_users',
        'strict': False,
    }

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # DRF permission classes (e.g. IsAuthenticated) check these attributes.
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
