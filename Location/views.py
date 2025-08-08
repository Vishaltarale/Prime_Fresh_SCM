from django.shortcuts import render,redirect
from Location.models import OfficeLocation,Warehouse
from product_Items.models import Product
#WAREHOUSE DASH
from collections import Counter
import plotly.graph_objs as go
import plotly.offline as opy

def location_dash(request):
    warehouses = Warehouse.objects.all()
    warehouse_data = []
    plot_data = []

    for w in warehouses:
        products = Product.objects(warehouse=w)
        warehouse_data.append({
            "warehouse": w,
            "products": products
        })

        # Count stock status
        status_counts = Counter()
        for p in products:
            if p.quantity_available <= 0:
                status_counts["Out of Stock"] += 1
            elif p.quantity_available < 50:
                status_counts["Low Stock"] += 1
            else:
                status_counts["Available"] += 1

        plot_data.append({
            "warehouse": w.warehouse_name,
            "Available": status_counts["Available"],
            "Low Stock": status_counts["Low Stock"],
            "Out of Stock": status_counts["Out of Stock"]
        })

    # Build Plotly Bar Graph
    x = [d["warehouse"] for d in plot_data]
    available = [d["Available"] for d in plot_data]
    low = [d["Low Stock"] for d in plot_data]
    out = [d["Out of Stock"] for d in plot_data]

    trace1 = go.Bar(x=x, y=available, name='Available', marker=dict(color='green'))
    trace2 = go.Bar(x=x, y=low, name='Low Stock', marker=dict(color='orange'))
    trace3 = go.Bar(x=x, y=out, name='Out of Stock', marker=dict(color='red'))

    layout = go.Layout(
        title='Warehouse-wise Product Stock Status',
        barmode='group',
        xaxis=dict(title='Warehouse'),
        yaxis=dict(title='Product Count'),
    )

    figure = go.Figure(data=[trace1, trace2, trace3], layout=layout)
    plot_div = opy.plot(figure, auto_open=False, output_type='div')

    return render(request, 'warehouse_dash.html', {
        'warehouse_data': warehouse_data,
        'plot_div': plot_div
    })

# Create your views here.
def office(request):
    return render(request,"office.html")

def office_register(request):
    if request.method == "POST":
            office_name = request.POST.get("office_name")
            address = request.POST.get("address")
            city = request.POST.get("city")
            state = request.POST.get("state")
            pincode = request.POST.get("pincode")

            # Save to MongoDB using MongoEngine
            office = OfficeLocation(
                office_name=office_name,
                address=address,
                city=city,
                state=state,
                pincode=pincode
            )
            office.save()

            # messages.success(request, "Office location registered successfully.")
            return redirect("Location:office")
    return render(request, "office.html")

#WAREHOUSE
def warehouse(request):
     return render(request,"warehouse.html")

def warehouse_register(request):
    if request.method == "POST":
            warehouse_name = request.POST.get("warehouse_name").strip()
            address = request.POST.get("address").strip()
            city = request.POST.get("city").strip()
            state = request.POST.get("state").strip()
            pincode = request.POST.get("pincode").strip()

            # Optional: Prevent duplicate warehouse names
            if Warehouse.objects(warehouse_name__iexact=warehouse_name).first():
                # messages.warning(request, "Warehouse with this name already exists.")
                return redirect("Location:warehouse")

            warehouse = Warehouse(
                warehouse_name=warehouse_name,
                address=address,
                city=city,
                state=state,
                pincode=pincode
            )
            warehouse.save()
            # messages.success(request, "Warehouse registered successfully.")
            return redirect("Location:warehouse")
    return redirect("Location:warehouse")

def reports(request):
     return render(request,"reports.html")



#For reports generation code......
# views.py for SCM Reports Section
from django.shortcuts import render
from django.http import HttpResponse
import datetime
import openpyxl
from reportlab.pdfgen import canvas
from Orders.models import Order
from django.db.models import Sum
from collections import defaultdict

