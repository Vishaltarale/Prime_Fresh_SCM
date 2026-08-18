"""
Orders module — mirrors Orders/views.py business logic:
  - Create: validates requested qty against warehouse stock, but does NOT
    deduct stock (matches Order_save — deduction is deferred to completion).
  - Update: supports UOM conversion via UOMConversionMatrix when an item's
    unit differs from the product's base unit (matches Order_update), and
    deducts warehouse stock when status becomes "Completed".
  - One intentional deviation from the old app, called out in review: the old
    Order_update deducts stock on every save where status=="Completed", even
    if the order was already Completed — so re-saving a completed order
    double-deducts stock. That is a data-integrity bug, not a workflow
    decision, so this version deducts only on the Draft/Pending/etc-to-
    Completed transition, not on saves where it was already Completed.
  - Invoice PDF: same xhtml2pdf render as generate_invoice_pdf, but with the
    old template's hardcoded placeholder values (customer "John Doe", fixed
    "₹800.00" total, invoice number "INV001") replaced with the real order's
    data, and the automatic email-to-a-hardcoded-personal-address step
    dropped per your direction — this endpoint only returns the PDF.
"""
import io

from django.template.loader import render_to_string
from mongoengine.errors import ValidationError as MongoValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.pagination import PageNumberPagination
from django.http import HttpResponse
from xhtml2pdf import pisa

from Orders.models import Order, ProductItem
from Location.models import Warehouse
from product_Items.models import Product
from UOM.models import UOM, UOMConversionMatrix
from .permissions import has_role

# Orders module access: Admin/Warehouse Manager (full, any order) or Customer
# (own orders only — enforced per-method below, not just at the gate).
# Inventory Officer, Supplier, and Farmer have no Orders access at all.
IsOrdersAccessRole = has_role('Admin', 'Warehouse Manager', 'Customer')

STATUS_CHOICES = ('Pending', 'Processing', 'Completed', 'Cancelled')
PAYMENT_CHOICES = ('Paid', 'Unpaid')


class OrderPagination(PageNumberPagination):
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


def _serialize_order(o):
    return {
        'id': str(o.id),
        'customer_name': o.customer_name,
        'order_date': o.order_date.isoformat() if o.order_date else None,
        'status': o.status,
        'payment_status': o.payment_status,
        'delivery_address': o.delivery_address or '',
        'created_by': o.created_by or '',
        'warehouse': {'id': str(o.warehouse.id), 'name': o.warehouse.warehouse_name} if o.warehouse else None,
        'total_amount': o.total_amount or 0,
        'items': [
            {'product_name': i.product_name, 'quantity': i.quantity, 'price': i.price, 'uom': i.uom, 'line_total': i.line_total}
            for i in o.items
        ],
    }


