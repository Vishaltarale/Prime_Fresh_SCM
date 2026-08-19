"""
Dashboard summary — replaces the old app's server-rendered matplotlib/Plotly
charts (index.html's order-trend line chart, admin_dash.html's entity-count
cards, inventory.html's category pie chart, warehouse_dash.html's stock bar
chart) with one JSON endpoint the React charting library (Recharts) renders
client-side.
"""
from collections import Counter

from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsReportsStaff

from Orders.models import Order
from product_Items.models import Product
from Location.models import Warehouse
from mysite.models import Employee, Farmer, Supplier, Customer
from .po_models import PurchaseOrder, POPaymentRecord

LOW_STOCK_THRESHOLD = 10


class DashboardSummaryView(APIView):
    permission_classes = [IsReportsStaff]

    def get(self, request):
        orders = list(Order.objects.all())
        products = list(Product.objects.all())

        status_counts = Counter(o.status for o in orders)
        order_status_breakdown = [{'status': s, 'count': c} for s, c in status_counts.items()]

        category_qty = Counter()
        for p in products:
            category_name = p.category.name if p.category else 'Uncategorized'
            category_qty[category_name] += p.total_quantity
        inventory_by_category = [{'category': k, 'quantity': v} for k, v in category_qty.items()]

        # A product with stock in two warehouses contributes to both — sum
        # per stock line, not per product, or one warehouse's count would
        # absorb the other's.
        warehouse_stock = Counter()
        for p in products:
            for line in p.stock:
                wh_name = line.warehouse.warehouse_name if line.warehouse else 'Unassigned'
                warehouse_stock[wh_name] += line.quantity_available or 0
        stock_by_warehouse = [{'warehouse': k, 'quantity': v} for k, v in warehouse_stock.items()]

        recent_orders = sorted(orders, key=lambda o: o.order_date or '', reverse=True)[:5]

        payment_records = list(POPaymentRecord.objects.all())
        total_outstanding_to_suppliers = sum(r.balance for r in payment_records)

        return Response({
            'counts': {
                'orders': len(orders),
                'products': len(products),
                'warehouses': Warehouse.objects.count(),
                'employees': Employee.objects.count(),
                'farmers': Farmer.objects.count(),
                'suppliers': Supplier.objects.count(),
                'customers': Customer.objects.count(),
                'low_stock_products': sum(1 for p in products if p.total_quantity <= LOW_STOCK_THRESHOLD),
                'pos_awaiting_approval': PurchaseOrder.objects(status='Awaiting Approval').count(),
                'pos_confirmed': PurchaseOrder.objects(status='Confirmed').count(),
            },
            'total_revenue': sum(o.total_amount or 0 for o in orders if o.status == 'Completed'),
            'total_outstanding_to_suppliers': total_outstanding_to_suppliers,
            'order_status_breakdown': order_status_breakdown,
            'inventory_by_category': inventory_by_category,
            'stock_by_warehouse': stock_by_warehouse,
            'recent_orders': [
                {
                    'id': str(o.id),
                    'customer_name': o.customer_name,
                    'status': o.status,
                    'total_amount': o.total_amount or 0,
                    'order_date': o.order_date.isoformat() if o.order_date else None,
                }
                for o in recent_orders
            ],
        })
