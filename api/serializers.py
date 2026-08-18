import datetime

from rest_framework import serializers
from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError as MongoValidationError

from .models import User, ROLE_CHOICES
from .po_models import PurchaseOrder
from mysite.grn_models import GRN, GRNItem
from product_Items.models import Product
from Location.models import Warehouse
from mysite.models import Supplier, Farmer, Customer


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        return {
            'id': str(instance.id),
            'full_name': instance.full_name,
            'email': instance.email,
            'phone': instance.phone or '',
            'role': instance.role,
            'created_at': instance.created_at,
        }


class RegisterSerializer(serializers.Serializer):
    """
    Registering as Customer/Supplier/Farmer creates BOTH the login (api.User)
    and the matching business entity (mysite.Customer/Supplier/Farmer) in one
    step, linked by email — there's no separate foreign key, so "my orders" /
    "my deliveries" scoping later just matches on request.user.email.
    """
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, default='Inventory Officer')

    # Extra fields only required for external (Customer/Supplier/Farmer) registration.
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    village = serializers.CharField(required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)

    REQUIRED_PROFILE_FIELDS = {
        'Customer': ['address', 'city', 'state'],
        'Supplier': ['company_name', 'address', 'state', 'district'],
        'Farmer': ['address', 'village', 'district', 'state'],
    }

    def validate_email(self, value):
        if User.objects(email=value).first():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, attrs):
        required = self.REQUIRED_PROFILE_FIELDS.get(attrs.get('role'))
        if required:
            missing = [f for f in required if not attrs.get(f)]
            if missing:
                raise serializers.ValidationError({f: 'This field is required.' for f in missing})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role')
        profile_fields = {
            f: validated_data.pop(f, '')
            for f in ('address', 'city', 'state', 'district', 'village', 'company_name')
        }

        user = User(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            phone=validated_data.get('phone', ''),
            role=role,
        )
        user.set_password(password)
        user.save()

        try:
            if role == 'Customer':
                Customer(
                    full_name=user.full_name, email=user.email, phone=user.phone,
                    address=profile_fields['address'], city=profile_fields['city'], state=profile_fields['state'],
                    registration_date=datetime.datetime.utcnow(),
                ).save()
            elif role == 'Supplier':
                Supplier(
                    supplier_name=user.full_name, company_name=profile_fields['company_name'],
                    email=user.email, phone=user.phone, address=profile_fields['address'],
                    state=profile_fields['state'], district=profile_fields['district'],
                    registration_date=datetime.datetime.utcnow(), verified=False,
                ).save()
            elif role == 'Farmer':
                Farmer(
                    full_name=user.full_name, email=user.email, phone=user.phone,
                    address=profile_fields['address'], village=profile_fields['village'],
                    district=profile_fields['district'], state=profile_fields['state'],
                    registration_date=datetime.datetime.utcnow(), verified=False,
                ).save()
        except (NotUniqueError, MongoValidationError):
            # The login was created but the linked entity failed — roll back
            # the login so the account isn't left in a half-registered state.
            user.delete()
            raise serializers.ValidationError('Could not create the linked business record. Please try again.')

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = User.objects(email=attrs['email']).first()
        if not user or not user.check_password(attrs['password']):
            raise serializers.ValidationError('Invalid email or password.')
        attrs['user'] = user
        return attrs


# ── Reference lookups (read-only, feed GRN create form dropdowns) ──────────

class WarehouseSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {'id': str(instance.id), 'name': instance.warehouse_name}


class SupplierSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {'id': str(instance.id), 'name': instance.supplier_name}


class FarmerSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {'id': str(instance.id), 'name': instance.full_name}


class ProductSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {
            'id': str(instance.id),
            'name': instance.name,
            'sku': instance.sku,
            'uom': instance.uom.name if instance.uom else '',
            'price_per_unit': instance.price_per_unit,
        }


# ── GRN ───────────────────────────────────────────────────────────────────

def _get_or_404(document_cls, doc_id, field_name):
    if not doc_id:
        return None
    try:
        obj = document_cls.objects(id=doc_id).first()
    except MongoValidationError:
        obj = None
    if not obj:
        raise serializers.ValidationError({field_name: f'No such {document_cls.__name__} "{doc_id}".'})
    return obj