class OrderListCreateView(APIView):
    permission_classes = [IsOrdersAccessRole]

    def get(self, request):
        qs = Order.objects.all()
        # A Customer only ever sees their own orders — this is enforced
        # server-side regardless of the `mine` query param, not left as a
        # client-optional filter (staff can still use `mine` for themselves).
        if request.user.role == 'Customer':
            qs = qs.filter(created_by=request.user.email)
        elif request.query_params.get('mine') == 'true':
            qs = qs.filter(created_by=request.user.email)
        status_filter = request.query_params.get('status', '')
        if status_filter:
            qs = qs.filter(status=status_filter)
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(customer_name__icontains=search)

        records = list(qs.order_by('-order_date'))
        paginator = OrderPagination()
        page = paginator.paginate_queryset(records, request)
        return paginator.get_paginated_response([_serialize_order(o) for o in page])

    def post(self, request):
        data = request.data
        # A Customer can only ever place an order for themselves — the name
        # is taken from their own account, never trusted from the request body.
        if request.user.role == 'Customer':
            customer_name = request.user.full_name
        else:
            customer_name = (data.get('customer_name') or '').strip()
        delivery_address = data.get('delivery_address', '')
        warehouse = _ref_or_none(Warehouse, data.get('warehouse'))
        items_data = data.get('items') or []

        errors = {}
        if not customer_name:
            errors['customer_name'] = 'This field is required.'
        if not warehouse:
            errors['warehouse'] = 'A valid warehouse is required.'
        if not items_data:
            errors['items'] = 'At least one line item is required.'
        if errors:
            return Response(errors, status=http_status.HTTP_400_BAD_REQUEST)

        items = []
        total_amount = 0.0
        for idx, raw in enumerate(items_data):
            product = _ref_or_none(Product, raw.get('product'))
            if not product or product.warehouse.id != warehouse.id:
                return Response({'items': f'Row {idx + 1}: product not found in the selected warehouse.'}, status=http_status.HTTP_400_BAD_REQUEST)
            try:
                qty = int(raw.get('quantity'))
                price = float(raw.get('price'))
            except (TypeError, ValueError):
                return Response({'items': f'Row {idx + 1}: invalid quantity or price.'}, status=http_status.HTTP_400_BAD_REQUEST)
            if product.quantity_available < qty:
                return Response({'items': f'"{product.name}" has insufficient stock (available: {product.quantity_available}).'}, status=http_status.HTTP_400_BAD_REQUEST)

            items.append(ProductItem(product_name=product.name, quantity=qty, price=price, uom=raw.get('uom', product.uom.name)))
            total_amount += qty * price

        order = Order(
            customer_name=customer_name,
            delivery_address=delivery_address,
            items=items,
            total_amount=total_amount,
            status='Pending',
            payment_status='Unpaid',
            created_by=request.user.email,
            warehouse=warehouse,
        ).save()

        return Response(_serialize_order(order), status=http_status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsOrdersAccessRole]

    def get(self, request, order_id):
        order = _ref_or_none(Order, order_id)
        if not order:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if request.user.role == 'Customer' and order.created_by != request.user.email:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(_serialize_order(order))

    def put(self, request, order_id):
        # Editing/changing status is a staff action — a Customer can view and
        # place their own orders, but not edit or cancel them after the fact.
        if request.user.role == 'Customer':
            return Response({'detail': 'Customers cannot edit orders.'}, status=http_status.HTTP_403_FORBIDDEN)

        order = _ref_or_none(Order, order_id)
        if not order:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        data = request.data
        status_value = data.get('status', order.status)
        if status_value not in STATUS_CHOICES:
            return Response({'status': 'Invalid status.'}, status=http_status.HTTP_400_BAD_REQUEST)
        payment_status = data.get('payment_status', order.payment_status)
        if payment_status not in PAYMENT_CHOICES:
            return Response({'payment_status': 'Invalid payment status.'}, status=http_status.HTTP_400_BAD_REQUEST)

        warehouse = _ref_or_none(Warehouse, data.get('warehouse')) or order.warehouse
        items_data = data.get('items')

        items = order.items
        total_amount = order.total_amount
        if items_data is not None:
            items = []
            total_amount = 0.0
            for idx, raw in enumerate(items_data):
                product = _ref_or_none(Product, raw.get('product'))
                if not product or product.warehouse.id != warehouse.id:
                    return Response({'items': f'Row {idx + 1}: product not found in the selected warehouse.'}, status=http_status.HTTP_400_BAD_REQUEST)

                uom_name = raw.get('uom') or product.uom.name
                user_uom = UOM.objects(name=uom_name).first()
                if not user_uom:
                    return Response({'items': f'Row {idx + 1}: UOM "{uom_name}" not found.'}, status=http_status.HTTP_400_BAD_REQUEST)

                try:
                    raw_qty = float(raw.get('quantity'))
                    price = float(raw.get('price'))
                except (TypeError, ValueError):
                    return Response({'items': f'Row {idx + 1}: invalid quantity or price.'}, status=http_status.HTTP_400_BAD_REQUEST)

                if product.uom.id != user_uom.id:
                    conversion = UOMConversionMatrix.objects(from_uom=user_uom, to_uom=product.uom).first()
                    if not conversion:
                        return Response({'items': f'Row {idx + 1}: no conversion from {uom_name} to {product.uom.name} for {product.name}.'}, status=http_status.HTTP_400_BAD_REQUEST)
                    converted_qty = raw_qty * conversion.factor
                else:
                    converted_qty = raw_qty

                items.append(ProductItem(product_name=product.name, quantity=converted_qty, price=price, uom=uom_name))
                total_amount += converted_qty * price

        was_completed = order.status == 'Completed'
        becoming_completed = status_value == 'Completed' and not was_completed

        if becoming_completed:
            for item in items:
                product = Product.objects(name=item.product_name, warehouse=warehouse).first()
                if product and product.quantity_available < item.quantity:
                    return Response(
                        {'items': f'Not enough stock for {item.product_name} (available: {product.quantity_available}, required: {item.quantity}).'},
                        status=http_status.HTTP_400_BAD_REQUEST,
                    )

        order.customer_name = data.get('customer_name', order.customer_name)
        order.delivery_address = data.get('delivery_address', order.delivery_address)
        order.status = status_value
        order.payment_status = payment_status
        order.warehouse = warehouse
        order.items = items
        order.total_amount = total_amount
        order.save()

        if becoming_completed:
            for item in items:
                product = Product.objects(name=item.product_name, warehouse=warehouse).first()
                if product:
                    product.quantity_available -= int(item.quantity)
                    product.save()

        return Response(_serialize_order(order))

    def delete(self, request, order_id):
        if request.user.role == 'Customer':
            return Response({'detail': 'Customers cannot delete orders.'}, status=http_status.HTTP_403_FORBIDDEN)

        order = _ref_or_none(Order, order_id)
        if not order:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        order.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)


class OrderInvoicePdfView(APIView):
    permission_classes = [IsOrdersAccessRole]

    def get(self, request, order_id):
        order = _ref_or_none(Order, order_id)
        if not order:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if request.user.role == 'Customer' and order.created_by != request.user.email:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        html = render_to_string('api_invoice.html', {'order': order})
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(html.encode('UTF-8')), dest=pdf_buffer)
        if pisa_status.err:
            return Response({'detail': 'Failed to generate PDF.'}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{order.id}.pdf"'
        return response
