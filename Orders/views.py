from django.shortcuts import render, redirect
from .models import Order,ProductItem  # If you're using MongoEngine Order model
from mysite.models import FruitInventory
from mongoengine.queryset.visitor import Q
from mysite.models import Customer
from UOM.models import UOMConversionMatrix
# from product_Items.models import Product
from UOM.models import UOM,UOMConversionMatrix
from product_Items.models  import Product
from Orders.models import BillItem,FinalCustomerBill

from django.core.serializers.json import DjangoJSONEncoder
import json
from Location.models import Warehouse
from product_Items.models import Category,Subcategory

from django.shortcuts import render, redirect
from Orders.models import Order, ProductItem
# from product_Items.models import Product  # Adjust import if your model is in a different app
from Location.models import Warehouse
from django.contrib import messages
from product_Items.models import Product
import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order, TransportChallan, TCProductItem
from product_Items.models import Product, Category, Subcategory
from Location.models import Warehouse
from mysite.models import Customer
import datetime

from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from io import BytesIO
import datetime

from .models import TransportChallan
from mysite.models import Customer  # adjust import path to your Customer model


from mysite.models import Customer

import os, re, email, imaplib, datetime
from bson import ObjectId
from django.conf import settings
from django.shortcuts import render
from Orders.models import TCResponse, TransportChallan

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import os, datetime

from product_Items.models import Product, Category, Subcategory
from Location.models import Warehouse
from mysite.models import Customer
from .models import TCResponse, FinalCustomerBill, BillItem


import pdfplumber
import PyPDF2
import re
from decimal import Decimal, InvalidOperation

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
from Orders.models import Order,FinalCustomerBill  # adjust to your app name

from Users.models import User1
from Users.models import User1
from mongoengine.queryset.visitor import Q

def Order_dash(request):
    if request.session.get("user_email") is None:
        return redirect("Users:login_user")

    user_email = request.session["user_email"]
    user_role = request.session.get("user_role")

    # Get orders based on user role
    if user_role == "Admin":
        # Admin can see all orders
        orders = Order.objects.all()
        final_bills = FinalCustomerBill.objects.all()
    elif user_role == "Sales_Manager":
        # Sales Manager can see orders created by customers and themselves
        # First, get all customer emails
        customer_users = User1.objects.filter(role="Customer") or User1.objects.filter(role__iexact="Sales_Manager")
        customer_emails = [user.email for user in customer_users]
        
        # Add current sales manager's email
        customer_emails.append(user_email)
        
        # Filter orders by the email list
        orders = Order.objects.filter(created_by__in=customer_emails)
        final_bills = FinalCustomerBill.objects.filter(created_by__in=customer_emails)
    elif user_role == "Customer":
        # Customer can only see their own orders
        orders = Order.objects.filter(created_by=user_email)
        final_bills = FinalCustomerBill.objects.filter(created_by=user_email)
    else:
        orders = Order.objects.none()
        final_bills = FinalCustomerBill.objects.none()

    # Order counts
    pending_count = orders.filter(status="Pending").count()
    completed_count = orders.filter(status="Completed").count()

    # Revenue (sum total_amount safely)
    completed_bills = final_bills.filter(orderstatus="Completed")
    revenue = sum(bill.total_amount for bill in completed_bills) if completed_bills else 0

    print(f"User Role: {user_role}, Orders Count: {orders.count()}")
    print(f"Pending: {pending_count}, Completed: {completed_count}")

    context = {
        "orders": orders,
        "pending_count": pending_count,
        "completed_count": completed_count,
        "revenue": revenue,
        "user_role": user_role,
    }
    return render(request, "Order_dash.html", context)

def Create_order(request):
    if request.session.get("user_email") and request.session.get("user_role")=="Customer" or "Sales_Manager"  or 'Admin':
        customers = Customer.objects.all()
        warehouses = Warehouse.objects.all()
        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()
        uoms = UOM.objects.all()

        # Flatten all ProductItems for the dropdown
        product_items = []
        for product in Product.objects.all():
            for item in product.items:
                product_items.append({
                    "id": str(product.id),
                    "product_name": item.product_name,
                    "sku": item.sku,
                    "category": str(item.category.id),
                    "subcategory": str(item.subcategory.id),
                    "uom": item.uom,
                    "price": item.price,
                    "warehouse": str(product.warehouse.id) if product.warehouse else "",
                })

        return render(request, "Order.html", {
            "Customers": customers,
            "warehouses": warehouses,
            "categories": categories,
            "subcategories": subcategories,
            "uoms": uoms,
            "products": product_items,  # pass flattened items
        })
    else:
        return redirect("Users:login_user")


