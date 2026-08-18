"""
Purchase Order views. Staff actions (create/send/confirm/reject/payment/refund)
use the same Admin + Inventory Officer + Warehouse Manager group GRN already
uses (IsCatalogStaff) — matching "confirmed or rejected by the admin or
inventory manager or the warehouse provider" from the request. The supplier
response endpoints are deliberately AllowAny + token-gated: the supplier
never logs in for this (per your direction), the random URL token is the
only credential, and it stops accepting new submissions once the PO leaves
Sent/Awaiting Approval.
"""
import datetime

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from mongoengine.errors import NotUniqueError, ValidationError as MongoValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status as http_status
from rest_framework.pagination import PageNumberPagination

from .permissions import IsCatalogStaff
from .po_models import PurchaseOrder, POItem, POPaymentRecord, POPaymentEntry
from product_Items.models import Product
from Location.models import Warehouse
from mysite.models import Supplier


class POPagination(PageNumberPagination):
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


def _serialize_item(i):
    return {
        'product': str(i.product.id),
        'product_name': i.product.name,
        'ordered_qty': i.ordered_qty,
        'proposed_price': i.proposed_price,
        'confirmed_price': i.confirmed_price,
        'received_qty': i.received_qty,
        'loss_qty': i.loss_qty,
        'remaining_qty': i.remaining_qty,
        'line_total_confirmed': i.line_total_confirmed,
        'line_total_received': i.line_total_received,
    }


def _serialize_po(po):
    return {
        'id': str(po.id),
        'po_number': po.po_number,
        'supplier': {'id': str(po.supplier.id), 'name': po.supplier.supplier_name, 'email': po.supplier.email},
        'warehouse': {'id': str(po.warehouse.id), 'name': po.warehouse.warehouse_name},
        'items': [_serialize_item(i) for i in po.items],
        'status': po.status,
        'notes': po.notes or '',
        'created_by': po.created_by or '',
        'approved_by': po.approved_by or '',
        'proposed_total': po.proposed_total,
        'confirmed_total': po.confirmed_total,
        'received_total': po.received_total,
        'created_at': po.created_at,
        'sent_at': po.sent_at,
        'responded_at': po.responded_at,
        'confirmed_at': po.confirmed_at,
    }


class POListCreateView(APIView):
    permission_classes = [IsCatalogStaff]

    def get(self, request):
        status_filter = request.query_params.get('status', '')
        search = request.query_params.get('search', '')
        qs = PurchaseOrder.objects.all()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(po_number__icontains=search)

        records = list(qs)
        paginator = POPagination()
        page = paginator.paginate_queryset(records, request)
        return paginator.get_paginated_response([_serialize_po(po) for po in page])

    def post(self, request):
        data = request.data
        supplier = _ref_or_none(Supplier, data.get('supplier'))
        warehouse = _ref_or_none(Warehouse, data.get('warehouse'))
        items_data = data.get('items') or []

        errors = {}
        if not supplier:
            errors['supplier'] = 'A valid supplier is required.'
        if not warehouse:
            errors['warehouse'] = 'A valid warehouse is required.'
        if not items_data:
            errors['items'] = 'At least one line item is required.'
        if errors:
            return Response(errors, status=http_status.HTTP_400_BAD_REQUEST)

        items = []
        for idx, raw in enumerate(items_data):
            product = _ref_or_none(Product, raw.get('product'))
            if not product:
                return Response({'items': f'Row {idx + 1}: unknown product.'}, status=http_status.HTTP_400_BAD_REQUEST)
            try:
                ordered_qty = int(raw.get('ordered_qty'))
                proposed_price = float(raw.get('proposed_price'))
            except (TypeError, ValueError):
                return Response({'items': f'Row {idx + 1}: invalid quantity or price.'}, status=http_status.HTTP_400_BAD_REQUEST)
            if ordered_qty < 1:
                return Response({'items': f'Row {idx + 1}: quantity must be at least 1.'}, status=http_status.HTTP_400_BAD_REQUEST)
            items.append(POItem(product=product, ordered_qty=ordered_qty, proposed_price=proposed_price))

        date_str = datetime.datetime.utcnow().strftime('%Y%m%d')
        po_number = f"PO-{date_str}-{PurchaseOrder.objects.count() + 1:04d}"

        po = PurchaseOrder(
            po_number=po_number, supplier=supplier, warehouse=warehouse, items=items,
            notes=data.get('notes', ''), created_by=request.user.email, status='Draft',
        ).save()
        return Response(_serialize_po(po), status=http_status.HTTP_201_CREATED)


