from django.shortcuts import render, redirect
from .models import Order,ProductItem  # If you're using MongoEngine Order model
from mysite.models import FruitInventory
from mongoengine.queryset.visitor import Q
from mysite.models import Customer
from UOM.models import UOMConversionMatrix
from product_Items.models import Product
from UOM.models import UOM,UOMConversionMatrix

def Order_dash(request):
    if 'user_email' in request.session:
        user_email = request.session['user_email']
        data = Order.objects(created_by=user_email)  # Store email in `created_by`
        return render(request, "Order_dash.html", {'Orders': data})
    else:
        return redirect("Users:login_user")

from django.core.serializers.json import DjangoJSONEncoder
import json
from Location.models import Warehouse

def Create_order(request):
    if request.session.get('user_email'):
        customers = Customer.objects.all()
        inventory = Product.objects.all()
        uoms = UOMConversionMatrix.objects.all()
        
        # Prepare JSON data
        product_data = [
            {
                "name": product.name,
                "price": product.price_per_unit,
                "uom": product.uom.name
            } for product in inventory
        ]
        product_json = json.dumps(product_data, cls=DjangoJSONEncoder)

        return render(request, "Order.html", {
            'Customers': customers,
            'inventory': inventory,
            'uoms': uoms,
            'product_json': product_json,
            'warehouses':Warehouse.objects.all()
        })
    else:
        return redirect("Users:login_user")


from django.shortcuts import render, redirect
from Orders.models import Order, ProductItem
from product_Items.models import Product  # Adjust import if your model is in a different app
from Location.models import Warehouse
from django.contrib import messages

