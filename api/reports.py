"""
Reports module — reworks Location/views.py's inventory_report/export_pdf/export_excel.

Fixes applied vs. the old code (data-breaking bugs, not stylistic changes — see
the migration review for detail):
  - "order" report: the old view had `return` INSIDE the row-building for loop,
    so it only ever returned a report with one row. Fixed to build all rows
    first, then return once.
  - "sales" report: filtered `status="completed"` (lowercase) against a model
    whose actual choices are capitalized ("Completed"), so it always matched
    zero orders. Fixed to compare against the real choice value.
  - "supplier" report: aggregated `Order.objects(supplier=s)`, but Order has no
    `supplier` field — replaced with the real relationship instead
    (Product.supplier), per your direction: supplier + their registered
    products/stock value.
  - "expiry" report: filtered on Product.expiry_date / Product.reorder_level,
    neither of which exist on Product — renamed to a Low-Stock report using
    the one part of the old logic that had real data behind it
    (quantity_available <= threshold), per your direction.
  - PDF/Excel export: the old export_pdf/export_excel always produced the same
    "top 5 products" summary regardless of which report was on screen. Now
    export renders the exact same headers/rows as the on-screen report, via
    one shared data builder both the JSON view and the export views call.
"""
import io
import datetime

import openpyxl
from reportlab.lib import colors as pdf_colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsReportsStaff
from rest_framework import status as http_status
from django.http import HttpResponse

from product_Items.models import Product
from Orders.models import Order
from Location.models import Warehouse
from mysite.models import Supplier
from .po_models import PurchaseOrder, POPaymentRecord

LOW_STOCK_DEFAULT_THRESHOLD = 10


def _report_inventory(params):
    products = Product.objects.all()
    headers = ['Product', 'SKU', 'Category', 'Subcategory', 'UOM', 'Quantity', 'Warehouse', 'Created At']
    rows = [
        [
            p.name, p.sku,
            p.category.name if p.category else '—',
            p.subcategory.name if p.subcategory else '—',
            p.uom.name if p.uom else '—',
            p.quantity_available,
            p.warehouse.warehouse_name if p.warehouse else '—',
            p.created_at.strftime('%d %b %Y, %I:%M %p') if p.created_at else '—',
        ]
        for p in products
    ]
    return {'title': 'Inventory Report', 'headers': headers, 'rows': rows}


def _report_orders(params):
    orders = Order.objects.all().order_by('-order_date')
    headers = ['Order ID', 'Customer', 'Order Date', 'Total Amount', 'Status', 'Payment Status']
    rows = [
        [
            str(o.id), o.customer_name,
            o.order_date.strftime('%d %b %Y') if o.order_date else '—',
            f'Rs. {o.total_amount:.2f}' if o.total_amount else 'Rs. 0.00',
            o.status, o.payment_status,
        ]
        for o in orders
    ]
    return {'title': 'Orders Report', 'headers': headers, 'rows': rows}


def _report_suppliers(params):
    suppliers = Supplier.objects.all()
    headers = ['Supplier', 'Company', 'Email', 'Phone', 'Products Supplied', 'Total Stock Value']
    rows = []
    for s in suppliers:
        products = Product.objects(supplier=s)
        stock_value = sum((p.quantity_available or 0) * (p.price_per_unit or 0) for p in products)
        rows.append([s.supplier_name, s.company_name, s.email, s.phone, products.count(), f'Rs. {stock_value:.2f}'])
    return {'title': 'Supplier Report', 'headers': headers, 'rows': rows}


def _report_warehouses(params):
    warehouses = Warehouse.objects.all()
    headers = ['Warehouse', 'City', 'Total Products', 'Total Quantity']
    rows = []
    for w in warehouses:
        products = Product.objects(warehouse=w)
        rows.append([w.warehouse_name, w.city, products.count(), sum(p.quantity_available or 0 for p in products)])
    return {'title': 'Warehouse Report', 'headers': headers, 'rows': rows}


def _report_sales(params):
    orders = Order.objects(status='Completed')
    headers = ['Order ID', 'Customer', 'Date', 'Total Amount', 'Payment Status']
    rows = [
        [
            str(o.id), o.customer_name,
            o.order_date.strftime('%d %b %Y') if o.order_date else '—',
            f'Rs. {o.total_amount:.2f}' if o.total_amount else 'Rs. 0.00',
            o.payment_status,
        ]
        for o in orders
    ]
    total_revenue = sum(o.total_amount for o in orders if o.total_amount)
    return {'title': 'Sales Report', 'headers': headers, 'rows': rows, 'summary': f'Total Revenue: Rs. {total_revenue:.2f}'}