class PODetailView(APIView):
    permission_classes = [IsCatalogStaff]

    def get(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(_serialize_po(po))

    def delete(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if po.status not in ('Draft', 'Rejected'):
            return Response({'detail': 'Only a Draft or Rejected PO can be deleted.'}, status=http_status.HTTP_400_BAD_REQUEST)
        po.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)


class POConfirmedForGRNView(APIView):
    """Lightweight lookup feeding the GRN-creation dropdown — Confirmed POs with remaining quantity."""
    permission_classes = [IsCatalogStaff]

    def get(self, request):
        pos = PurchaseOrder.objects(status='Confirmed')
        results = []
        for po in pos:
            if any(i.remaining_qty > 0 for i in po.items):
                results.append({
                    'id': str(po.id),
                    'po_number': po.po_number,
                    'supplier': {'id': str(po.supplier.id), 'name': po.supplier.supplier_name},
                    'warehouse': {'id': str(po.warehouse.id), 'name': po.warehouse.warehouse_name},
                    'items': [_serialize_item(i) for i in po.items if i.remaining_qty > 0],
                })
        return Response(results)


class POSendView(APIView):
    permission_classes = [IsCatalogStaff]

    def post(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if po.status not in ('Draft', 'Rejected'):
            return Response({'detail': 'Only a Draft or Rejected PO can be sent.'}, status=http_status.HTTP_400_BAD_REQUEST)

        po.generate_response_token()
        po.status = 'Sent'
        po.sent_at = datetime.datetime.utcnow()
        po.save()

        response_url = f"{settings.REACT_WEB_URL}/po-response/{po.response_token}"
        lines = "\n".join(
            f"  - {i.product.name}: {i.ordered_qty} {i.product.uom.name if i.product.uom else ''} @ proposed Rs. {i.proposed_price:.2f}"
            for i in po.items
        )
        body = (
            f"Dear {po.supplier.supplier_name},\n\n"
            f"Prime Fresh SCM has a new purchase order for your review: {po.po_number}.\n\n"
            f"Proposed items:\n{lines}\n\n"
            f"Proposed total: Rs. {po.proposed_total:.2f}\n\n"
            f"Please review and submit your fixed pricing here:\n{response_url}\n\n"
            f"This link is unique to this purchase order — please do not share it.\n"
        )
        try:
            email = EmailMultiAlternatives(
                subject=f"Purchase Order {po.po_number} — Prime Fresh SCM",
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=[po.supplier.email],
            )
            email.send(fail_silently=False)
            email_sent = True
        except Exception as exc:
            email_sent = False
            email_error = str(exc)

        payload = _serialize_po(po)
        payload['email_sent'] = email_sent
        if not email_sent:
            payload['email_error'] = email_error
        return Response(payload)


class POConfirmView(APIView):
    permission_classes = [IsCatalogStaff]

    def post(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if po.status != 'Awaiting Approval':
            return Response({'detail': 'Only a PO awaiting approval can be confirmed.'}, status=http_status.HTTP_400_BAD_REQUEST)
        if any(i.confirmed_price is None for i in po.items):
            return Response({'detail': 'All items must have a supplier-confirmed price before approval.'}, status=http_status.HTTP_400_BAD_REQUEST)

        po.status = 'Confirmed'
        po.confirmed_at = datetime.datetime.utcnow()
        po.approved_by = request.user.email
        po.save()
        return Response(_serialize_po(po))


class PORejectView(APIView):
    permission_classes = [IsCatalogStaff]

    def post(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if po.status not in ('Awaiting Approval', 'Sent'):
            return Response({'detail': 'Only a Sent or Awaiting-Approval PO can be rejected.'}, status=http_status.HTTP_400_BAD_REQUEST)

        po.status = 'Rejected'
        po.approved_by = request.user.email
        po.save()
        return Response(_serialize_po(po))


# ── Supplier-facing, unauthenticated (token-gated) ─────────────────────────

class POPublicView(APIView):
    """No login — the response token in the URL is the only credential."""
    permission_classes = [AllowAny]

    def get(self, request, token):
        po = PurchaseOrder.objects(response_token=token).first()
        if not po or po.status not in ('Sent', 'Awaiting Approval'):
            return Response({'detail': 'This purchase order link is invalid or no longer active.'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(_serialize_po(po))

    def post(self, request, token):
        po = PurchaseOrder.objects(response_token=token).first()
        if not po or po.status not in ('Sent', 'Awaiting Approval'):
            return Response({'detail': 'This purchase order link is invalid or no longer active.'}, status=http_status.HTTP_404_NOT_FOUND)

        prices = request.data.get('items') or []
        price_by_product = {}
        for row in prices:
            try:
                price_by_product[str(row.get('product'))] = float(row.get('confirmed_price'))
            except (TypeError, ValueError):
                return Response({'items': 'Every item needs a valid confirmed price.'}, status=http_status.HTTP_400_BAD_REQUEST)

        missing = [str(i.product.id) for i in po.items if str(i.product.id) not in price_by_product]
        if missing:
            return Response({'items': 'A confirmed price is required for every item.'}, status=http_status.HTTP_400_BAD_REQUEST)

        for item in po.items:
            item.confirmed_price = price_by_product[str(item.product.id)]

        po.status = 'Awaiting Approval'
        po.responded_at = datetime.datetime.utcnow()
        po.save()
        return Response(_serialize_po(po))


# ── Payments & refunds ──────────────────────────────────────────────────────

def _serialize_payment_record(record):
    return {
        'po': str(record.po.id),
        'total_amount': record.total_amount,
        'amount_paid': record.amount_paid,
        'balance': record.balance,
        'status': record.status,
        'history': [
            {
                'kind': h.kind, 'amount': h.amount, 'method': h.method or '',
                'reason': h.reason or '', 'recorded_by': h.recorded_by or '', 'date': h.date,
            }
            for h in record.history
        ],
    }


def _get_or_create_payment_record(po):
    record = POPaymentRecord.objects(po=po).first()
    if not record:
        record = POPaymentRecord(po=po, history=[]).save()
    return record


class POPaymentView(APIView):
    permission_classes = [IsCatalogStaff]

    def get(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        record = _get_or_create_payment_record(po)
        return Response(_serialize_payment_record(record))

    def post(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if po.status != 'Confirmed':
            return Response({'detail': 'Payments can only be recorded against a Confirmed PO.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(request.data.get('amount'))
        except (TypeError, ValueError):
            return Response({'amount': 'A valid amount is required.'}, status=http_status.HTTP_400_BAD_REQUEST)
        if amount <= 0:
            return Response({'amount': 'Amount must be greater than zero.'}, status=http_status.HTTP_400_BAD_REQUEST)

        record = _get_or_create_payment_record(po)
        if amount > record.balance + 1e-9:
            return Response({'amount': f'Payment exceeds the remaining balance (Rs. {record.balance:.2f}).'}, status=http_status.HTTP_400_BAD_REQUEST)

        record.history.append(POPaymentEntry(
            kind='Payment', amount=amount, method=request.data.get('method', ''),
            recorded_by=request.user.email,
        ))
        record.save()
        return Response(_serialize_payment_record(record), status=http_status.HTTP_201_CREATED)


class PORefundView(APIView):
    permission_classes = [IsCatalogStaff]

    def post(self, request, po_id):
        po = _ref_or_none(PurchaseOrder, po_id)
        if not po:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        try:
            amount = float(request.data.get('amount'))
        except (TypeError, ValueError):
            return Response({'amount': 'A valid amount is required.'}, status=http_status.HTTP_400_BAD_REQUEST)
        reason = (request.data.get('reason') or '').strip()
        if amount <= 0:
            return Response({'amount': 'Amount must be greater than zero.'}, status=http_status.HTTP_400_BAD_REQUEST)
        if not reason:
            return Response({'reason': 'A reason is required for a refund.'}, status=http_status.HTTP_400_BAD_REQUEST)

        record = _get_or_create_payment_record(po)
        if amount > record.amount_paid + 1e-9:
            return Response({'amount': f'Refund exceeds the amount actually paid (Rs. {record.amount_paid:.2f}).'}, status=http_status.HTTP_400_BAD_REQUEST)

        record.history.append(POPaymentEntry(
            kind='Refund', amount=amount, reason=reason, recorded_by=request.user.email,
        ))
        record.save()
        return Response(_serialize_payment_record(record), status=http_status.HTTP_201_CREATED)