def Order_save(request):
    if not request.session.get('user_email'):
        return redirect("Users:login_user")

    if request.method == "POST":
        user_email = request.session['user_email']
        customer_name = request.POST.get('customer_name')
        delivery_address = request.POST.get('delivery_address')
        warehouse_id = request.POST.get('warehouse_id')
        warehouse = Warehouse.objects(id=warehouse_id).first() if warehouse_id else None

        if not warehouse:
            messages.error(request, "Please select a valid warehouse.")
            return redirect('Orders:Create_order')

        # Get product rows
        product_names = request.POST.getlist('product_name[]')
        skus = request.POST.getlist('sku[]')
        categories = request.POST.getlist('category[]')
        subcategories = request.POST.getlist('subcategory[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        uoms = request.POST.getlist('uom[]')

        items = []       
        total_amount = 0
        error_flag = False

        for i in range(len(product_names)):
            product_name = product_names[i]
            sku = skus[i]
            qty = int(quantities[i])
            price = float(prices[i])

            # ✅ Check availability in ProductItems of selected warehouse
            inventory_item = None
            for prod in Product.objects(warehouse=warehouse):
                for pi in prod.items:
                    if pi.product_name == product_name and pi.quantity >= qty:
                        inventory_item = pi
                        break
                if inventory_item:
                    break

            if not inventory_item:
                messages.error(
                    request,
                    f"Product '{product_name}' is not available in the selected warehouse "
                    f"or does not have sufficient quantity."
                )
                error_flag = True
                break

            total_amount += qty * price

            # Create ProductItem to save in order
            item = ProductItem(
                product_name=product_name,
                sku=sku,
                category=Category.objects(id=categories[i]).first() if categories[i] else None,
                subcategory=Subcategory.objects(id=subcategories[i]).first() if subcategories[i] else None,
                quantity=qty,
                price=price,
                uom=uoms[i],
            )
            items.append(item)

        if error_flag:
            return redirect('Orders:Create_order')

        # Save order
        order = Order(
            customer_name=customer_name,
            delivery_address=delivery_address,
            warehouse=warehouse,
            items=items,
            total_amount=total_amount,
            created_by=user_email,
            order_date=datetime.date.today()
        )
        order.save()

        messages.success(request, "Order created successfully.")
        return redirect('Orders:Order_dash')

    return redirect('Orders:Create_order')

def orderedit(request):
    if not request.session.get("user_email") and request.session.get("user_role") == "Sales_Manager" or "Customer" or 'Admin':
            
        order_id = request.GET.get('id')
        order = Order.objects(id=order_id).first()
        products = Product.objects.all()

        if not order:
            return redirect("Orders:Order_dash")

        if request.method == "POST":
            # Update order details
            order.customer_name = request.POST.get("customer_name")
            order.delivery_address = request.POST.get("delivery_address")
            order.warehouse_id = request.POST.get("warehouse_id")

            # Handle product items
            product_names = request.POST.getlist("product_name[]")
            skus = request.POST.getlist("sku[]")
            categories = request.POST.getlist("category[]")
            subcategories = request.POST.getlist("subcategory[]")
            quantities = request.POST.getlist("quantity[]")
            uoms = request.POST.getlist("uom[]")
            prices = request.POST.getlist("price[]")

            new_items = []
            for i in range(len(product_names)):
                if product_names[i]:  # skip empty rows
                    item = ProductItem(
                        product_name=product_names[i],
                        sku=skus[i],
                        category=categories[i] if categories[i] else None,
                        subcategory=subcategories[i] if subcategories[i] else None,
                        quantity=int(quantities[i]) if quantities[i] else 0,
                        uom=uoms[i],
                        price=float(prices[i]) if prices[i] else 0.0,
                    )
                    new_items.append(item)

            order.items = new_items
            order.save()
            return redirect("Orders:Order_dash")

        return render(request, "orderedit.html", {
            "order": order,
            "products": products,
            "categories": Category.objects.all(),
            "subcategories": Subcategory.objects.all(),
            "warehouses": Warehouse.objects.all(),
            "customers": Customer.objects.all(),
        })
    else:
        return redirect("Users:login_user")



# --------------------------------------------------------------------------------------------CREATING TRANSPORT CHALLAN -----------------------------------------------------------------------------------------
def ordertransportchallen(request):
    if request.session.get("user_email") and request.session.get("user_role") == "Sales_Manager" or 'Admin':
        print(request.session.get('user_role'))
        order_id = request.GET.get("id") or request.POST.get("order_id")
        order = Order.objects(id=order_id).first() if order_id else None

        if request.method == "POST":
            if not order:
                messages.error(request, "Invalid order selected.")
                return redirect("Orders:Order_dash")

            customer_id = request.POST.get('customer')  # since order is linked to a customer
            customer = order.customer_name if order else None
            # Fetch customer object if needed
            delivery_address = request.POST.get("delivery_address")
            warehouse_id = request.POST.get("warehouse_id")
            warehouse = Warehouse.objects(id=warehouse_id).first() if warehouse_id else None
            challan_date = request.POST.get("challan_date") or datetime.date.today()
            vehicle_number = request.POST.get("vehicle_number")
            driver_name = request.POST.get("driver_name")
            driver_contact = request.POST.get("driver_contact")
            transport_agency = request.POST.get("transport_agency")
            dispatch_date = request.POST.get("dispatch_datetime")
            transporatation_bill = float(request.POST.get("transportation_bill")) if request.POST.get("transportation_bill") else 0.0
            created_by = request.session.get("user_email", "unknown")
            
            sub_total = request.POST.get("sub_total")
            gst_total = request.POST.get("gst_total")
            grand_total = request.POST.get("grand_total")

            # Copy items directly from order
            new_items = []
            subtotal_amount, gst_amount, total_amount = 0, 0, 0

            for oi in order.items:
                item = TCProductItem(
                    product_name=oi.product_name,
                    sku=oi.sku,
                    category=oi.category,
                    subcategory=oi.subcategory,
                    quantity=oi.quantity,
                    uom=oi.uom,
                    price=oi.price,
                    gst=18.0,  # Assuming a flat 18% GST for simplicity
                    total= oi.quantity * oi.price * 1.18  # price + gst
                )
                new_items.append(item)

                subtotal_amount = sub_total if sub_total else oi.quantity * oi.price
                gst_amount = gst_total if gst_total else oi.quantity * oi.price * 0.18
                total_amount = grand_total if grand_total else oi.quantity * oi.price * 1.18 + (transporatation_bill if transporatation_bill else 0)

            challan = TransportChallan(
                order=order,
                custoomer_name=customer,
                delevery_address=delivery_address,
                warehouse=warehouse,
                orderstatus="Created",
                challan_date=challan_date,
                items=new_items,
                created_by=created_by,
                transport_details=transport_agency,
                vehicle_number=vehicle_number,
                driver_name=driver_name,
                driver_contact=driver_contact,
                dispatch_date=dispatch_date,
                transportation_bill=float(transporatation_bill) if transporatation_bill else 0.0,
                subtotal_amount=subtotal_amount,
                gst_amount=gst_amount,
                total_amount=total_amount,
                
            )
            challan.save()
            messages.success(request, "Transport Challan created successfully.")
            return redirect("Orders:Order_dash")

        context =  {
            "order": order,
            "customers": Customer.objects.all(),
            "warehouses": Warehouse.objects.all(),
            "products": Product.objects.all(),
            "categories": Category.objects.all(),
            "subcategories": Subcategory.objects.all(),
            "po": TransportChallan.objects(order=order).first() if order else None,
        }
        return render(request, "ordertransportchallen.html", context)
    else:
        return redirect("Users:login_user")

# --------------------------------------------------------------------------------------------TRANSPORT CHALLAN DASHBOARD -----------------------------------------------------------------------------------------
def transport_challan_view(request):
    if request.session.get("user_email") and request.session.get("user_role") == "Sales_Manager" or 'Admin':
        user = request.session.get('user_email')
        challans = TransportChallan.objects(created_by=user)
        return render(request, "transportchallendash.html", {"challans": challans})
    return redirect("Users:login_user")


# --------------------------------------------------------------------------------------------ACTIONS IN TC-----------------------------------------------------------------------------------------
def TCEdit(request):
    if request.session.get("user_email") and request.session.get("user_role") == "Sales_Manager" or 'Admin':
        challan_id = request.GET.get('id')
        challan = TransportChallan.objects(id=challan_id).first()
        products = Product.objects.all()

        if not challan:
            return redirect("Orders:transport_challan_view")

        if request.method == "POST":
            # Update challan details
            challan.custoomer_name = request.POST.get("customer_name")
            challan.delevery_address = request.POST.get("delivery_address")
            challan.warehouse_id = request.POST.get("warehouse_id")

            # Handle product items
            product_names = request.POST.getlist("product_name[]")
            skus = request.POST.getlist("sku[]")
            categories = request.POST.getlist("category[]")
            subcategories = request.POST.getlist("subcategory[]")
            quantities = request.POST.getlist("quantity[]")
            uoms = request.POST.getlist("uom[]")
            prices = request.POST.getlist("price[]")

            new_items = []
            for i in range(len(product_names)):
                if product_names[i]:  # skip empty rows
                    item = TCProductItem(
                        product_name=product_names[i],
                        sku=skus[i],
                        category=categories[i] if categories[i] else None,
                        subcategory=subcategories[i] if subcategories[i] else None,
                        quantity=int(quantities[i]) if quantities[i] else 0,
                        uom=uoms[i],
                        price=float(prices[i]) if prices[i] else 0.0,
                        gst=18.0,  # Assuming a flat 18% GST for simplicity
                        total=(int(quantities[i]) * float(prices[i]) * 1.18) if quantities[i] and prices[i] else 0.0,
                    )
                    new_items.append(item)

            challan.items = new_items
            challan.save()
            return redirect("Orders:transport_challan_view")

        return render(request, "TCEdit.html", {
            "challan": challan,
            "products": products,
            "categories": Category.objects.all(),
            "subcategories": Subcategory.objects.all(),
            "warehouses": Warehouse.objects.all(),
            "customers": Customer.objects.all(),
        })
    else:
        return redirect("Users:login_user")

#DELETE Challan 
def TCDelete(request):
    if request.session.get("user_email") and request.session.get("user_role") == "Sales_Manager" or 'Admin':
        challan_id = request.GET.get('id')
        challan = TransportChallan.objects(id=challan_id).first()
        if challan:
            challan.delete()
            messages.success(request, "Transport Challan deleted successfully.")
        else:
            messages.error(request, "Transport Challan not found.")
            return redirect("Orders:transport_challan_view")
    else:
        return redirect("Users:login_user")


# ------------------------------------------------------------------------------------MAIL SENDING AND PDF DOWNLOAD---------------------------------------------------------------------------------
# Orders/views.py
#Generating PDFS

def generate_challan_pdf_bytes(challan):
    invoice_number = f"TC/{challan.challan_date:%Y%m%d}/{str(challan.id)[-6:]}" if getattr(challan, 'challan_date', None) else f"TC/{str(challan.id)[-6:]}"
    context = {
        'challan': challan,
        'challan_id': str(challan.id),
        'invoice_number': invoice_number,
        'company_name': getattr(settings, 'COMPANY_NAME', ''),
        'company_address': getattr(settings, 'COMPANY_ADDRESS', ''),
        'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
        'company_email': getattr(settings, 'COMPANY_EMAIL', ''),
        'current_date': timezone.localtime(timezone.now()).strftime('%d %b %Y'),
    }

    # Render HTML
    html_string = render_to_string('tc_invoice_pdf.html', context)

    # Generate PDF (use small embedded CSS or stylesheet)
    font_config = FontConfiguration()
    css = CSS(string="""
        @page { size: A4; margin: 1in; }
        body { font-family: 'DejaVu Sans', Arial, sans-serif; }
    """)
    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(target=pdf_file, stylesheets=[css], font_config=font_config)
    pdf_file.seek(0)
    return pdf_file, context

def TC_sent_email(request):
    """
    View that generates invoice PDF for a TransportChallan and sends it to the customer email.
    Expects GET param ?id=<challan_id>
    """
    challan_id = request.GET.get('id')
    if not challan_id:
        messages.error(request, "No challan id provided.")
        return HttpResponseRedirect(reverse('Orders:transport_challan_view'))

    challan = TransportChallan.objects(id=challan_id).first()
    if not challan:
        messages.error(request, "Transport Challan not found.")
        return HttpResponseRedirect(reverse('Orders:transport_challan_view'))

    # Determine recipient email: attempt a few fallbacks
    recipient_email = None
    recipient_name = challan.custoomer_name or ''

    # Attempt to find a Customer object by name if you store email there
    try:
        cust_obj = Customer.objects(full_name=challan.custoomer_name).first() if challan.custoomer_name else None
        if cust_obj and getattr(cust_obj, 'email', None):
            recipient_email = cust_obj.email
            recipient_name = getattr(cust_obj, 'full_name', recipient_name)
    except Exception:
        recipient_email = None

    # If still no email, try order relation if present
    try:
        if not recipient_email and getattr(challan, 'order', None):
            order = challan.order
            # If order has a customer reference with email
            if getattr(order, 'customer', None) and getattr(order.customer, 'email', None):
                recipient_email = order.customer.email
                recipient_name = getattr(order.customer, 'full_name', recipient_name)
    except Exception:
        pass

    if not recipient_email:
        messages.error(request, "Customer email not found. Email not sent.")
        return HttpResponseRedirect(reverse('Orders:transport_challan_view'))

    # Generate PDF
    try:
        pdf_file, context = generate_challan_pdf_bytes(challan)
    except Exception as e:
        messages.error(request, f"Error generating PDF: {e}")
        return HttpResponseRedirect(reverse('Orders:transport_challan_view'))

    # Prepare email content
    invoice_number = context['invoice_number']
    subject = f"- TC_ID:{challan_id}"
    html_body = render_to_string('tc_email_template.html', {
        'recipient_name': recipient_name,
        'invoice_number': invoice_number,
        'current_date': context['current_date'],
        'company_name': context['company_name'],
        'company_email': context['company_email'],
        'challan': challan,
    })
    text_body = render_to_string('tc_email_template.txt', {
        'recipient_name': recipient_name,
        'invoice_number': invoice_number,
        'current_date': context['current_date'],
        'company_name': context['company_name'],
        'challan': challan,
    })

    try:
        email = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [recipient_email])
        email.attach_alternative(html_body, "text/html")
        pdf_name = f"{invoice_number}.pdf"
        email.attach(pdf_name, pdf_file.getvalue(), "application/pdf")
        email.send()
        messages.success(request, f"Invoice sent to {recipient_email}.")
    except Exception as e:
        messages.error(request, f"Error sending email: {e}")
        return HttpResponseRedirect(reverse('Orders:transport_challan_view'))

    # Optionally redirect back to challan listing or detail
    return HttpResponseRedirect(reverse('Orders:transport_challan_view'))