class GRNItemSerializer(serializers.Serializer):
    product = serializers.CharField()
    product_name = serializers.SerializerMethodField(read_only=True)
    ordered_qty = serializers.IntegerField(min_value=0)
    received_qty = serializers.IntegerField(min_value=0)
    loss_qty = serializers.IntegerField(min_value=0, required=False, default=0)
    loss_reason = serializers.CharField(required=False, allow_blank=True, default='')
    unit_price = serializers.FloatField(min_value=0)
    uom = serializers.CharField(required=False, allow_blank=True, default='')
    remarks = serializers.CharField(required=False, allow_blank=True, default='')
    line_total = serializers.SerializerMethodField(read_only=True)

    def get_product_name(self, obj):
        product = obj['product'] if isinstance(obj, dict) else obj.product
        return getattr(product, 'name', None)

    def get_line_total(self, obj):
        if isinstance(obj, dict):
            return obj.get('received_qty', 0) * obj.get('unit_price', 0)
        return obj.line_total

    def to_representation(self, instance):
        return {
            'product': str(instance.product.id),
            'product_name': instance.product.name,
            'ordered_qty': instance.ordered_qty,
            'received_qty': instance.received_qty,
            'loss_qty': instance.loss_qty,
            'loss_reason': instance.loss_reason or '',
            'unit_price': instance.unit_price,
            'uom': instance.uom or '',
            'remarks': instance.remarks or '',
            'line_total': instance.line_total,
        }


class GRNSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    grn_number = serializers.CharField(read_only=True)
    grn_date = serializers.DateTimeField(read_only=True)
    source_type = serializers.ChoiceField(choices=GRN.SOURCE_TYPE)
    supplier = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    farmer = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    purchase_order = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    warehouse = serializers.CharField()
    items = GRNItemSerializer(many=True)
    total_amount = serializers.FloatField(read_only=True)
    status = serializers.CharField(read_only=True)
    received_by = serializers.CharField(read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    created_at = serializers.DateTimeField(read_only=True)

    def validate(self, attrs):
        if attrs['source_type'] == 'Supplier':
            # Supplier-sourced GRNs must be received against a Confirmed PO —
            # Farmer-sourced GRNs stay ad-hoc (no PO concept in that workflow).
            if not attrs.get('purchase_order'):
                raise serializers.ValidationError({'purchase_order': 'A Confirmed Purchase Order is required for supplier receipts.'})
            po = PurchaseOrder.objects(id=attrs['purchase_order']).first()
            if not po:
                raise serializers.ValidationError({'purchase_order': 'Purchase Order not found.'})
            if po.status != 'Confirmed':
                raise serializers.ValidationError({'purchase_order': 'Only a Confirmed Purchase Order can receive goods.'})
            attrs['supplier'] = str(po.supplier.id)
        if attrs['source_type'] == 'Farmer' and not attrs.get('farmer'):
            raise serializers.ValidationError({'farmer': 'Required when source_type is Farmer.'})
        return attrs

    def to_representation(self, instance):
        return {
            'id': str(instance.id),
            'grn_number': instance.grn_number,
            'grn_date': instance.grn_date,
            'source_type': instance.source_type,
            'supplier': {'id': str(instance.supplier.id), 'name': instance.supplier.supplier_name} if instance.supplier else None,
            'farmer': {'id': str(instance.farmer.id), 'name': instance.farmer.full_name} if instance.farmer else None,
            'purchase_order': {'id': str(instance.purchase_order.id), 'po_number': instance.purchase_order.po_number} if instance.purchase_order else None,
            'warehouse': {'id': str(instance.warehouse.id), 'name': instance.warehouse.warehouse_name},
            'items': GRNItemSerializer(instance.items, many=True).data,
            'total_amount': instance.total_amount,
            'status': instance.status,
            'received_by': instance.received_by or '',
            'notes': instance.notes or '',
            'created_at': instance.created_at,
        }

    def create(self, validated_data):
        import datetime as dt

        items_data = validated_data.pop('items')
        warehouse = _get_or_404(Warehouse, validated_data.pop('warehouse'), 'warehouse')
        supplier = _get_or_404(Supplier, validated_data.pop('supplier', None), 'supplier')
        farmer = _get_or_404(Farmer, validated_data.pop('farmer', None), 'farmer')
        po_id = validated_data.pop('purchase_order', None)
        purchase_order = PurchaseOrder.objects(id=po_id).first() if po_id else None

        items = []
        for item_data in items_data:
            product = _get_or_404(Product, item_data.pop('product'), 'product')
            item_data.pop('product_name', None)
            item_data.pop('line_total', None)
            items.append(GRNItem(product=product, **item_data))

        date_str = dt.datetime.utcnow().strftime('%Y%m%d')
        grn_number = f"GRN-{date_str}-{GRN.objects.count() + 1:04d}"

        request = self.context['request']
        grn = GRN(
            grn_number=grn_number,
            source_type=validated_data['source_type'],
            supplier=supplier,
            farmer=farmer,
            purchase_order=purchase_order,
            warehouse=warehouse,
            items=items,
            received_by=request.user.email,
            notes=validated_data.get('notes', ''),
        )
        grn.recalculate_total()
        # PO rollup deliberately happens on GRN *confirm*, not here at create —
        # a Draft GRN can still be rejected, and a rejected shipment must not
        # count toward the PO's cumulative received/loss (see GRNConfirmView).
        grn.save()
        return grn
