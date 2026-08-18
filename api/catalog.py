"""
Product/Category/Subcategory/UOM module — unlike the generic entities registry,
these carry real foreign keys (subcategory->category, product->{category,
subcategory,uom,warehouse,supplier|farmer}, conversion->{from_uom,to_uom}) and
entity-specific business rules (UOM name normalization, upsert-by-pair on
conversions, friendly duplicate-category message) mirrored from
product_Items/views.py and UOM/views.py.
"""
from mongoengine.errors import NotUniqueError, ValidationError as MongoValidationError
from mongoengine.queryset.visitor import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsStaffOrReadOnly
from rest_framework import status as http_status
from rest_framework.pagination import PageNumberPagination

from product_Items.models import Category, Subcategory, Product
from UOM.models import UOM, UOMConversionMatrix
from Location.models import Warehouse
from mysite.models import Supplier, Farmer


class CatalogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def _ref_or_none(model, object_id):
    if not object_id:
        return None
    try:
        return model.objects(id=object_id).first()
    except MongoValidationError:
        return None


# ── Category ─────────────────────────────────────────────────────────────

def _serialize_category(c):
    return {'id': str(c.id), 'name': c.name, 'description': c.description or ''}


class CategoryListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        qs = Category.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        records = list(qs)
        paginator = CatalogPagination()
        page = paginator.paginate_queryset(records, request)
        return paginator.get_paginated_response([_serialize_category(c) for c in page])

    def post(self, request):
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'name': 'This field is required.'}, status=http_status.HTTP_400_BAD_REQUEST)
        if Category.objects(name=name).first():
            return Response({'name': 'A category with this name already exists.'}, status=http_status.HTTP_400_BAD_REQUEST)
        category = Category(name=name, description=request.data.get('description', '')).save()
        return Response(_serialize_category(category), status=http_status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def delete(self, request, object_id):
        category = _ref_or_none(Category, object_id)
        if not category:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if Subcategory.objects(category=category).first():
            return Response({'detail': 'Cannot delete a category that has subcategories.'}, status=http_status.HTTP_400_BAD_REQUEST)
        category.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)


# ── Subcategory ──────────────────────────────────────────────────────────

def _serialize_subcategory(s):
    return {'id': str(s.id), 'name': s.name, 'category': {'id': str(s.category.id), 'name': s.category.name}}


class SubcategoryListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        category_id = request.query_params.get('category', '')
        qs = Subcategory.objects.all()
        if category_id:
            qs = qs.filter(category=category_id)
        if search:
            qs = qs.filter(name__icontains=search)
        records = list(qs)
        paginator = CatalogPagination()
        page = paginator.paginate_queryset(records, request)
        return paginator.get_paginated_response([_serialize_subcategory(s) for s in page])

    def post(self, request):
        name = (request.data.get('name') or '').strip()
        category = _ref_or_none(Category, request.data.get('category'))
        if not name or not category:
            errors = {}
            if not name:
                errors['name'] = 'This field is required.'
            if not category:
                errors['category'] = 'A valid category is required.'
            return Response(errors, status=http_status.HTTP_400_BAD_REQUEST)
        subcategory = Subcategory(name=name, category=category).save()
        return Response(_serialize_subcategory(subcategory), status=http_status.HTTP_201_CREATED)


class SubcategoryDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def delete(self, request, object_id):
        subcategory = _ref_or_none(Subcategory, object_id)
        if not subcategory:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if Product.objects(subcategory=subcategory).first():
            return Response({'detail': 'Cannot delete a subcategory that has products.'}, status=http_status.HTTP_400_BAD_REQUEST)
        subcategory.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)


# ── UOM ──────────────────────────────────────────────────────────────────

def _serialize_uom(u):
    return {'id': str(u.id), 'name': u.name, 'description': u.description or ''}


class UOMListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        qs = UOM.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        records = list(qs)
        paginator = CatalogPagination()
        page = paginator.paginate_queryset(records, request)
        return paginator.get_paginated_response([_serialize_uom(u) for u in page])

    def post(self, request):
        # Mirrors UOM.views.uom_register: normalize to upper-case, stripped.
        name = (request.data.get('name') or '').upper().strip()
        if not name:
            return Response({'name': 'This field is required.'}, status=http_status.HTTP_400_BAD_REQUEST)
        try:
            uom = UOM(name=name, description=request.data.get('description', '')).save()
        except NotUniqueError:
            return Response({'name': 'A UOM with this name already exists.'}, status=http_status.HTTP_400_BAD_REQUEST)
        return Response(_serialize_uom(uom), status=http_status.HTTP_201_CREATED)


class UOMDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def delete(self, request, object_id):
        uom = _ref_or_none(UOM, object_id)
        if not uom:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if Product.objects(uom=uom).first():
            return Response({'detail': 'Cannot delete a UOM that is used by products.'}, status=http_status.HTTP_400_BAD_REQUEST)
        UOMConversionMatrix.objects(Q(from_uom=uom) | Q(to_uom=uom)).delete()
        uom.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)


# ── UOM Conversion Matrix ────────────────────────────────────────────────

def _serialize_conversion(c):
    return {
        'id': str(c.id),
        'from_uom': {'id': str(c.from_uom.id), 'name': c.from_uom.name},
        'to_uom': {'id': str(c.to_uom.id), 'name': c.to_uom.name},
        'factor': c.factor,
    }


class ConversionListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request):
        records = list(UOMConversionMatrix.objects.all())
        paginator = CatalogPagination()
        page = paginator.paginate_queryset(records, request)
        return paginator.get_paginated_response([_serialize_conversion(c) for c in page])

    def post(self, request):
        # Mirrors UOM.views.conversion_register: reject same-unit, upsert on (from,to) pair.
        from_uom = _ref_or_none(UOM, request.data.get('from_uom'))
        to_uom = _ref_or_none(UOM, request.data.get('to_uom'))
        factor = request.data.get('factor')

        errors = {}
        if not from_uom:
            errors['from_uom'] = 'A valid "from" unit is required.'
        if not to_uom:
            errors['to_uom'] = 'A valid "to" unit is required.'
        if from_uom and to_uom and from_uom.id == to_uom.id:
            errors['to_uom'] = 'From and To units must be different.'
        if factor in (None, ''):
            errors['factor'] = 'This field is required.'
        if errors:
            return Response(errors, status=http_status.HTTP_400_BAD_REQUEST)

        factor = float(factor)
        existing = UOMConversionMatrix.objects(from_uom=from_uom, to_uom=to_uom).first()
        if existing:
            existing.factor = factor
            existing.save()
            return Response(_serialize_conversion(existing))

        conversion = UOMConversionMatrix(from_uom=from_uom, to_uom=to_uom, factor=factor).save()
        return Response(_serialize_conversion(conversion), status=http_status.HTTP_201_CREATED)


class ConversionDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def delete(self, request, object_id):
        conversion = _ref_or_none(UOMConversionMatrix, object_id)
        if not conversion:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        conversion.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)


# ── Product ──────────────────────────────────────────────────────────────

def _serialize_product(p):
    return {
        'id': str(p.id),
        'name': p.name,
        'sku': p.sku,
        'category': {'id': str(p.category.id), 'name': p.category.name} if p.category else None,
        'subcategory': {'id': str(p.subcategory.id), 'name': p.subcategory.name} if p.subcategory else None,
        'uom': {'id': str(p.uom.id), 'name': p.uom.name} if p.uom else None,
        'warehouse': {'id': str(p.warehouse.id), 'name': p.warehouse.warehouse_name} if p.warehouse else None,
        'price_per_unit': p.price_per_unit,
        'quantity_available': p.quantity_available,
        'description': p.description or '',
        'source_type': 'supplier' if p.supplier else ('farmer' if p.farmer else None),
        'supplier': {'id': str(p.supplier.id), 'name': p.supplier.supplier_name} if p.supplier else None,
        'farmer': {'id': str(p.farmer.id), 'name': p.farmer.full_name} if p.farmer else None,
        'created_at': p.created_at,
    }


class CatalogProductListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        category_id = request.query_params.get('category', '')
        qs = Product.objects.all()
        if category_id:
            qs = qs.filter(category=category_id)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        records = list(qs)
        paginator = CatalogPagination()
        page = paginator.paginate_queryset(records, request)
        return paginator.get_paginated_response([_serialize_product(p) for p in page])

    def post(self, request):
        data = request.data
        errors = {}

        name = (data.get('name') or '').strip()
        sku = (data.get('sku') or '').strip()
        if not name:
            errors['name'] = 'This field is required.'
        if not sku:
            errors['sku'] = 'This field is required.'

        category = _ref_or_none(Category, data.get('category'))
        subcategory = _ref_or_none(Subcategory, data.get('subcategory'))
        uom = _ref_or_none(UOM, data.get('uom'))
        warehouse = _ref_or_none(Warehouse, data.get('warehouse'))
        if not category:
            errors['category'] = 'A valid category is required.'
        if not subcategory:
            errors['subcategory'] = 'A valid subcategory is required.'
        if not uom:
            errors['uom'] = 'A valid UOM is required.'
        if not warehouse:
            errors['warehouse'] = 'A valid warehouse is required.'

        source_type = data.get('source_type')
        supplier = farmer = None
        if source_type == 'supplier':
            supplier = _ref_or_none(Supplier, data.get('supplier'))
            if not supplier:
                errors['supplier'] = 'A valid supplier is required for this source type.'
        elif source_type == 'farmer':
            farmer = _ref_or_none(Farmer, data.get('farmer'))
            if not farmer:
                errors['farmer'] = 'A valid farmer is required for this source type.'

        try:
            price_per_unit = float(data.get('price_per_unit'))
        except (TypeError, ValueError):
            errors['price_per_unit'] = 'Must be a number.'
            price_per_unit = None
        try:
            quantity_available = int(data.get('quantity_available', 0) or 0)
        except (TypeError, ValueError):
            errors['quantity_available'] = 'Must be a whole number.'
            quantity_available = None

        if errors:
            return Response(errors, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            product = Product(
                name=name, sku=sku, category=category, subcategory=subcategory, uom=uom,
                warehouse=warehouse, price_per_unit=price_per_unit, quantity_available=quantity_available,
                description=data.get('description', ''), supplier=supplier, farmer=farmer,
            ).save()
        except NotUniqueError:
            return Response({'sku': 'A product with this SKU already exists.'}, status=http_status.HTTP_400_BAD_REQUEST)

        return Response(_serialize_product(product), status=http_status.HTTP_201_CREATED)


class CatalogProductDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request, object_id):
        product = _ref_or_none(Product, object_id)
        if not product:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(_serialize_product(product))

    def delete(self, request, object_id):
        product = _ref_or_none(Product, object_id)
        if not product:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)