# Download PDF
def transport_challan_pdf_download(request):
    challan_id = request.GET.get('id')
    challan = TransportChallan.objects(id=challan_id).first()
    if not challan:
        messages.error(request, "Challan not found.")
        return HttpResponseRedirect(reverse('Orders:transport_challan_view'))

    pdf_file, context = generate_challan_pdf_bytes(challan)
    filename = f"TransportChallan_{str(challan.id)}.pdf"
    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# --------------------------------------------------------------------------------------------CustomerReplies-----------------------------------------------------------------------------------------
# Directory for saving attachments
ATTACHMENTS_DIR = os.path.join(settings.MEDIA_ROOT, "TC_attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

def parse_tc_reply(body: str) -> dict:
    """Extract structured TC response fields from email body."""
    details = {}

    patterns = {
        "challan_id": r"Challan ID:\s*([a-f0-9]{24})",
        "message": r"Message:\s*(.*)"
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            details[field] = match.group(1).strip()

    return details


def fetch_tc_emails():
    """Fetch Transport Challan response emails via IMAP."""
    mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
    mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    if status != "OK":
        return

    mail_ids = messages[0].split()
    latest_5 = mail_ids[-5:]  # last 5 emails only

    for num in latest_5[::-1]:  # newest first
        status, data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue

        msg = email.message_from_bytes(data[0][1])
        sender = msg["From"]
        subject = msg.get("Subject", "")
        body = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get("Content-Disposition"))

                # Extract plain text body
                if ctype == "text/plain" and "attachment" not in disp:
                    body = part.get_payload(decode=True).decode(errors="ignore")

                # Extract attachments
                elif "attachment" in disp:
                    filename = part.get_filename()
                    if filename:
                        filepath = os.path.join(ATTACHMENTS_DIR, filename)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        attachments.append(f"TC_attachments/{filename}")  # relative path
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        # Extract challan ID from subject/body
        full_text = subject + " " + body
        match = re.search(r"([a-f0-9]{24})", full_text)
        if not match:
            continue

        challan_id = match.group(1).strip()
        challan = TransportChallan.objects(id=ObjectId(challan_id)).first()
        if not challan:
            continue

        # Avoid duplicate save
        existing = TCResponse.objects(
            challan=challan,
            customer=sender,
            message=body.strip()
        ).first()

        if not existing:
            TCResponse(
                challan=challan,
                customer=sender,
                message=body.strip(),
                attachments=attachments
            ).save()

    mail.logout()


def customer_replies(request):
    fetch_tc_emails()  # call fetcher (later, schedule via cron/celery)
    replies = TCResponse.objects.order_by("-received_at")
    return render(request, "customer_replies.html", {"replies": replies})


#___________________________________________Creating final Bill____________________________________________________________
def create_final_bill(request):
    if request.session.get("user_email") and request.session.get("user_role") in ["Sales_Manager", "Admin"]:
        response_id = request.GET.get("id")
        response = TCResponse.objects(id=response_id).first()
        if not response:
            messages.error(request, "Invalid Response ID")
            return redirect("Orders:customer_replies")

        challan = response.challan
        pdf_items = []

        # ---------------- Extract items from PDF attachments ----------------
        for file in response.attachments:
            filepath = os.path.join(settings.MEDIA_ROOT, file)
            if filepath.endswith(".pdf") and os.path.exists(filepath):
                pdf_items.extend(extract_items_from_pdf(filepath))

        # ---------------- Handle POST Submission ----------------
        if request.method == "POST":
            if not challan:
                messages.error(request, "Invalid order selected.")
                return redirect("Orders:Order_dash")

            # --- Parse form fields safely ---
            delivery_address = request.POST.get("delivery_address", "").strip()
            warehouse_id = request.POST.get("warehouse_id")
            warehouse = Warehouse.objects(id=warehouse_id).first() if warehouse_id else None

            # Parse challan date
            challan_date_str = request.POST.get("challan_date")
            try:
                challan_date = (
                    datetime.datetime.strptime(challan_date_str, "%Y-%m-%d").date()
                    if challan_date_str else datetime.date.today()
                )
            except Exception:
                challan_date = datetime.date.today()

            vehicle_number = request.POST.get("vehicle_number", "").strip()
            driver_name = request.POST.get("driver_name", "").strip()
            driver_contact = request.POST.get("driver_contact", "").strip()
            transport_agency = request.POST.get("transport_agency", "").strip()

            # Parse dispatch date
            dispatch_date_str = request.POST.get("dispatch_date")
            try:
                dispatch_date = (
                    datetime.datetime.strptime(dispatch_date_str, "%Y-%m-%d").date()
                    if dispatch_date_str else None
                )
            except Exception:
                dispatch_date = None

            transportation_bill = float(request.POST.get("transportation_bill") or 0.0)
            created_by = request.session.get("user_email", "unknown")

            # Optional totals (manual entry override)
            sub_total = float(request.POST.get("sub_total") or 0.0)
            gst_total = float(request.POST.get("gst_total") or 0.0)
            grand_total = float(request.POST.get("grand_total") or 0.0)

            # ---------------- Build Bill Items ----------------
            items = []
            names = request.POST.getlist("product_name[]")
            skus = request.POST.getlist("sku[]")
            cats = request.POST.getlist("category[]")
            subs = request.POST.getlist("subcategory[]")
            qtys = request.POST.getlist("quantity[]")
            prices = request.POST.getlist("price[]")
            uoms = request.POST.getlist("uom[]") 
            gst_vals = request.POST.getlist("gst[]")
            line_totals = request.POST.getlist("line_total[]")

            subtotal_amount, gst_amount, total_amount = 0.0, 0.0, 0.0

            # ✅ Protect against mismatched list lengths
            row_count = min(len(names), len(skus), len(cats), len(subs),
                            len(qtys), len(prices), len(uoms), len(gst_vals), len(line_totals))

            for i in range(row_count):
                try:
                    category = Category.objects(name=cats[i]).first() if cats[i] else None
                    subcategory = Subcategory.objects(name=subs[i]).first() if subs[i] else None

                    qty = int(qtys[i]) if qtys[i] else 0
                    price = float(prices[i]) if prices[i] else 0.0
                    gst_value = float(gst_vals[i]) if gst_vals[i] else 0.0
                    line_total = float(line_totals[i]) if line_totals[i] else qty * price

                    item = BillItem(
                        product_name=names[i],
                        sku=skus[i],
                        category=category,
                        subcategory=subcategory,
                        quantity=qty,
                        price=price,
                        uom=uoms[i] if uoms[i] else None,
                        gst=gst_value,
                        total=line_total,
                    )
                    items.append(item)

                    subtotal_amount += qty * price
                    gst_amount += (qty * price) * (gst_value / 100)
                    total_amount += line_total

                except Exception as e:  
                    messages.warning(request, f"Error processing item {i+1}: {str(e)}")

            # --- Override with manual totals if provided ---
            if sub_total:
                subtotal_amount = sub_total
            if gst_total:
                gst_amount = gst_total
            if grand_total:
                total_amount = grand_total
            else:
                total_amount += transportation_bill

            # ---------------- Create Final Bill ----------------
            try:
                # Debug: Print available attributes of challan object
                print("Available attributes in challan:", dir(challan))
                print("Challan order:", getattr(challan, 'order', None))
                
                # Get customer name from the correct source
                customer_name = None
                
                # Try different possible sources for customer name
                if hasattr(challan, 'customer_name'):
                    customer_name = challan.customer_name
                elif hasattr(challan, 'custoomer_name'):  # Your original spelling
                    customer_name = challan.custoomer_name
                elif hasattr(challan, 'customer') and challan.customer:
                    customer_name = getattr(challan.customer, 'name', None)
                elif hasattr(challan, 'order') and challan.order:
                    if hasattr(challan.order, 'customer_name'):
                        customer_name = challan.order.customer_name
                    elif hasattr(challan.order, 'customer') and challan.order.customer:
                        customer_name = getattr(challan.order.customer, 'name', None)
                
                # If still no customer name, use a default
                if not customer_name:
                    customer_name = "Customer"
                    messages.warning(request, "Customer name not found, using default.")

                final_bill = FinalCustomerBill(
                    challan=challan,
                    response=response,
                    customer_name=challan.custoomer_name,  # Use the correctly sourced customer name
                    delevery_address=delivery_address,
                    warehouse=warehouse,
                    orderstatus="Completed",
                    bill_date=challan_date,
                    items=items,
                    created_by=created_by,
                    transport_details=transport_agency,
                    vehicle_number=vehicle_number,
                    driver_name=driver_name,
                    driver_contact=driver_contact,
                    dispatch_date=dispatch_date,
                    transportation_bill=transportation_bill,
                    subtotal_amount=subtotal_amount,
                    gst_amount=gst_amount,
                    total_amount=total_amount,
                )
                final_bill.save()

                # --- Update related order status ---
                if challan.order:
                    challan.order.status = "Completed"
                    challan.order.save()

                # --- Deduct products from inventory with warehouse check ---
                if not warehouse:
                    messages.error(request, "Warehouse not specified. Inventory not updated.")
                else:
                    inventory_updated = True
                    inventory_warnings = []
                    
                    for bill_item in items:
                        # Find product in the SPECIFIED warehouse with matching SKU
                        product = Product.objects(
                            items__sku=bill_item.sku,
                            warehouse=warehouse
                        ).first()
                        
                        if not product:
                            warning_msg = f"Product with SKU {bill_item.sku} not found in warehouse {warehouse.name}."
                            messages.warning(request, warning_msg)
                            inventory_warnings.append(warning_msg)
                            inventory_updated = False
                            continue

                        # Update the specific product item quantity in this warehouse
                        updated = False
                        for prod_item in product.items:
                            if prod_item.sku == bill_item.sku:
                                if prod_item.quantity >= bill_item.quantity:
                                    old_quantity = prod_item.quantity
                                    prod_item.quantity -= bill_item.quantity
                                    updated = True
                                    
                                    messages.success(
                                        request,
                                        f"Deducted {bill_item.quantity} of {bill_item.product_name} "
                                        f"from warehouse {warehouse.warehouse_name}. Remaining: {prod_item.quantity}"
                                    )
                                else:
                                    warning_msg = (
                                        f"Not enough stock for {bill_item.product_name} in warehouse {warehouse.name}. "
                                        f"Requested: {bill_item.quantity}, Available: {prod_item.quantity}"
                                    )
                                    messages.warning(request, warning_msg)
                                    inventory_warnings.append(warning_msg)
                                    updated = True
                                break

                        if updated:
                            try:
                                product.save()
                            except Exception as e:
                                error_msg = f"Error saving product {bill_item.product_name}: {str(e)}"
                                messages.error(request, error_msg)
                                inventory_updated = False
                        else:
                            warning_msg = f"SKU {bill_item.sku} not found in product items for warehouse {warehouse.name}."
                            messages.warning(request, warning_msg)
                            inventory_warnings.append(warning_msg)
                            inventory_updated = False

                    if inventory_updated and not inventory_warnings:
                        messages.success(request, "Final Customer Bill created successfully and inventory updated.")
                    elif inventory_warnings:
                        messages.warning(request, "Bill created but with some inventory warnings.")
                    else:
                        messages.error(request, "Bill created but inventory update failed.")

                return redirect("Orders:Order_dash")

            except Exception as e:
                messages.error(request, f"Error saving Final Bill: {str(e)}")
                import traceback
                print(f"Error details: {traceback.format_exc()}")
                return redirect("Orders:customer_replies")

        # ---------------- GET Request ----------------
        context = {
            "challan": challan,
            "items": pdf_items,
            "response": response,
            "categories": Category.objects.all(),
            "subcategories": Subcategory.objects.all(),
            "warehouses": Warehouse.objects.all(),
            "customers": Customer.objects.all(),
        }
        return render(request, "create_final_challan.html", context)
    else:
        return redirect("Users:login_user")
#_____________________________________________________________________Extracting DAta FRom the PDF________________________________________________________________________________________________________________
def extract_items_from_pdf(pdf_path):
    """
    Extract items from a transport challan PDF into a list of dictionaries.
    Each item dictionary will contain:
    - sr_no, product, sku, category, subcategory, quantity, price, gst_percentage, line_total
    """
    items = []
    
    print(f"Starting PDF extraction for: {pdf_path}")
    
    # Try pdfplumber first (better for table extraction)
    print("Trying pdfplumber extraction...")
    items = extract_with_pdfplumber(pdf_path)
    print(f"pdfplumber extracted {len(items)} items")
    
    # If pdfplumber fails or returns empty, try PyPDF2
    if not items:
        print("Trying PyPDF2 extraction...")
        items = extract_with_pypdf2(pdf_path)
        print(f"PyPDF2 extracted {len(items)} items")
    
    # If still no items, try text-based extraction
    if not items:
        print("Trying text pattern extraction...")
        items = extract_with_text_patterns(pdf_path)
        print(f"Text patterns extracted {len(items)} items")
    
    # Debug: print first few items
    if items:
        print(f"Successfully extracted {len(items)} items")
        for i, item in enumerate(items[:3]):  # Show first 3 items
            print(f"Item {i+1}: {item}")
    else:
        print("No items extracted - debugging...")
        debug_pdf_content(pdf_path)
    
    return items

def debug_pdf_content(pdf_path):
    """Debug function to show PDF content structure"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n--- Page {page_num + 1} ---")
                
                # Show tables
                tables = page.extract_tables()
                if tables:
                    print(f"Found {len(tables)} tables")
                    for i, table in enumerate(tables[:1]):  # Show first table only
                        print(f"Table {i+1} has {len(table)} rows")
                        if table:
                            print("First few rows:")
                            for row_idx, row in enumerate(table[:5]):
                                print(f"Row {row_idx}: {row}")
                
                # Show text content (first 1000 chars)
                text = page.extract_text()
                if text:
                    print(f"Text content (first 1000 chars):")
                    print(text[:1000])
                    print("...")
                    
    except Exception as e:
        print(f"Debug error: {e}")
        
        # Fallback to PyPDF2 debug
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                print(f"PyPDF2: PDF has {len(reader.pages)} pages")
                
                if reader.pages:
                    text = reader.pages[0].extract_text()
                    print(f"PyPDF2 first page text (first 1000 chars):")
                    print(text[:1000] if text else "No text extracted")
                    
        except Exception as e2:
            print(f"PyPDF2 debug error: {e2}")

def extract_with_pdfplumber(pdf_path):
    """Extract items using pdfplumber - better for structured tables"""
    items = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Try to extract tables first
                tables = page.extract_tables()
                
                if tables:
                    for table in tables:
                        items.extend(parse_table_data(table))
                
                # If no tables found, extract text and parse
                if not items:
                    text = page.extract_text()
                    if text:
                        items.extend(parse_text_content(text))
                        
    except Exception as e:
        print(f"Error with pdfplumber: {e}")
    
    return items

def extract_with_pypdf2(pdf_path):
    """Extract items using PyPDF2 - fallback method"""
    items = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            items = parse_text_content(text)
                        
    except Exception as e:
        print(f"Error with PyPDF2: {e}")
    
    return items

def parse_table_data(table):
    """Parse structured table data"""
    items = []
    
    if not table or len(table) < 2:
        return items
    
    # Find header row
    header_row = None
    for i, row in enumerate(table):
        if row and any(cell and ('product' in str(cell).lower() or 'item' in str(cell).lower()) for cell in row):
            header_row = i
            break
    
    if header_row is None:
        return items
    
    # Get column indices
    headers = [str(cell).lower().strip() if cell else '' for cell in table[header_row]]
    col_mapping = get_column_mapping(headers)
    
    # Process data rows
    for row_idx in range(header_row + 1, len(table)):
        row = table[row_idx]
        if not row or not any(row):
            continue
            
        item_data = extract_item_from_row(row, col_mapping)
        if item_data:
            items.append(item_data)
    
    return items

def parse_text_content(text):
    """Parse text content for items"""
    items = []
    
    if not text:
        return items
    
    lines = text.split('\n')
    
    # Find items section
    start_idx = find_items_start(lines)
    if start_idx == -1:
        return items
    
    # Extract items
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        
        if not line:
            continue
            
        # Stop at summary sections
        if is_summary_line(line):
            break
            
        item_data = extract_item_from_line(line)
        if item_data:
            items.append(item_data)
    
    return items

def extract_with_text_patterns(pdf_path):
    """Advanced text pattern extraction"""
    items = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Try multiple extraction patterns
                    items.extend(extract_items_pattern_1(text))
                    if not items:
                        items.extend(extract_items_pattern_2(text))
                    if not items:
                        items.extend(extract_items_pattern_3(text))
                        
    except Exception as e:
        print(f"Error in pattern extraction: {e}")
    
    return items

def get_column_mapping(headers):
    """Map column names to indices"""
    mapping = {}
    
    for i, header in enumerate(headers):
        header_lower = header.lower()
        
        if any(keyword in header_lower for keyword in ['sr', 'serial', 'no', '#']):
            mapping['sr_no'] = i
        elif any(keyword in header_lower for keyword in ['product', 'item', 'description']):
            mapping['product'] = i
        elif 'sku' in header_lower:
            mapping['sku'] = i
        elif 'category' in header_lower and 'sub' not in header_lower:
            mapping['category'] = i
        elif 'subcategory' in header_lower or 'sub-category' in header_lower:
            mapping['subcategory'] = i
        elif any(keyword in header_lower for keyword in ['qty', 'quantity', 'quan']):
            mapping['quantity'] = i
        elif any(keyword in header_lower for keyword in ['price', 'rate', 'amount']) and 'total' not in header_lower:
            mapping['price'] = i
        elif any(keyword in header_lower for keyword in ['gst', 'tax', '%']):
            mapping['gst'] = i
        elif any(keyword in header_lower for keyword in ['total', 'line total', 'amount']):
            mapping['total'] = i
    
    return mapping

def extract_item_from_row(row, col_mapping):
    """Extract item data from table row"""
    try:
        item = {}
        
        # Get values based on column mapping
        item['sr_no'] = safe_int(get_cell_value(row, col_mapping.get('sr_no')))
        item['product'] = clean_text(get_cell_value(row, col_mapping.get('product')))
        item['sku'] = clean_text(get_cell_value(row, col_mapping.get('sku')))
        item['category'] = clean_text(get_cell_value(row, col_mapping.get('category')))
        item['subcategory'] = clean_text(get_cell_value(row, col_mapping.get('subcategory')))
        item['quantity'] = safe_int(get_cell_value(row, col_mapping.get('quantity')))
        item['price'] = safe_float(get_cell_value(row, col_mapping.get('price')))
        item['gst_percentage'] = safe_float(get_cell_value(row, col_mapping.get('gst')))
        item['line_total'] = safe_float(get_cell_value(row, col_mapping.get('total')))
        
        # Validate required fields
        if item['product'] and item['quantity'] is not None and item['price'] is not None:
            # Calculate missing values
            if item['line_total'] is None and item['quantity'] and item['price']:
                gst_multiplier = 1 + (item['gst_percentage'] or 0) / 100
                item['line_total'] = item['quantity'] * item['price'] * gst_multiplier
            
            return item
            
    except Exception as e:
        print(f"Error extracting item from row: {e}")
    
    return None

def find_items_start(lines):
    """Find the start of items section in text"""
    keywords = [
        ['product', 'sku', 'category'],
        ['item', 'description', 'qty'],
        ['sr', 'product', 'quantity'],
        ['#', 'description', 'amount']
    ]
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for keyword_set in keywords:
            if all(keyword in line_lower for keyword in keyword_set):
                return i + 1
    
    return -1

def is_summary_line(line):
    """Check if line is part of summary section"""
    summary_keywords = [
        'subtotal', 'total', 'grand total', 'transportation',
        'gst', 'tax', 'discount', 'final amount', 'net amount',
        'balance', 'due', 'paid', 'signature'
    ]
    
    line_lower = line.lower()
    return any(keyword in line_lower for keyword in summary_keywords)

def extract_item_from_line(line):
    """Extract item data from a single line"""
    try:
        # Multiple regex patterns for different formats
        patterns = [
            # Pattern 1: Sr Product SKU Category Subcategory Qty ₹Price GST% ₹Total
            r'^(\d+)\s+(.+?)\s+([A-Z0-9]+)\s+([A-Za-z\s]+?)\s+([A-Za-z\s]+?)\s+(\d+)\s+₹?([\d,]+\.?\d*)\s+([\d.]+)%?\s+₹?([\d,]+\.?\d*)$',
            
            # Pattern 2: More flexible spacing
            r'^(\d+)\s+(.+?)\s+([A-Z0-9]+)\s+(.+?)\s+(.+?)\s+(\d+)\s+₹?([\d,]+\.?\d*)\s+([\d.]+)%?\s+₹?([\d,]+\.?\d*)$',
            
            # Pattern 3: Tab separated
            r'^(\d+)\t+(.+?)\t+([A-Z0-9]+)\t+(.+?)\t+(.+?)\t+(\d+)\t+₹?([\d,]+\.?\d*)\t+([\d.]+)%?\t+₹?([\d,]+\.?\d*)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match and len(match.groups()) >= 9:
                return {
                    'sr_no': safe_int(match.group(1)),
                    'product': clean_text(match.group(2)),
                    'sku': clean_text(match.group(3)),
                    'category': clean_text(match.group(4)),
                    'subcategory': clean_text(match.group(5)),
                    'quantity': safe_int(match.group(6)),
                    'price': safe_float(match.group(7)),
                    'gst_percentage': safe_float(match.group(8)),
                    'line_total': safe_float(match.group(9))
                }
        
        # Fallback: split by whitespace
        parts = line.split()
        if len(parts) >= 8:
            try:
                # Find numeric parts
                numeric_parts = []
                text_parts = []
                
                for part in parts:
                    if re.match(r'^\d+$', part) or re.match(r'^[\d,]+\.?\d*$', part.replace('₹', '')):
                        numeric_parts.append(part)
                    else:
                        text_parts.append(part)
                
                if len(numeric_parts) >= 4 and len(text_parts) >= 3:
                    return {
                        'sr_no': safe_int(numeric_parts[0]),
                        'product': ' '.join(text_parts[:-2]) if len(text_parts) > 2 else text_parts[0],
                        'sku': text_parts[-2] if len(text_parts) >= 2 else '',
                        'category': text_parts[-1] if len(text_parts) >= 1 else '',
                        'subcategory': '',
                        'quantity': safe_int(numeric_parts[1]),
                        'price': safe_float(numeric_parts[2]),
                        'gst_percentage': safe_float(numeric_parts[3]) if len(numeric_parts) > 3 else 0,
                        'line_total': safe_float(numeric_parts[4]) if len(numeric_parts) > 4 else None
                    }
            except:
                pass
                
    except Exception as e:
        print(f"Error parsing line '{line}': {e}")
    
    return None

def extract_items_pattern_1(text):
    """Pattern 1: Standard table format"""
    items = []
    lines = text.split('\n')
    
    in_items_section = False
    for line in lines:
        line = line.strip()
        
        if 'product' in line.lower() and any(keyword in line.lower() for keyword in ['sku', 'quantity', 'price']):
            in_items_section = True
            continue
            
        if in_items_section:
            if is_summary_line(line):
                break
                
            item = extract_item_from_line(line)
            if item:
                items.append(item)
    
    return items

def extract_items_pattern_2(text):
    """Pattern 2: Multi-line items"""
    # Implementation for multi-line item descriptions
    return []

def extract_items_pattern_3(text):
    """Pattern 3: Custom format detection"""
    # Implementation for custom formats
    return []

# Helper functions
def get_cell_value(row, index):
    """Safely get cell value from row"""
    if index is not None and 0 <= index < len(row):
        return row[index]
    return None

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return str(text).strip().replace('\n', ' ').replace('\t', ' ')

def safe_int(value):
    """Safely convert to integer"""
    if value is None:
        return None
    try:
        # Remove non-numeric characters except digits
        cleaned = re.sub(r'[^\d]', '', str(value))
        return int(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None

def safe_float(value):
    """Safely convert to float"""
    if value is None:
        return None
    try:
        # Clean the value
        cleaned = str(value).replace('₹', '').replace(',', '').replace('%', '').strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None
        
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

#_______________________________________________________GENRATING INVOICES___________________________________________________________________________________________________________

def generate_invoice_pdf(request, order_id):
    if request.session.get("user_email") and request.session.get("user_role") == "Sales_Manager" or 'Admin':
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
    return redirect("Users:login_user")
