"""
Generic, config-driven CRUD over the old app's "master data" registries
(mysite.views.MODEL_MAP / list_entity / edit_entity_form) — Employee, Farmer,
Supplier, Customer, Warehouse. Each shares the same shape (a flat
document, some scalar fields, no cross-entity relationships), so one
parameterized API + one parameterized React page covers all five instead of
duplicating a CRUD module five times.

Product/Category/Subcategory/UOM are intentionally excluded here — they carry
foreign keys (category, subcategory, uom, warehouse, supplier/farmer) that need
real dropdowns, not a generic text-field form, so they get their own module.

Office was removed (data migrated into Warehouse) — the two models were
functionally identical (same fields, no distinct relationships to anything
else in the system) and kept as a single registry to avoid the duplication.
"""
from datetime import datetime, date

from mysite.models import Employee, Farmer, Supplier, Customer
from Location.models import Warehouse

FIELD_TEXT = 'text'
FIELD_EMAIL = 'email'
FIELD_DATE = 'date'
FIELD_SELECT = 'select'
FIELD_TEXTAREA = 'textarea'
FIELD_BOOL = 'bool'

ENTITY_REGISTRY = {
    'employee': {
        'label': 'Employees',
        'model': Employee,
        'search_fields': ['full_name', 'email', 'phone'],
        'fields': [
            {'name': 'full_name', 'label': 'Full Name', 'type': FIELD_TEXT, 'required': True},
            {'name': 'email', 'label': 'Email', 'type': FIELD_EMAIL, 'required': True},
            {'name': 'phone', 'label': 'Phone', 'type': FIELD_TEXT, 'required': True},
            {'name': 'role', 'label': 'Role', 'type': FIELD_SELECT, 'required': True,
             'choices': ['Admin', 'Inventory Officer', 'Warehouse Manager']},
            {'name': 'joining_date', 'label': 'Joining Date', 'type': FIELD_DATE, 'required': True},
            {'name': 'address', 'label': 'Address', 'type': FIELD_TEXTAREA, 'required': True},
        ],
    },
    'farmer': {
        'label': 'Farmers',
        'model': Farmer,
        'search_fields': ['full_name', 'email', 'phone', 'village'],
        'fields': [
            {'name': 'full_name', 'label': 'Full Name', 'type': FIELD_TEXT, 'required': True},
            {'name': 'email', 'label': 'Email', 'type': FIELD_EMAIL, 'required': True},
            {'name': 'phone', 'label': 'Phone', 'type': FIELD_TEXT, 'required': True},
            {'name': 'address', 'label': 'Address', 'type': FIELD_TEXTAREA, 'required': True},
            {'name': 'village', 'label': 'Village', 'type': FIELD_TEXT, 'required': True},
            {'name': 'district', 'label': 'District', 'type': FIELD_TEXT, 'required': True},
            {'name': 'state', 'label': 'State', 'type': FIELD_TEXT, 'required': True},
            {'name': 'registration_date', 'label': 'Registration Date', 'type': FIELD_DATE, 'required': True},
            {'name': 'verified', 'label': 'Verified', 'type': FIELD_BOOL, 'required': False},
        ],
    },
    'supplier': {
        'label': 'Suppliers',
        'model': Supplier,
        'search_fields': ['supplier_name', 'company_name', 'email', 'phone'],
        'fields': [
            {'name': 'supplier_name', 'label': 'Supplier Name', 'type': FIELD_TEXT, 'required': True},
            {'name': 'company_name', 'label': 'Company Name', 'type': FIELD_TEXT, 'required': True},
            {'name': 'email', 'label': 'Email', 'type': FIELD_EMAIL, 'required': True},
            {'name': 'phone', 'label': 'Phone', 'type': FIELD_TEXT, 'required': True},
            {'name': 'address', 'label': 'Address', 'type': FIELD_TEXTAREA, 'required': True},
            {'name': 'state', 'label': 'State', 'type': FIELD_TEXT, 'required': True},
            {'name': 'district', 'label': 'District', 'type': FIELD_TEXT, 'required': True},
            {'name': 'registration_date', 'label': 'Registration Date', 'type': FIELD_DATE, 'required': True},
            {'name': 'verified', 'label': 'Verified', 'type': FIELD_BOOL, 'required': False},
        ],
    },
    'customer': {
        'label': 'Customers',
        'model': Customer,
        'search_fields': ['full_name', 'email', 'phone', 'city'],
        'fields': [
            {'name': 'full_name', 'label': 'Full Name', 'type': FIELD_TEXT, 'required': True},
            {'name': 'email', 'label': 'Email', 'type': FIELD_EMAIL, 'required': True},
            {'name': 'phone', 'label': 'Phone', 'type': FIELD_TEXT, 'required': True},
            {'name': 'address', 'label': 'Address', 'type': FIELD_TEXTAREA, 'required': True},
            {'name': 'city', 'label': 'City', 'type': FIELD_TEXT, 'required': True},
            {'name': 'state', 'label': 'State', 'type': FIELD_TEXT, 'required': True},
            {'name': 'registration_date', 'label': 'Registration Date', 'type': FIELD_DATE, 'required': True},
        ],
    },
    'warehouse': {
        'label': 'Warehouses',
        'model': Warehouse,
        'search_fields': ['warehouse_name', 'city'],
        'fields': [
            {'name': 'warehouse_name', 'label': 'Warehouse Name', 'type': FIELD_TEXT, 'required': True},
            {'name': 'address', 'label': 'Address', 'type': FIELD_TEXTAREA, 'required': True},
            {'name': 'city', 'label': 'City', 'type': FIELD_TEXT, 'required': True},
            {'name': 'state', 'label': 'State', 'type': FIELD_TEXT, 'required': True},
            {'name': 'pincode', 'label': 'Pincode', 'type': FIELD_TEXT, 'required': True},
        ],
    },
}


def serialize_instance(instance, fields):
    data = {'id': str(instance.id)}
    for f in fields:
        value = getattr(instance, f['name'], None)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        data[f['name']] = value
    return data


def coerce_value(raw_value, field_type):
    if field_type == FIELD_DATE and isinstance(raw_value, str) and raw_value:
        return datetime.strptime(raw_value, '%Y-%m-%d')
    if field_type == FIELD_BOOL:
        return bool(raw_value) if not isinstance(raw_value, str) else raw_value.lower() in ('true', '1', 'yes')
    return raw_value


def validate_and_coerce(payload, fields, partial=False):
    """Returns (cleaned_data, errors). errors is a dict of field -> message."""
    errors = {}
    cleaned = {}
    for f in fields:
        name = f['name']
        if name not in payload:
            if f['required'] and not partial:
                errors[name] = 'This field is required.'
            continue
        raw = payload.get(name)
        if f['required'] and (raw is None or raw == ''):
            errors[name] = 'This field is required.'
            continue
        cleaned[name] = coerce_value(raw, f['type'])
    return cleaned, errors