def _report_low_stock(params):
    try:
        threshold = int(params.get('threshold', LOW_STOCK_DEFAULT_THRESHOLD))
    except (TypeError, ValueError):
        threshold = LOW_STOCK_DEFAULT_THRESHOLD
    products = Product.objects(quantity_available__lte=threshold)
    headers = ['Product', 'SKU', 'UOM', 'Quantity Available', 'Warehouse']
    rows = [
        [p.name, p.sku, p.uom.name if p.uom else '—', p.quantity_available, p.warehouse.warehouse_name if p.warehouse else '—']
        for p in products
    ]
    return {'title': f'Low-Stock Report (≤ {threshold})', 'headers': headers, 'rows': rows}


def _report_purchase_orders(params):
    pos = PurchaseOrder.objects.all()
    headers = ['PO Number', 'Supplier', 'Status', 'Ordered Value', 'Received Value', 'Loss Qty', 'Created']
    rows = []
    ordered_total = received_total = 0.0
    for po in pos:
        ordered_value = sum(i.ordered_qty * (i.confirmed_price or i.proposed_price) for i in po.items)
        received_value = po.received_total
        loss_qty = sum(i.loss_qty for i in po.items)
        ordered_total += ordered_value
        received_total += received_value
        rows.append([
            po.po_number, po.supplier.supplier_name, po.status,
            f'Rs. {ordered_value:.2f}', f'Rs. {received_value:.2f}', loss_qty,
            po.created_at.strftime('%d %b %Y') if po.created_at else '—',
        ])
    loss_value = ordered_total - received_total
    return {
        'title': 'Purchase Orders Report', 'headers': headers, 'rows': rows,
        'summary': f'Ordered: Rs. {ordered_total:.2f}  |  Received: Rs. {received_total:.2f}  |  Loss: Rs. {loss_value:.2f}',
    }


def _report_po_payments(params):
    records = POPaymentRecord.objects.all()
    headers = ['PO Number', 'Supplier', 'Total Owed', 'Paid', 'Refunded', 'Balance', 'Status']
    rows = []
    total_paid = total_outstanding = total_refunded = 0.0
    for r in records:
        paid = sum(h.amount for h in r.history if h.kind == 'Payment')
        refunded = sum(h.amount for h in r.history if h.kind == 'Refund')
        total_paid += paid
        total_refunded += refunded
        total_outstanding += r.balance
        rows.append([
            r.po.po_number, r.po.supplier.supplier_name,
            f'Rs. {r.total_amount:.2f}', f'Rs. {paid:.2f}', f'Rs. {refunded:.2f}',
            f'Rs. {r.balance:.2f}', r.status,
        ])
    return {
        'title': 'Supplier Payments Report', 'headers': headers, 'rows': rows,
        'summary': f'Paid: Rs. {total_paid:.2f}  |  Outstanding: Rs. {total_outstanding:.2f}  |  Refunded: Rs. {total_refunded:.2f}',
    }


REPORT_BUILDERS = {
    'inventory': _report_inventory,
    'orders': _report_orders,
    'suppliers': _report_suppliers,
    'warehouses': _report_warehouses,
    'sales': _report_sales,
    'low-stock': _report_low_stock,
    'purchase-orders': _report_purchase_orders,
    'po-payments': _report_po_payments,
}


class ReportDataView(APIView):
    permission_classes = [IsReportsStaff]

    def get(self, request, report_type):
        builder = REPORT_BUILDERS.get(report_type)
        if not builder:
            return Response({'detail': f'Unknown report type "{report_type}".'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(builder(request.query_params))


class ReportExportPdfView(APIView):
    permission_classes = [IsReportsStaff]

    def get(self, request, report_type):
        builder = REPORT_BUILDERS.get(report_type)
        if not builder:
            return Response({'detail': f'Unknown report type "{report_type}".'}, status=http_status.HTTP_404_NOT_FOUND)
        data = builder(request.query_params)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.pdf"'

        doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(data['title'], styles['Title']),
            Spacer(1, 8),
            Paragraph(f"Generated: {datetime.date.today().strftime('%B %d, %Y')}", styles['Normal']),
            Spacer(1, 16),
        ]
        if data.get('summary'):
            story.append(Paragraph(data['summary'], styles['Heading3']))
            story.append(Spacer(1, 12))

        table_data = [data['headers']] + [[str(cell) for cell in row] for row in data['rows']]
        table = Table(table_data, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), pdf_colors.HexColor('#6D28D9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), pdf_colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, pdf_colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ]))
        story.append(table)
        doc.build(story)
        return response


class ReportExportExcelView(APIView):
    permission_classes = [IsReportsStaff]

    def get(self, request, report_type):
        builder = REPORT_BUILDERS.get(report_type)
        if not builder:
            return Response({'detail': f'Unknown report type "{report_type}".'}, status=http_status.HTTP_404_NOT_FOUND)
        data = builder(request.query_params)

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = data['title'][:31]
        ws.append(data['headers'])
        for row in data['rows']:
            ws.append([str(cell) for cell in row])
        wb.save(response)
        return response
