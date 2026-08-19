from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status as http_status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination

from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, GRNSerializer,
    WarehouseSerializer, SupplierSerializer, FarmerSerializer, ProductSerializer,
)
from .models import User
from .permissions import IsCatalogStaff, IsSupplierOrFarmer, get_linked_entity
from .notify import sync_low_stock_alert, notify_status
from mysite.grn_models import GRN
from Location.models import Warehouse
from mysite.models import Supplier, Farmer
from product_Items.models import Product


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'user': UserSerializer(user).data, 'tokens': _tokens_for_user(user)},
            status=http_status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({'user': UserSerializer(user).data, 'tokens': _tokens_for_user(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ── Reference lookups ────────────────────────────────────────────────────

class WarehouseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(WarehouseSerializer(Warehouse.objects.all(), many=True).data)


class SupplierListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(SupplierSerializer(Supplier.objects.all(), many=True).data)


class FarmerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(FarmerSerializer(Farmer.objects.all(), many=True).data)


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProductSerializer(Product.objects.all(), many=True).data)


# ── GRN ───────────────────────────────────────────────────────────────────

class GRNPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class GRNListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsCatalogStaff()]
        return [IsAuthenticated()]

    def get(self, request):
        user = request.user
        if user.role == 'Customer':
            return Response({'detail': 'Customers do not have access to GRN records.'}, status=http_status.HTTP_403_FORBIDDEN)

        status_filter = request.query_params.get('status', '')
        search = request.query_params.get('search', '')

        qs = GRN.objects.all()
        if user.role in ('Supplier', 'Farmer'):
            entity = get_linked_entity(user)
            if not entity:
                return paginator_empty_response(request)
            qs = qs.filter(supplier=entity) if user.role == 'Supplier' else qs.filter(farmer=entity)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(grn_number__icontains=search)

        records = list(qs)
        paginator = GRNPagination()
        page = paginator.paginate_queryset(records, request)
        serializer = GRNSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = GRNSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        grn = serializer.save()
        return Response(GRNSerializer(grn).data, status=http_status.HTTP_201_CREATED)


def paginator_empty_response(request):
    paginator = GRNPagination()
    paginator.paginate_queryset([], request)
    return paginator.get_paginated_response([])


class GRNDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_grn(self, grn_id):
        return GRN.objects(id=grn_id).first()

    def get(self, request, grn_id):
        grn = self._get_grn(grn_id)
        if not grn:
            return Response({'detail': 'GRN not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        user = request.user
        if user.role == 'Customer':
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if user.role in ('Supplier', 'Farmer'):
            entity = get_linked_entity(user)
            owns_it = (user.role == 'Supplier' and grn.supplier and entity and grn.supplier.id == entity.id) or \
                      (user.role == 'Farmer' and grn.farmer and entity and grn.farmer.id == entity.id)
            if not owns_it:
                return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        return Response(GRNSerializer(grn).data)


class GRNConfirmView(APIView):
    permission_classes = [IsCatalogStaff]

    def post(self, request, grn_id):
        grn = GRN.objects(id=grn_id).first()
        if not grn:
            return Response({'detail': 'GRN not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if grn.status != 'Draft':
            return Response({'detail': 'Only a Draft GRN can be confirmed.'}, status=http_status.HTTP_400_BAD_REQUEST)

        for item in grn.items:
            product = item.product
            if product:
                # Adds to this GRN's warehouse specifically — a product
                # received into two different warehouses across two GRNs
                # ends up with two separate stock lines, each with its own
                # quantity and landed cost, not one shared bucket.
                product.receive_stock(grn.warehouse, item.received_qty, item.unit_price)
                # Source tracking: tag the product with whoever it was
                # actually just received from, so the Products page "Source"
                # column and the Suppliers report reflect real purchase
                # history instead of only whatever was picked (or left
                # blank) at product-creation time.
                if grn.source_type == 'Supplier' and grn.supplier:
                    product.supplier = grn.supplier
                    product.farmer = None
                elif grn.source_type == 'Farmer' and grn.farmer:
                    product.farmer = grn.farmer
                    product.supplier = None
                product.save()
                sync_low_stock_alert(product, grn.warehouse)

        if grn.purchase_order:
            po = grn.purchase_order
            po_items_by_product = {str(i.product.id): i for i in po.items}
            for line in grn.items:
                po_item = po_items_by_product.get(str(line.product.id))
                if po_item:
                    po_item.received_qty += line.received_qty
                    po_item.loss_qty += line.loss_qty
            po.save()

        grn.status = 'Confirmed'
        grn.save()
        source_name = grn.supplier.supplier_name if grn.supplier else (grn.farmer.full_name if grn.farmer else 'source')
        notify_status(
            'grn_status', 'GRN confirmed',
            f'{grn.grn_number} from {source_name} was confirmed into {grn.warehouse.warehouse_name}.',
            severity='info', grn_id=grn.id,
        )
        return Response(GRNSerializer(grn).data)


class GRNRejectView(APIView):
    permission_classes = [IsCatalogStaff]

    def post(self, request, grn_id):
        grn = GRN.objects(id=grn_id).first()
        if not grn:
            return Response({'detail': 'GRN not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if grn.status != 'Draft':
            return Response({'detail': 'Only a Draft GRN can be rejected.'}, status=http_status.HTTP_400_BAD_REQUEST)

        grn.status = 'Rejected'
        grn.save()
        notify_status('grn_status', 'GRN rejected', f'{grn.grn_number} was rejected.', severity='warning', grn_id=grn.id)
        return Response(GRNSerializer(grn).data)
