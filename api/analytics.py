"""
Analytics summary — one endpoint aggregating real data (orders, purchase
orders, stock, payments) into the shapes needed for the Analytics screen's
charts (bar / pie / donut / candlestick / 3D bar). No fabricated numbers:
every series is a real aggregate over existing documents, grouped or bucketed
differently than the plain Dashboard/Reports views for chart-friendly shapes.
"""
import datetime
from collections import defaultdict, Counter

from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsReportsStaff

from Orders.models import Order
from product_Items.models import Product
from mysite.models import Supplier
from mysite.grn_models import GRN
from .po_models import PurchaseOrder, POPaymentRecord

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _month_label(year, month):
    return f'{MONTH_NAMES[month - 1]} {year}'


def _candles(dated_values):
    """
    dated_values: list of (date, value), any order. Buckets by calendar month
    and returns OHLC-style candles — Open/Close are the first/last value
    chronologically within the month, High/Low the max/min — real spread in
    that month's order/PO values, not synthetic data.
    """
    dated_values = sorted((d, v) for d, v in dated_values if d is not None)
    buckets = defaultdict(list)
    for d, v in dated_values:
        buckets[(d.year, d.month)].append(v)
    rows = []
    for (year, month), values in sorted(buckets.items()):
        rows.append({
            'month': _month_label(year, month),
            'open': round(values[0], 2),
            'close': round(values[-1], 2),
            'high': round(max(values), 2),
            'low': round(min(values), 2),
            'count': len(values),
        })
    return rows[-12:]  # last 12 months with activity


class AnalyticsSummaryView(APIView):
    permission_classes = [IsReportsStaff]

    def get(self, request):
        orders = list(Order.objects.all())
        products = list(Product.objects.all())
        pos = list(PurchaseOrder.objects.all())
        payments = list(POPaymentRecord.objects.all())

        sales_candles = _candles(
            (o.order_date, o.total_amount) for o in orders if o.total_amount
        )
        po_candles = _candles(
            (po.created_at.date() if isinstance(po.created_at, datetime.datetime) else po.created_at, po.proposed_total)
            for po in pos if po.proposed_total
        )

        order_status_distribution = [
            {'name': status, 'value': count}
            for status, count in Counter(o.status for o in orders).items()
        ]

        category_stock = Counter()
        for p in products:
            category_stock[p.category.name if p.category else 'Uncategorized'] += p.total_quantity
        category_stock_distribution = [{'name': k, 'value': v} for k, v in category_stock.items()]

        # Per stock line, not per product — a product held in two warehouses
        # must count toward both, not just whichever one happened to be set.
        warehouse_stock = Counter()
        for p in products:
            for line in p.stock:
                warehouse_stock[line.warehouse.warehouse_name if line.warehouse else 'Unassigned'] += line.quantity_available or 0
        warehouse_stock_distribution = [{'name': k, 'value': v} for k, v in warehouse_stock.items()]

        payment_status_breakdown = Counter()
        for r in payments:
            payment_status_breakdown[r.status] += r.total_amount
        payment_status_distribution = [{'name': k, 'value': round(v, 2)} for k, v in payment_status_breakdown.items()]

        top_products_by_value = sorted(
            (
                {'name': p.name, 'value': round(p.total_quantity * (p.price_per_unit or 0), 2)}
                for p in products
            ),
            key=lambda r: r['value'], reverse=True,
        )[:8]

        # Real purchase history per supplier — summed straight off confirmed
        # GRN line items (what was actually received and at what price),
        # not inferred from Product.supplier's current (lossy, last-writer-
        # wins) value or from PO-agreed pricing which can drift from what
        # was actually receipted.
        supplier_qty = Counter()
        supplier_value = Counter()
        for grn in GRN.objects(status='Confirmed', source_type='Supplier'):
            if not grn.supplier:
                continue
            name = grn.supplier.supplier_name
            for item in grn.items:
                supplier_qty[name] += item.received_qty
                supplier_value[name] += item.line_total

        supplier_spend_distribution = sorted(
            ({'name': k, 'value': round(v, 2)} for k, v in supplier_value.items() if v > 0),
            key=lambda r: r['value'], reverse=True,
        )[:8]
        supplier_qty_distribution = sorted(
            ({'name': k, 'value': v} for k, v in supplier_qty.items() if v > 0),
            key=lambda r: r['value'], reverse=True,
        )[:8]

        return Response({
            'sales_candles': sales_candles,
            'purchase_order_candles': po_candles,
            'order_status_distribution': order_status_distribution,
            'category_stock_distribution': category_stock_distribution,
            'warehouse_stock_distribution': warehouse_stock_distribution,
            'payment_status_distribution': payment_status_distribution,
            'top_products_by_value': top_products_by_value,
            'supplier_spend_distribution': supplier_spend_distribution,
            'supplier_qty_distribution': supplier_qty_distribution,
        })