def Order_save(request):
    if request.method == "POST":
        customer_name = request.POST.get('customer_name')
        delivery_address = request.POST.get('delivery_address')
        warehouse_id = request.POST.get('warehouse_id')

        product_names = request.POST.getlist('product_name[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        uoms = request.POST.getlist('uom[]')

        items = []
        total_amount = 0

        # Check availability for each product
        for name, qty, price, uom in zip(product_names, quantities, prices, uoms):
            try:
                qty_int = int(qty)
                price_float = float(price)
            except ValueError:
                messages.error(request, "Invalid quantity or price format.")
                return redirect("Orders:Order_create")

            #  Check stock in the selected warehouse
            product = Product.objects(name=name, warehouse=warehouse_id).first()

            if not product:
                messages.error(request, f"Product '{name}' not found in selected warehouse.")
                return redirect("Orders:Create_order")

            if product.quantity_available < qty_int:
                messages.error(request, f"Product '{name}' is out of stock or has insufficient quantity.")
                return redirect("Orders:Create_order")

            # Prepare item
            items.append(ProductItem(
                product_name=name,
                quantity=qty_int,
                price=price_float,
                uom=uom
            ))
            total_amount += qty_int * price_float

        user_email = request.session.get('user_email')
        if not user_email:
            messages.error(request, "Please log in to place an order.")
            return redirect("Users:login_user")

        Order.objects.create(
            customer_name=customer_name,
            delivery_address=delivery_address,
            items=items,
            total_amount=total_amount,
            status="Pending",
            payment_status="Unpaid",
            created_by=user_email,
            warehouse=warehouse_id
        )
        messages.success(request, "Order placed successfully.")
        return redirect("Orders:Order_dash")

    return render(request, "Order.html")



def orderedit(request):
    id = request.GET['id']
    order = Order.objects(id=id).first()
    status_choices = ["Pending", "Processing", "Completed", "Cancelled"]
    payment_choices = ["Paid", "Unpaid"]
    customers = Customer.objects.all() 
    warehouses = Warehouse.objects.all()
    
    
    return render(request, "orderedit.html", {
        "products":Product.objects.all(),
        "order": order,
        'uoms':UOM.objects.all(),
        "status_choices": status_choices,
        "payment_choices": payment_choices,
        "Customers": customers,
        "warehouses":warehouses
    })

from django.core.exceptions import ValidationError
def Order_update(request):
    if request.method == "POST":
        try:
            customer_name = request.POST['customer_name']
            delivery_address = request.POST['delivery_address']
            status = request.POST['status']
            payment_status = request.POST['payment_status']
            warehouse_id = request.POST.get('warehouse_id')
            order_id = request.GET.get("id")

            # Get warehouse
            selected_warehouse = Warehouse.objects(id=warehouse_id).first()

            product_names = request.POST.getlist('product_name[]')
            quantities = request.POST.getlist('quantity[]')
            prices = request.POST.getlist('price[]')
            uoms = request.POST.getlist('uom[]')

            if not (len(product_names) == len(quantities) == len(prices) == len(uoms)):
                raise ValidationError("Mismatched order item fields.")

            items = []
            total_amount = 0

            for name, qty, price, uom_name in zip(product_names, quantities, prices, uoms):
                product = Product.objects(name=name, warehouse=selected_warehouse).first()
                if not product:
                    raise ValidationError(f"Product '{name}' not found in selected warehouse.")

                user_uom = UOM.objects(name=uom_name).first()
                if not user_uom:
                    raise ValidationError(f"UOM '{uom_name}' not found.")

                # Unit conversion if necessary
                if product.uom != user_uom:
                    conversion = UOMConversionMatrix.objects(
                        from_uom=user_uom,
                        to_uom=product.uom
                    ).first()
                    if not conversion:
                        raise ValidationError(
                            f"No conversion from {uom_name} to {product.uom.name} for {name}."
                        )
                    converted_qty = float(qty) * conversion.factor
                else:
                    converted_qty = float(qty)

                items.append({
                    "product_name": name,
                    "quantity": converted_qty,
                    "uom": uom_name,
                    "price": float(price),
                })

                total_amount += converted_qty * float(price)

            # Update order
            Order.objects(id=order_id).update(
                set__customer_name=customer_name,
                set__delivery_address=delivery_address,
                set__status=status,
                set__payment_status=payment_status,
                set__warehouse=selected_warehouse,
                set__items=items,
                set__total_amount=total_amount,
            )

            # Deduct from warehouse-specific stock if status is completed
            if status == "Completed":
                for item in items:
                    product = Product.objects(name=item["product_name"], warehouse=selected_warehouse).first()
                    if not product:
                        continue
                    if product.quantity_available < item["quantity"]:
                        raise ValidationError(
                            f"Not enough stock for {item['product_name']} in warehouse '{selected_warehouse.name}'. "
                            f"Available: {product.quantity_available}, Required: {item['quantity']}"
                        )
                    product.quantity_available -= item["quantity"]
                    product.save()

            return redirect("Orders:admin_customer_orders")

        except ValidationError as ve:
            order = Order.objects(id=request.GET.get("id")).first()
            customers = Customer.objects()
            products = Product.objects()
            warehouses = Warehouse.objects()
            status_choices = ["Pending", "Completed", "Cancelled"]
            payment_choices = ["Unpaid", "Paid", "Partially Paid"]
            uoms = UOM.objects()

            return render(request, "Orders/OrderEdit.html", {
                "error": str(ve),
                "order": order,
                "Customers": customers,
                "products": products,
                "warehouses": warehouses,
                "status_choices": status_choices,
                "payment_choices": payment_choices,
                "uoms": uoms,
            })
        
def orderdelete(request):
    id = request.GET['id']
    Order.objects(id=id).first().delete()
    return redirect("Orders:Order_dash")

#ADMIN_CUSTOMER_ORDERS
def admin_customer_orders(request):
    orders = Order.objects.all()
    return render(request,'admin_customer_orders.html',{'Orders':orders})

from django.shortcuts import render, get_object_or_404
from Orders.models import Order
def generate_invoice(request):
    order_id = request.GET.get("id")
    order = Order.objects(id=order_id).first()
    
    if not order:
        return redirect("some_error_page_or_custom_404")  # Optional: handle missing order

    return render(request, "invoice.html", {
        "order": order,
    })

from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse
from django.core.mail import EmailMessage
from xhtml2pdf import pisa
import io
from .models import Order  # MongoEngine model


import io
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from Orders.models import Order  # adjust to your app name

def generate_invoice_pdf(request, order_id):
    order = Order.objects.get(id=order_id)

    # 1. Render invoice template to HTML
    template = get_template('invoice.html')
    html = template.render({'order': order})

    # 2. Generate PDF from HTML
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=pdf_buffer)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    pdf_value = pdf_buffer.getvalue()

    # 3. Send email with attachment
    email = EmailMessage(
            subject=f"Invoice #{order.id} - SCM Company",
            body="Please find your invoice attached.",
            from_email="vishaltarale055@gmail.com",
            to=['taralevishal82@gmail.com'],  # Make sure this field exists
        )
    email.attach(f"Invoice_{order.id}.pdf", pdf_value, 'application/pdf')
    email.send()

    # 4. Optional: return PDF as response
    response = HttpResponse(pdf_value, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.id}.pdf"'
    return response