def inventory_report(request,entity):
    if entity == "inventory":
        products = Product.objects.all()
        
        headers = ["Product", "SKU", "Category", "Subcategory", "UOM", "Quantity", "Warehouse", "Created At"]
        
        rows = []
        for p in products:
            rows.append([
                p.name,
                p.sku,
                p.category,
                p.subcategory,
                p.uom.name if p.uom else "—",
                p.quantity_available,
                p.warehouse.warehouse_name if p.warehouse else "—",
                p.created_at.strftime("%d %b %Y, %I:%M %p") if p.created_at else "—",
            ])
        
        return render(request, 'inventory_report.html', {
            'headers': headers,
            'rows': rows
        })
    
    elif entity == "order":
        orders = Order.objects.all().order_by('-order_date')  # newest first

        headers = ["Order ID", "Customer", "Order Date", "Total Amount", "Status", "Payment Method", "Created At"]
        
        rows = []
        for o in orders:
            rows.append([
                str(o.id),
                o.customer_name if hasattr(o, 'customer_name') else "—",
                o.order_date.strftime("%d %b %Y") if o.order_date else "—",
                f"₹{o.total_amount:.2f}" if hasattr(o, 'total_amount') else "—",
                o.status if hasattr(o, 'status') else "—",
                o.payment_method if hasattr(o, 'payment_method') else "Cash",
                o.created_at.strftime("%d %b %Y, %I:%M %p") if hasattr(o, 'created_at') and o.created_at else "—",
            ])
            return render(request, 'inventory_report.html', {
            'headers': headers,
            'rows': rows
        })
    
    elif entity == "supplier":
        suppliers = Supplier.objects.all()

        headers = [
            "Supplier", "Company", "Email", "Phone",
            "Total Transactions", "Total Amount", "Amount Paid", "Outstanding Dues"
        ]

        rows = []

        for s in suppliers:
            transactions = Order.objects(supplier=s)

            total_amount_agg = list(transactions.aggregate({
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$total_amount"}
                }
            }))
            amount_paid_agg = list(transactions.aggregate({
                "$group": {
                    "_id": None,
                    "paid": {"$sum": "$amount_paid"}
                }
            }))

            # total_amount = total_amount_agg[0]["total"] if total_amount_agg else 0
            # amount_paid = amount_paid_agg[0]["paid"] if amount_paid_agg else 0
            # outstanding = total_amount - amount_paid

            rows.append([
                s.supplier_name,
                s.company_name,
                s.email,
                s.phone,
                transactions.count(),
                # f"₹{total_amount:.2f}",
                # f"₹{amount_paid:.2f}",
                # f"₹{outstanding:.2f}"
            ])

        return render(request, 'inventory_report.html', {
            'headers': headers,
            'rows': rows
        })
    
    elif entity == "warehouse":
        warehouses = Warehouse.objects.all()
        headers = ["Warehouse", "Location", "Total Products", "Total Quantity"]

        rows = []
        for warehouse in warehouses:
            products = Product.objects(warehouse=warehouse)

            total_products = products.count()
            total_quantity = sum([p.quantity_available or 0 for p in products])

            rows.append([
                warehouse.warehouse_name,
                warehouse.address if hasattr(warehouse, 'address') else "—",
                total_products,
                total_quantity
            ])

        return render(request, 'inventory_report.html', {
            'headers': headers,
            'rows': rows
        })
    
    elif entity == "sales":
        orders = Order.objects(status="completed")
     
        headers = ["Order ID", "Customer", "Date", "Total Amount", "Status"]
        rows = []

        for order in orders:
            rows.append([
                str(order.id),
                order.customer_name if hasattr(order, 'customer_name') else "—",
                order.order_date.strftime("%d %b %Y, %I:%M %p") if order.order_date else "—",
                f"₹{order.total_amount:,.2f}" if order.total_amount else "₹0.00",
                order.status.title()
            ])

        total_revenue = sum(order.total_amount for order in orders if order.total_amount)

        return render(request, 'inventory_report.html', {
            'headers': headers,
            'rows': rows,
            'title': "Sales Report",
            'summary': f"Total Revenue: ₹{total_revenue:,.2f}"
        })
    
    elif entity == "expiry":
        today = datetime.datetime.now()
        upcoming_expiry_date = today + datetime.timedelta(days=30)  # configurable threshold
        
        products = Product.objects.filter(
            __raw__={
                "$or": [
                    {"expiry_date": {"$lte": upcoming_expiry_date}},
                    {"quantity_available": {"$lte": 10}}  # Default restock threshold
                ]
            }
        )

        headers = ["Product", "SKU", "UOM", "Qty", "Warehouse", "Expiry Date", "Restock Alert"]

        rows = []
        for p in products:
            expiry_str = p.expiry_date.strftime("%d %b %Y") if hasattr(p, 'expiry_date') and p.expiry_date else "—"
            restock_alert = "Yes" if hasattr(p, 'reorder_level') and p.quantity_available <= p.reorder_level else ("Yes" if p.quantity_available <= 10 else "No")

            rows.append([
                p.name,
                p.sku,
                p.uom.name if p.uom else "—",
                p.quantity_available,
                p.warehouse.warehouse_name if p.warehouse else "—",
                expiry_str,
                restock_alert
            ])

        return render(request, 'inventory_report.html', {
            'headers': headers,
            'rows': rows,
            'title': "Expiry / Restock Alerts",
        })


from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime
from product_Items.models import Product
from Orders.models import Order

def export_pdf(request):
    # Fetch data
    products = Product.objects.all()
    orders = Order.objects.all()

    # Response setup
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="scm_report.pdf"'

    # PDF setup
    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    # Style setup
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['BodyText']

    # Custom paragraph style
    summary_style = ParagraphStyle(
        'summaryStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=18,
        spaceAfter=10,
    )

    # Story = content flow
    story = []

    # Title and date
    story.append(Paragraph("Supply Chain Management Report", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", normal_style))
    story.append(Spacer(1, 24))

    # Summary section
    story.append(Paragraph("📊 Summary", heading_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total Inventory Items: <b>{products.count()}</b>", summary_style))
    story.append(Paragraph(f"Total Orders: <b>{orders.count()}</b>", summary_style))
    story.append(Spacer(1, 24))

    # Top 5 Products Table
    story.append(Paragraph("📦 Top 5 Products (by Quantity Available)", heading_style))
    story.append(Spacer(1, 12))

    product_data = [['Product Name', 'Available Quantity']]  # Table Header
    top_products = products.order_by('-quantity_available')[:5]
    for product in top_products:
        product_data.append([product.name, str(product.quantity_available)])

    table = Table(product_data, hAlign='LEFT', colWidths=[300, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),

        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EAF2F8')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(table)
    story.append(Spacer(1, 30))

    # Footer
    story.append(Paragraph("🧾 Report generated by SCM Dashboard", styles['Normal']))
    story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)
    return response

def export_excel(request):
    from product_Items.models import Product

    products = Product.objects.all()

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="scm_report.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventory"
    ws.append(['Product', 'SKU', 'Qty', 'Warehouse'])

    for p in products:
        ws.append([
            p.name,
            p.sku,
            p.quantity_available,
            p.warehouse.warehouse_name if p.warehouse else "—"
        ])

    wb.save(response)
    return response

