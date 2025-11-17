from django.shortcuts import render
from uuid import uuid4
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Category, Subcategory
from datetime import datetime
from UOM.models import UOM,UOMConversionMatrix
from Location.models import Warehouse
from mysite.models import Supplier,Farmer
from Purchase.models import ProductItem,RFQProduct,RFQResponse,PurchaseOrder, GRN, ProductItem
from product_Items.models import Product, ProductItems,main_product
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from bson import ObjectId
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, get_object_or_404,HttpResponse
from Purchase.models import PurchaseOrder,GRN,ProductItem
import logging
import os
import re
import imaplib
import email
import imaplib, email, re


logger = logging.getLogger(__name__)
from django.shortcuts import render, redirect
from mongoengine.errors import DoesNotExist

from django.shortcuts import render, redirect
from mongoengine.errors import DoesNotExist, ValidationError
from .models import RFQProduct, RFQResponse, PurchaseOrder, Farmer, Supplier

def rfq_dashboard(request):
    # --- Check Login Session ---
    if not request.session.get("user_email"):
        return redirect("Users:login_user")

    user_email = request.session.get("user_email")
    user_role = request.session.get("user_role")
    print(user_email, user_role)

    # --- Role-Based Access Control ---
    if user_role not in ["Purchase_Manager", "Admin"]:
        return redirect("Users:login_user")

    # --- Fetch RFQs Based on Role ---
    if user_role == "Admin":
        rfqs = RFQProduct.objects.all()
    else:
        user_email = request.session.get("user_email").strip().lower()
        rfqs = RFQProduct.objects(created_by__iexact=user_email)

    # --- Clean Up Broken References Gracefully ---
    safe_rfqs = []
    for rfq in rfqs:
        try:
            # Attempt to access referenced fields safely
            _ = rfq.farmer.id if hasattr(rfq, "farmer") and rfq.farmer else None
            _ = rfq.supplier.id if hasattr(rfq, "supplier") and rfq.supplier else None
            safe_rfqs.append(rfq)
        except (DoesNotExist, ValidationError):
            # Skip broken or invalid references
            continue

    # --- Farmers (Safe Fetch) ---
    farmers = []
    for farmer in Farmer.objects.all():
        try:
            farmers.append(farmer)
        except (DoesNotExist, ValidationError):
            continue

    # --- Suppliers (Safe Fetch) ---
    suppliers = []
    for supplier in Supplier.objects.all():
        try:
            suppliers.append(supplier)
        except (DoesNotExist, ValidationError):
            continue

    # --- RFQ Responses ---
    if user_role == "Admin":
        rfq_replies = RFQResponse.objects.all()
    else:
        rfq_replies = RFQResponse.objects.filter(created_by=user_email)

    # --- Purchase Orders ---
    if user_role == "Admin":
        purchase_orders = PurchaseOrder.objects.all()
    else:
        purchase_orders = PurchaseOrder.objects(created_by=user_email)

    # --- Prepare Context with proper variable names ---
    context = {
        "rfqs": safe_rfqs,  # Keep for backward compatibility
        "admin_rfqs": safe_rfqs if user_role == "Admin" else [],  # NEW: For admin view
        "user_rfqs": safe_rfqs if user_role == "Purchase_Manager" else [],  # NEW: For user view
        "farmers": farmers,
        "suppliers": suppliers,
        "new_responses": rfq_replies,
        "new_purchase_orders": purchase_orders,
        "user_role": user_role,
    }

    return render(request, "rfq_dashboard.html", context)


def RFQGenerations(request):
    if request.session.get("user_email") and request.session.get("user_role") in ["Purchase_Manager", "Admin"]:
        user = request.session.get("user_email")
        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()
        warehouses = Warehouse.objects.all()
        suppliers = Supplier.objects.all()
        farmers = Farmer.objects.all()
        products = main_product.objects.all()
        
        if request.method == "POST":
            try:
                warehouse = Warehouse.objects.get(id=request.POST.get("warehouse"))
                supplier_id = request.POST.get("supplier_id")
                farmer_id = request.POST.get("farmer_id")

                # Get all the form data
                product_names = request.POST.getlist("product_name[]")
                product_ids = request.POST.getlist("product_id[]")
                skus = request.POST.getlist("sku[]")
                category_ids = request.POST.getlist("category_id[]")
                category_names = request.POST.getlist("category_name[]")
                subcategory_ids = request.POST.getlist("subcategory_id[]")
                quantities = request.POST.getlist("quantity[]")
                prices = request.POST.getlist("price[]")
                uoms = request.POST.getlist("uom[]")

                print("Received data:")
                print("Product Names:", product_names)
                print("Product IDs:", product_ids)
                print("SKUs:", skus)
                print("Category IDs:", category_ids)
                print("Subcategory IDs:", subcategory_ids)
                print("Quantities:", quantities)
                print("Prices:", prices)
                print("UOMs:", uoms)

                items = []
                total_amount = 0

                for i in range(len(product_ids)):
                    if product_ids[i]:  # Only process if product is selected
                        # Get or generate SKU
                        sku_value = skus[i].strip()
                        if not sku_value:
                            sku_value = f"GEN{str(i+1).zfill(3)}"
                        
                        # Get category and subcategory objects
                        category = Category.objects.get(id=category_ids[i])
                        subcategory = Subcategory.objects.get(id=subcategory_ids[i])
                        
                        # Calculate line total
                        quantity = int(quantities[i])
                        price = float(prices[i])
                        line_total = quantity * price
                        total_amount += line_total
                        
                        # Create product item
                        item = ProductItem(
                            product_name=product_names[i],
                            sku=sku_value,
                            category=category,
                            subcategory=subcategory,
                            quantity=quantity,
                            price=price,
                            uom=uoms[i],
                        )
                        items.append(item)

                print(f"Created {len(items)} items")
                print(f"Total amount: {total_amount}")

                # Create RFQ
                rfq_data = {
                    'warehouse': warehouse,
                    'items': items,
                    'total_amount': total_amount,
                    'created_by': user
                }
                
                # Add supplier or farmer based on selection
                if supplier_id:
                    rfq_data['supplier'] = Supplier.objects.get(id=supplier_id)
                if farmer_id:
                    rfq_data['farmer'] = Farmer.objects.get(id=farmer_id)

                rfq = RFQProduct(**rfq_data)
                rfq.save()
                
                messages.success(request, 'RFQ created successfully!')
                return redirect("Purchase:purchase_dash")

            except Exception as e:
                print(f"Error creating RFQ: {str(e)}")
                messages.error(request, f'Error creating RFQ: {str(e)}')

        return render(request, "RFQGenerations.html", {
            "categories": categories,
            "subcategories": subcategories,
            "warehouses": warehouses,
            "suppliers": suppliers,
            "farmers": farmers,
            "uoms": ["kg", "g", "lb", "pcs"],
            "products": products
        })
    else:
        return redirect('Users:login_user')

 #------------------------------------------------------------------------------------RFQ Options Edit sent mail & Delete--------------------------------------------------------------


def RFQEdit(request):
    if request.session.get('user_email') and request.session.get('user_role') == 'Purchase_Manager' or 'Admin':
        rfq_id = request.GET.get("id") or request.POST.get("id")

        try:
            rfq = RFQProduct.objects.get(id=ObjectId(rfq_id))
        except RFQProduct.DoesNotExist:
            return HttpResponse("RFQ not found", status=404)

        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()
        warehouses = Warehouse.objects.all()
        suppliers = Supplier.objects.all()
        farmers = Farmer.objects.all()
        uoms = ["Kg", "Gram", "Piece", "Box"]

        if request.method == "POST":
            warehouse = Warehouse.objects.get(id=ObjectId(request.POST.get("warehouse"))) \
                if request.POST.get("warehouse") else None

            supplier = farmer = None
            if request.POST.get("source_type") == "supplier":
                supplier = Supplier.objects.get(id=ObjectId(request.POST.get("supplier_id")))
            elif request.POST.get("source_type") == "farmer":
                farmer = Farmer.objects.get(id=ObjectId(request.POST.get("farmer_id")))

            items = []
            total_amount = 0
            for i, name in enumerate(request.POST.getlist("product_name[]")):
                qty = int(request.POST.getlist("quantity[]")[i] or 0)
                price = float(request.POST.getlist("price[]")[i] or 0)
                total_amount += qty * price

                items.append(ProductItem(
                    product_name=name,
                    sku=request.POST.getlist("sku[]")[i],
                    category=Category.objects.get(id=ObjectId(request.POST.getlist("category[]")[i])),
                    subcategory=Subcategory.objects.get(id=ObjectId(request.POST.getlist("subcategory[]")[i])),
                    quantity=qty,
                    price=price,
                    uom=request.POST.getlist("uom[]")[i],
                    warehouse=warehouse
                ))

            RFQProduct.objects(id=ObjectId(rfq_id)).update(
                set__warehouse=warehouse,
                set__supplier=supplier,
                set__farmer=farmer,
                set__items=items,
                set__total_amount=total_amount,
            )

            return redirect("Purchase:purchase_dash")  # adjust to your URL name

        return render(request, "RFQEdit.html", {
            "rfq": rfq,
            "categories": categories,
            "subcategories": subcategories,
            "warehouses": warehouses,
            "suppliers": suppliers,
            "farmers": farmers,
            "uoms": uoms,
        })
    else:
        return redirect('Users:login_user')

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from bson import ObjectId
from io import BytesIO
from datetime import datetime
import logging
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger(__name__)

def rfq_sent_email(request):
    if request.session.get('user_email') and (request.session.get('user_role') == 'Purchase_Manager' or request.session.get('user_role') == 'Admin'):
        rfq_id = request.GET.get('id')
        if not rfq_id:
            messages.error(request, "RFQ ID is required")
            return redirect('Purchase:purchase_dash')

        # Fetch RFQ from MongoDB with related fields
        try:
            # Get RFQ with all related data
            rfq = RFQProduct.objects.get(id=ObjectId(rfq_id))
            
            # Prefetch related objects to avoid multiple database queries
            if hasattr(rfq, 'supplier') and rfq.supplier:
                rfq.supplier = Supplier.objects.get(id=rfq.supplier.id)
            
            if hasattr(rfq, 'farmer') and rfq.farmer:
                rfq.farmer = Farmer.objects.get(id=rfq.farmer.id)
            
            if hasattr(rfq, 'warehouse') and rfq.warehouse:
                rfq.warehouse = Warehouse.objects.get(id=rfq.warehouse.id)
            
            # Process items with category and subcategory details
            processed_items = []
            if hasattr(rfq, 'items') and rfq.items:
                for item in rfq.items:
                    # Create a copy of the item with resolved relationships
                    item_data = {
                        'product_name': item.product_name,
                        'sku': item.sku,
                        'quantity': item.quantity,
                        'price': item.price,
                        'uom': item.uom,
                        'gst_amount': getattr(item, 'gst_amount', 18.0),
                        'gst_value': getattr(item, 'gst_value', 0.0),
                        'subtotal': getattr(item, 'subtotal', 0.0),
                        'line_total': getattr(item, 'line_total', 0.0),
                        'description': getattr(item, 'description', ''),
                        'category': {'name': 'Unknown'},
                        'subcategory': {'name': 'Unknown'},
                        'warehouse': None
                    }
                    
                    # Fetch category details
                    if hasattr(item, 'category') and item.category:
                        try:
                            category = Category.objects.get(id=item.category.id)
                            item_data['category']['name'] = category.name
                        except Category.DoesNotExist:
                            item_data['category']['name'] = 'Unknown'
                    
                    # Fetch subcategory details
                    if hasattr(item, 'subcategory') and item.subcategory:
                        try:
                            subcategory = Subcategory.objects.get(id=item.subcategory.id)
                            item_data['subcategory']['name'] = subcategory.name
                        except Subcategory.DoesNotExist:
                            item_data['subcategory']['name'] = 'Unknown'
                    
                    # Fetch item warehouse if exists
                    if hasattr(item, 'warehouse') and item.warehouse:
                        try:
                            item_warehouse = Warehouse.objects.get(id=item.warehouse.id)
                            item_data['warehouse'] = {
                                'warehouse_name': item_warehouse.warehouse_name,
                                'location': getattr(item_warehouse, 'location', '')
                            }
                        except Warehouse.DoesNotExist:
                            pass
                    
                    # Calculate missing financial fields
                    if item_data['subtotal'] == 0:
                        item_data['subtotal'] = item.quantity * item.price
                    
                    if item_data['gst_value'] == 0 and item_data['gst_amount'] > 0:
                        item_data['gst_value'] = (item_data['subtotal'] * item_data['gst_amount']) / 100
                    
                    if item_data['line_total'] == 0:
                        item_data['line_total'] = item_data['subtotal'] + item_data['gst_value']
                    
                    processed_items.append(item_data)
            
            # Replace original items with processed items
            rfq.processed_items = processed_items
            
            # Calculate overall totals if not present
            if not hasattr(rfq, 'subtotal') or rfq.subtotal == 0:
                rfq.subtotal = sum(item['subtotal'] for item in processed_items)
            
            if not hasattr(rfq, 'gst_amount') or rfq.gst_amount == 0:
                rfq.gst_amount = sum(item['gst_value'] for item in processed_items)
            
            if not hasattr(rfq, 'total_amount') or rfq.total_amount == 0:
                rfq.total_amount = sum(item['line_total'] for item in processed_items)
                
        except (RFQProduct.DoesNotExist, ValueError) as e:
            logger.error(f"RFQ not found: {e}")
            messages.error(request, "RFQ not found")
            return redirect('Purchase:purchase_dash')
        except Exception as e:
            logger.error(f"Error fetching RFQ data: {e}")
            messages.error(request, f"Error fetching RFQ data: {str(e)}")
            return redirect('Purchase:purchase_dash')

        # Determine recipient details
        recipient_email = None
        recipient_name = None
        recipient_type = None

        if hasattr(rfq, 'supplier') and rfq.supplier:
            recipient_email = getattr(rfq.supplier, 'email', None)
            recipient_name = getattr(rfq.supplier, 'supplier_name', None)
            recipient_type = "Supplier"
        elif hasattr(rfq, 'farmer') and rfq.farmer:
            recipient_email = getattr(rfq.farmer, 'email', None)
            recipient_name = getattr(rfq.farmer, 'full_name', None)
            recipient_type = "Farmer"

        if not recipient_email:
            messages.error(request, "No email found for this RFQ recipient")
            return redirect('Purchase:RFQDashboard')

        try:
            # Prepare PDF context with all required data
            context = {
                'rfq': rfq,
                'company_name': getattr(settings, 'COMPANY_NAME', 'VBT-Tech'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'vishaltarale055@gmail.com'),
                'current_date': datetime.now().strftime('%d %b %Y'),
            }

            # Render PDF HTML using the corrected template
            html_string = render_to_string('rfq_pdf_template.html', context)

            # Generate PDF with better styling
            font_config = FontConfiguration()
            css = CSS(string="""
                @page {
                    size: A4;
                    margin: 0.5in;
                }
                body {
                    font-family: Arial, sans-serif;
                    font-size: 11px;
                    line-height: 1.3;
                    margin: 0;
                    padding: 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 10px;
                }
                th, td {
                    border: 1px solid #000;
                    padding: 4px;
                    text-align: left;
                }
                th {
                    background: #f0f0f0;
                    font-weight: bold;
                }
                .header {
                    text-align: center;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 10px;
                }
                .section-title {
                    font-size: 14px;
                    font-weight: bold;
                    margin: 12px 0 8px 0;
                    border-bottom: 1px solid #000;
                    padding-bottom: 3px;
                    background-color: #f8f9fa;
                    padding: 6px;
                }
            """)
            
            pdf_file = BytesIO()
            html = HTML(string=html_string)
            html.write_pdf(pdf_file, stylesheets=[css], font_config=font_config)
            pdf_file.seek(0)

            # Prepare email content
            subject = f"Request for Quotation - {rfq_id}"
            
            email_context = {
                'rfq': rfq,
                'recipient_name': recipient_name,
                'recipient_type': recipient_type,
                'company_name': getattr(settings, 'COMPANY_NAME', 'VBT-Tech'),
            }
            
            html_body = render_to_string('rfq_email_template.html', email_context)
            text_body = render_to_string('rfq_email_template.txt', email_context)

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
                reply_to=[getattr(settings, 'COMPANY_EMAIL', 'vishaltarale055@gmail.com')]
            )
            email.attach_alternative(html_body, "text/html")

            # Attach PDF with proper filename
            if hasattr(rfq, 'processed_items') and rfq.processed_items:
                sku_part = rfq.processed_items[0]['sku'] if rfq.processed_items[0].get('sku') else "RFQ"
            else:
                sku_part = "RFQ"
                
            pdf_filename = f"RFQ_{sku_part}_{datetime.now().strftime('%Y%m%d')}.pdf"
            email.attach(pdf_filename, pdf_file.read(), 'application/pdf')

            # Send email
            email.send()

            # Update RFQ status if needed
            try:
                rfq.status = "Sent"
                rfq.save()
            except Exception as e:
                logger.warning(f"Could not update RFQ status: {e}")

            messages.success(request, f"RFQ sent successfully to {recipient_name} ({recipient_email})")
            logger.info(f"RFQ {rfq_id} sent to {recipient_email}")

        except Exception as e:
            logger.error(f"Error sending RFQ email: {e}")
            messages.error(request, f"Error sending RFQ: {str(e)}")

        return redirect('Purchase:purchase_dash')
    else:
        messages.error(request, "Unauthorized access")
        return redirect('Users:login_user')

def RFQDelete(request):
    if request.session.get('user_email') and request.session.get('user_role') == 'Purchase_Manager' or 'Admin':
        id = request.GET['id']
        RFQProduct.objects.get(id=ObjectId(id)).delete()
        messages.success(request, f"suuccesfully deleted {{id}}")
        return redirect('Purchase:purchase_dash')
    else:
        return redirect('User:login_user')

#-----------------------------------------------------------------------------------------Extracting mail Reply-------------------------------------------------------------  
import os
import re
import imaplib
import email
from email.header import decode_header
from bson import ObjectId
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import RFQProduct, RFQResponse


# Directory setup
ATTACHMENTS_DIR = os.path.join(settings.MEDIA_ROOT, "rfq_attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


def extract_rfq_id(text):
    """Extract 24-char hex RFQ ID from text"""
    patterns = [
        r"RFQ\s*[:\-]?\s*ID\s*[:\-]?\s*([a-fA-F0-9]{24})",
        r"RFQ\s*[:\-#]?\s*([a-fA-F0-9]{24})",
        r"\b([a-fA-F0-9]{24})\b"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rfq_id = match.group(1)
            try:
                ObjectId(rfq_id)
                return rfq_id
            except:
                continue
    return None


def decode_header_value(header):
    """Decode email header"""
    if not header:
        return ""
    decoded_parts = decode_header(header)
    result = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            result += str(part)
    return result.strip()


def extract_email_address(from_header):
    """Extract email address from From header"""
    match = re.search(r'<([^>]+)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', from_header)
    if match:
        return (match.group(1) or match.group(2)).lower().strip()
    return from_header.strip()


def get_email_body(msg):
    """Extract plain text body from email"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                if "attachment" not in str(part.get("Content-Disposition")):
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            body = str(msg.get_payload())
    
    return body.strip()


def save_attachments(msg, rfq_id):
    """Save email attachments and return list of filenames"""
    saved_files = []
    
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        
        filename = part.get_filename()
        if filename:
            filename = decode_header_value(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{filename}"
            safe_filename = re.sub(r'[^\w\-_\.]', '_', safe_filename)
            
            file_path = os.path.join(ATTACHMENTS_DIR, safe_filename)
            
            try:
                data = part.get_payload(decode=True)
                if data:
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    saved_files.append(safe_filename)
            except Exception as e:
                print(f"Error saving attachment: {e}")
                continue
    
    return saved_files


def process_email_message(msg):
    """Process single email and create/update RFQ response"""
    try:
        # Decode email headers
        subject = decode_header_value(msg.get("Subject", ""))
        from_header = decode_header_value(msg.get("From", ""))
        sender_email = extract_email_address(from_header)
        
        # Get email body
        body = get_email_body(msg)
        
        # Extract RFQ ID
        full_text = f"{subject} {body}"
        rfq_id = extract_rfq_id(full_text)
        
        if not rfq_id:
            return None
        
        # Check if RFQ exists
        try:
            rfq = RFQProduct.objects.get(id=ObjectId(rfq_id))
        except RFQProduct.DoesNotExist:
            print(f"RFQ {rfq_id} not found in database")
            return None
        
        # Check if response already exists
        existing = RFQResponse.objects(
            rfq=rfq,
            sender_email=sender_email
        ).first()
        
        # Save attachments
        attachments = save_attachments(msg, rfq_id)
        
        if existing:
            # Update existing response
            existing.message = body
            existing.attachments = attachments
            existing.received_at = datetime.utcnow()
            existing.save()
            print(f"Updated response for RFQ {rfq_id} from {sender_email}")
            return existing
        else:
            # Create new response
            response = RFQResponse(
                rfq=rfq,
                sender_email=sender_email,
                message=body,
                attachments=attachments,
                received_at=datetime.utcnow(),
                created_by="system"
            )
            response.save()
            print(f"Created new response for RFQ {rfq_id} from {sender_email}")
            return response
            
    except Exception as e:
        print(f"Error processing email: {e}")
        return None


def fetch_rfq_emails():
    """Connect to inbox and process RFQ response emails"""
    mail = None
    processed = 0
    
    try:
        # Connect to email server
        mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        mail.select("inbox")
        
        # Search for emails containing RFQ
        status, messages = mail.search(None, 'OR SUBJECT "RFQ" BODY "RFQ"')
        
        if status != "OK":
            print("No emails found")
            return 0
        
        email_ids = messages[0].split()
        
        # Process latest 30 emails
        latest_emails = email_ids[-30:] if len(email_ids) > 30 else email_ids
        
        for email_id in reversed(latest_emails):
            try:
                status, data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                msg = email.message_from_bytes(data[0][1])
                result = process_email_message(msg)
                
                if result:
                    processed += 1
                    
            except Exception as e:
                print(f"Error fetching email: {e}")
                continue
        
        print(f"Processed {processed} RFQ responses")
        return processed
        
    except Exception as e:
        print(f"Email fetch error: {e}")
        return 0
    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass


def rfq_responses_list(request):
    """Display RFQ responses with auto-fetch on page load"""
    try:
        # Auto-fetch emails
        fetch_rfq_emails()
        
        # Manual fetch button
        if request.method == 'POST' and 'fetch_emails' in request.POST:
            count = fetch_rfq_emails()
            messages.success(request, f"Processed {count} email(s)")
        
        # Get all responses
        responses = RFQResponse.objects.order_by("-received_at")
        
        return render(request, "rfq_responses_list.html", {
            "responses": responses,
            "MEDIA_URL": settings.MEDIA_URL,
        })
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return render(request, "rfq_responses_list.html", {
            "responses": [],
            "MEDIA_URL": settings.MEDIA_URL,
        })


def manual_process_emails(request):
    """Manual email processing endpoint"""
    try:
        count = fetch_rfq_emails()
        messages.success(request, f"Processed {count} email(s)")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('Purchase:rfq_responses_list')
#-----------------------------------------------------------------------------------------Generating Automatic SKU for every product--------------------------------------------------------------

import random, string
def generate_sku(product_name):
    """Generate a unique SKU like APP-XYZ123"""
    prefix = "".join([ch for ch in product_name.upper() if ch.isalpha()][:3])  # APP
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    sku = f"{prefix}-{suffix}"
    # Ensure uniqueness in DB
    while Product.objects(items__sku=sku).first():
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        sku = f"{prefix}-{suffix}"
    return sku

from Purchase.models import PurchaseOrder
def create_purchase_order_from_rfq(rfq: RFQProduct, warehouse=None, supplier=None, farmer=None, notes=None):
    po_items = []
    if getattr(rfq, "items", None):
        for item in rfq.items:
            # We copy the embedded ProductItem document (if it is an EmbeddedDocument this will be fine)
            po_items.append(item)

    po = PurchaseOrder(
        rfq=rfq,
        warehouse=warehouse or getattr(rfq, 'warehouse', None),
        supplier=supplier or getattr(rfq, 'supplier', None),
        farmer=farmer or getattr(rfq, 'farmer', None),
        items=po_items,
        notes=notes or ''
    )
    po.save()
    return po

#------------------------------------------------------------------------------------------PO Options Edit & Delete--------------------------------------------------------------
import os
import pdfplumber
import re
from django.shortcuts import render, redirect
from django.contrib import messages
from bson import ObjectId
from django.conf import settings
import logging
from Location.models import Warehouse

logger = logging.getLogger(__name__)


def extract_data_from_pdf(pdf_path):
    """
    Extract comprehensive data from PDF including tables using pdfplumber
    """
    extracted_data = {
        'supplier_name': '',
        'farmer_name': '',
        'warehouse_name': '',
        'warehouse_location': '',
        'products': [],
        'subtotal': 0,
        'gst_amount': 0,
        'grand_total': 0,
        'notes': '',
        'source_type': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            all_tables = []
            
            # Extract text and tables from all pages
            for page in pdf.pages:
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
            
            logger.info(f"Extracted PDF text: {full_text[:500]}...")
            logger.info(f"Found {len(all_tables)} tables in PDF")
            
            # Extract supplier information
            supplier_patterns = [
                r'Supplier\s*[:\-]\s*([^\n\r]+)',
                r'Vendor\s*[:\-]\s*([^\n\r]+)',
                r'From\s*[:\-]\s*([^\n\r]+)',
                r'Company\s*[:\-]\s*([^\n\r]+)',
            ]
            
            for pattern in supplier_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    extracted_data['supplier_name'] = match.group(1).strip()
                    extracted_data['source_type'] = 'supplier'
                    break
            
            # Extract farmer information
            if not extracted_data['supplier_name']:
                farmer_patterns = [
                    r'Farmer\s*[:\-]\s*([^\n\r]+)',
                    r'Grower\s*[:\-]\s*([^\n\r]+)',
                ]
                
                for pattern in farmer_patterns:
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        extracted_data['farmer_name'] = match.group(1).strip()
                        extracted_data['source_type'] = 'farmer'
                        break
            
            # Extract warehouse information
            warehouse_patterns = [
                r'Warehouse\s*[:\-]\s*([^\n\r]+?)(?:\s*\(([^)]+)\))?',
                r'Location\s*[:\-]\s*([^\n\r]+)',
                r'Delivery Location\s*[:\-]\s*([^\n\r]+)',
                r'Ship To\s*[:\-]\s*([^\n\r]+?)(?:\s*-\s*([^\n\r]+))?',
            ]
            
            for pattern in warehouse_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    extracted_data['warehouse_name'] = match.group(1).strip()
                    if match.lastindex >= 2 and match.group(2):
                        extracted_data['warehouse_location'] = match.group(2).strip()
                    break
            
            # Extract products from tables
            products = []
            
            # Define category keywords for inference
            category_keywords = {
                'Electronics': ['electronic', 'device', 'mobile', 'laptop', 'computer', 'phone', 'tablet'],
                'Furniture': ['furniture', 'chair', 'table', 'desk', 'sofa', 'cabinet'],
                'Office Supplies': ['pen', 'paper', 'notebook', 'stationery', 'office', 'file'],
                'Raw Materials': ['raw', 'material', 'metal', 'wood', 'plastic', 'steel'],
                'Agricultural': ['agricultural', 'crop', 'grain', 'seed', 'fertilizer', 'pesticide'],
            }
            
            # Process tables
            for table_index, table in enumerate(all_tables):
                logger.info(f"Processing table {table_index + 1}")
                
                if not table or len(table) < 2:  # Need at least header + 1 row
                    continue
                
                # Try to identify header row
                header_row = None
                data_start_index = 0
                
                # Check first few rows for header
                for i in range(min(3, len(table))):
                    row = [str(cell).lower() if cell else '' for cell in table[i]]
                    # Look for common header keywords
                    if any(keyword in ' '.join(row) for keyword in ['product', 'item', 'description', 'name', 'qty', 'quantity', 'price', 'amount']):
                        header_row = table[i]
                        data_start_index = i + 1
                        logger.info(f"Found header at row {i}: {header_row}")
                        break
                
                # If no header found, assume first row is header
                if header_row is None:
                    header_row = table[0]
                    data_start_index = 1
                
                # Identify column indices
                column_mapping = identify_columns(header_row)
                logger.info(f"Column mapping: {column_mapping}")
                
                # Process data rows
                for row_index in range(data_start_index, len(table)):
                    row = table[row_index]
                    if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                        continue  # Skip empty rows
                    
                    product_data = extract_product_from_table_row(
                        row, column_mapping, category_keywords
                    )
                    
                    if product_data:
                        products.append(product_data)
                        logger.info(f"Extracted product: {product_data['product_name']}")
            
            # If no products found in tables, try text extraction
            if not products:
                logger.info("No products found in tables, trying text extraction")
                products = extract_products_from_text(full_text, category_keywords)
            
            extracted_data['products'] = products
            
            # Extract totals
            total_patterns = [
                (r'Sub[-\s]?total\s*[:\-]?\s*[₹$\s]*([\d,]+(?:\.\d{2})?)', 'subtotal'),
                (r'GST\s*[:\-]?\s*[₹$\s]*([\d,]+(?:\.\d{2})?)', 'gst'),
                (r'Total\s*GST\s*[:\-]?\s*[₹$\s]*([\d,]+(?:\.\d{2})?)', 'gst'),
                (r'Grand\s*Total\s*[:\-]?\s*[₹$\s]*([\d,]+(?:\.\d{2})?)', 'grand_total'),
                (r'Total\s*Amount\s*[:\-]?\s*[₹$\s]*([\d,]+(?:\.\d{2})?)', 'grand_total'),
            ]
            
            for pattern, field_type in total_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    try:
                        amount = float(match.replace(',', ''))
                        if field_type == 'subtotal':
                            extracted_data['subtotal'] = amount
                        elif field_type == 'gst':
                            extracted_data['gst_amount'] = amount
                        elif field_type == 'grand_total':
                            extracted_data['grand_total'] = amount
                    except ValueError:
                        continue
            
            # Calculate missing totals if we have products
            if products:
                if extracted_data['subtotal'] == 0 and extracted_data['grand_total'] == 0:
                    total = sum(product['line_total'] for product in products)
                    # Assume total includes GST
                    extracted_data['subtotal'] = round(total / 1.18, 2)
                    extracted_data['gst_amount'] = round(total - extracted_data['subtotal'], 2)
                    extracted_data['grand_total'] = round(total, 2)
                elif extracted_data['grand_total'] > 0 and extracted_data['subtotal'] == 0:
                    extracted_data['subtotal'] = round(extracted_data['grand_total'] / 1.18, 2)
                    extracted_data['gst_amount'] = round(extracted_data['grand_total'] - extracted_data['subtotal'], 2)
            
            # Extract notes
            notes_patterns = [
                r'Notes?\s*[:\-]\s*(.+?)(?=\n\s*(?:Total|Grand|Sub|GST|Thank)|\Z)',
                r'Remarks?\s*[:\-]\s*(.+?)(?=\n\s*(?:Total|Grand|Sub|GST|Thank)|\Z)',
                r'Comments?\s*[:\-]\s*(.+?)(?=\n\s*(?:Total|Grand|Sub|GST|Thank)|\Z)',
            ]
            
            for pattern in notes_patterns:
                notes_match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
                if notes_match:
                    extracted_data['notes'] = notes_match.group(1).strip()
                    break
                    
    except Exception as e:
        logger.error(f"Error extracting PDF data from {pdf_path}: {e}", exc_info=True)
    
    return extracted_data


def identify_columns(header_row):
    """
    Identify column indices from header row
    """
    column_mapping = {
        'product_name': None,
        'sku': None,
        'description': None,
        'quantity': None,
        'uom': None,
        'price': None,
        'unit_price': None,
        'amount': None,
        'total': None,
        'gst': None,
        'category': None,
    }
    
    if not header_row:
        return column_mapping
    
    # Keywords for each column type
    keywords = {
        'product_name': ['product', 'item', 'name', 'description', 'particulars'],
        'sku': ['sku', 'code', 'id', 'item code'],
        'quantity': ['qty', 'quantity', 'quan'],
        'uom': ['uom', 'unit', 'measure'],
        'price': ['price', 'rate', 'unit price', 'cost'],
        'amount': ['amount', 'total', 'line total', 'value'],
        'gst': ['gst', 'tax', 'vat'],
        'category': ['category', 'type', 'class'],
    }
    
    for col_index, cell in enumerate(header_row):
        if cell is None:
            continue
        
        cell_lower = str(cell).lower().strip()
        
        # Check each keyword set
        for field, field_keywords in keywords.items():
            if any(keyword in cell_lower for keyword in field_keywords):
                # Prefer more specific matches
                if column_mapping[field] is None:
                    column_mapping[field] = col_index
                    logger.info(f"Mapped '{cell}' to {field} at index {col_index}")
                    break
    
    return column_mapping


def extract_product_from_table_row(row, column_mapping, category_keywords):
    """
    Extract product information from a table row
    """
    try:
        # Get product name
        product_name_idx = column_mapping.get('product_name')
        if product_name_idx is None or product_name_idx >= len(row):
            return None
        
        product_name = str(row[product_name_idx]).strip() if row[product_name_idx] else ''
        
        # Skip if product name is empty or looks like a header/total
        if not product_name or any(skip in product_name.lower() for skip in ['total', 'subtotal', 'grand', 'gst', 'tax', 'amount', 'none']):
            return None
        
        # Extract SKU
        sku = ''
        sku_idx = column_mapping.get('sku')
        if sku_idx is not None and sku_idx < len(row) and row[sku_idx]:
            sku = str(row[sku_idx]).strip()
        else:
            # Try to extract from product name
            sku = extract_sku_from_text(product_name)
        
        # Extract quantity
        quantity = 1
        qty_idx = column_mapping.get('quantity')
        if qty_idx is not None and qty_idx < len(row) and row[qty_idx]:
            try:
                quantity = int(float(str(row[qty_idx]).replace(',', '')))
            except (ValueError, AttributeError):
                quantity = 1
        
        # Extract UOM
        uom = 'PCS'
        uom_idx = column_mapping.get('uom')
        if uom_idx is not None and uom_idx < len(row) and row[uom_idx]:
            uom = str(row[uom_idx]).strip().upper()
        else:
            uom = infer_uom(product_name)
        
        # Extract price
        price = 0.0
        price_idx = column_mapping.get('price')
        if price_idx is not None and price_idx < len(row) and row[price_idx]:
            try:
                price = float(str(row[price_idx]).replace(',', '').replace('₹', '').replace('$', '').strip())
            except (ValueError, AttributeError):
                price = 0.0
        
        # Extract line total
        line_total = 0.0
        amount_idx = column_mapping.get('amount')
        if amount_idx is not None and amount_idx < len(row) and row[amount_idx]:
            try:
                line_total = float(str(row[amount_idx]).replace(',', '').replace('₹', '').replace('$', '').strip())
            except (ValueError, AttributeError):
                line_total = quantity * price
        else:
            line_total = quantity * price
        
        # Calculate GST (assume 18% if not specified)
        gst_percent = 18.0
        gst_idx = column_mapping.get('gst')
        if gst_idx is not None and gst_idx < len(row) and row[gst_idx]:
            try:
                gst_value = str(row[gst_idx]).replace('%', '').strip()
                gst_percent = float(gst_value)
            except (ValueError, AttributeError):
                pass
        
        # Calculate subtotal and GST value
        # Assuming line_total includes GST
        subtotal = round(line_total / (1 + gst_percent / 100), 2)
        gst_value = round(line_total - subtotal, 2)
        
        # Infer category
        category_name = infer_category(product_name, category_keywords)
        subcategory_name = infer_subcategory(product_name)
        
        return {
            'product_name': product_name,
            'sku': sku,
            'category_name': category_name,
            'subcategory_name': subcategory_name,
            'quantity': quantity,
            'price': price,
            'uom': uom,
            'line_total': line_total,
            'gst_amount': gst_percent,
            'gst_value': gst_value,
            'subtotal': subtotal
        }
        
    except Exception as e:
        logger.error(f"Error extracting product from row: {e}")
        return None


def extract_products_from_text(text, category_keywords):
    """
    Fallback method to extract products from plain text
    """
    products = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip lines that are clearly not products
        if any(skip in line.lower() for skip in ['total', 'subtotal', 'gst', 'tax', 'invoice', 'date', 'thank']):
            continue
        
        # Try to match product pattern: Name/Code Qty Price Amount
        pattern = r'(.+?)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
        match = re.search(pattern, line)
        
        if match:
            try:
                product_name = match.group(1).strip()
                quantity = int(match.group(2))
                price = float(match.group(3).replace(',', ''))
                line_total = float(match.group(4).replace(',', ''))
                
                # Calculate GST
                subtotal = round(line_total / 1.18, 2)
                gst_value = round(line_total - subtotal, 2)
                
                product_data = {
                    'product_name': product_name,
                    'sku': extract_sku_from_text(product_name),
                    'category_name': infer_category(product_name, category_keywords),
                    'subcategory_name': infer_subcategory(product_name),
                    'quantity': quantity,
                    'price': price,
                    'uom': infer_uom(product_name),
                    'line_total': line_total,
                    'gst_amount': 18.0,
                    'gst_value': gst_value,
                    'subtotal': subtotal
                }
                products.append(product_data)
            except (ValueError, IndexError):
                continue
    
    return products


def extract_sku_from_text(product_name):
    """Extract or generate SKU from product name"""
    # Look for SKU-like patterns
    sku_pattern = r'\b[A-Z0-9]{3,}[-_]?[A-Z0-9]{2,}\b'
    match = re.search(sku_pattern, product_name)
    if match:
        return match.group()
    return ""


def infer_category(product_name, category_keywords):
    """Infer category from product name"""
    product_lower = product_name.lower()
    for category, keywords in category_keywords.items():
        if any(keyword in product_lower for keyword in keywords):
            return category
    return "General"


def infer_subcategory(product_name):
    """Infer subcategory from product name"""
    words = product_name.lower().split()
    if any(word in words for word in ['premium', 'deluxe', 'professional', 'pro']):
        return "Premium"
    elif any(word in words for word in ['basic', 'standard', 'regular']):
        return "Standard"
    elif any(word in words for word in ['bulk', 'wholesale', 'commercial']):
        return "Bulk"
    return "General"


def infer_uom(product_name):
    """Infer unit of measure from product name"""
    product_lower = product_name.lower()
    if any(word in product_lower for word in ['kg', 'kilo', 'kilogram']):
        return "KG"
    elif any(word in product_lower for word in ['liter', 'litre', 'ltr', 'l']):
        return "LTR"
    elif any(word in product_lower for word in ['meter', 'metre', 'mtr', 'm']):
        return "MTR"
    elif any(word in product_lower for word in ['pack', 'package', 'box', 'carton']):
        return "PACK"
    elif any(word in product_lower for word in ['dozen', 'doz']):
        return "DOZ"
    return "PCS"


def get_pdf_path(attachments):
    """Get the correct PDF path from attachments field"""
    if not attachments:
        logger.warning("No attachments provided")
        return None
    
    logger.info(f"Attachments type: {type(attachments)}, Value: {attachments}")
    
    # Case 1: attachments is a string (single file path)
    if isinstance(attachments, str):
        # Try with MEDIA_ROOT
        pdf_path = os.path.join(settings.MEDIA_ROOT, attachments)
        logger.info(f"Trying path with MEDIA_ROOT: {pdf_path}")
        if os.path.exists(pdf_path):
            logger.info(f"PDF found at: {pdf_path}")
            return pdf_path
        
        # Try direct path
        logger.info(f"Trying direct path: {attachments}")
        if os.path.exists(attachments):
            logger.info(f"PDF found at: {attachments}")
            return attachments
        
        # Try without leading slash
        if attachments.startswith('/'):
            pdf_path = os.path.join(settings.MEDIA_ROOT, attachments[1:])
            logger.info(f"Trying path without leading slash: {pdf_path}")
            if os.path.exists(pdf_path):
                logger.info(f"PDF found at: {pdf_path}")
                return pdf_path
    
    # Case 2: attachments is a list
    elif isinstance(attachments, list) and attachments:
        logger.info(f"Processing list of {len(attachments)} attachments")
        for i, attachment in enumerate(attachments):
            logger.info(f"Processing attachment {i}: {attachment} (type: {type(attachment)})")
            
            if isinstance(attachment, str):
                if attachment.lower().endswith('.pdf'):
                    # Try with MEDIA_ROOT
                    pdf_path = os.path.join(settings.MEDIA_ROOT, attachment)
                    logger.info(f"Trying path: {pdf_path}")
                    if os.path.exists(pdf_path):
                        logger.info(f"PDF found at: {pdf_path}")
                        return pdf_path
                    
                    # Try direct path
                    if os.path.exists(attachment):
                        logger.info(f"PDF found at: {attachment}")
                        return attachment
                    
                    # Try without leading slash
                    if attachment.startswith('/'):
                        pdf_path = os.path.join(settings.MEDIA_ROOT, attachment[1:])
                        if os.path.exists(pdf_path):
                            logger.info(f"PDF found at: {pdf_path}")
                            return pdf_path
            
            elif isinstance(attachment, dict):
                # Handle dict in list (e.g., [{'file': 'path.pdf', 'name': 'document'}])
                for key, value in attachment.items():
                    if isinstance(value, str) and value.lower().endswith('.pdf'):
                        pdf_path = os.path.join(settings.MEDIA_ROOT, value)
                        if os.path.exists(pdf_path):
                            logger.info(f"PDF found at: {pdf_path}")
                            return pdf_path
    
    # Case 3: attachments is a dict
    elif isinstance(attachments, dict):
        logger.info(f"Processing dict with keys: {attachments.keys()}")
        for key, value in attachments.items():
            logger.info(f"Processing key '{key}': {value} (type: {type(value)})")
            
            if isinstance(value, str) and value.lower().endswith('.pdf'):
                # Try with MEDIA_ROOT
                pdf_path = os.path.join(settings.MEDIA_ROOT, value)
                logger.info(f"Trying path: {pdf_path}")
                if os.path.exists(pdf_path):
                    logger.info(f"PDF found at: {pdf_path}")
                    return pdf_path
                
                # Try direct path
                if os.path.exists(value):
                    logger.info(f"PDF found at: {value}")
                    return value
    
    logger.warning(f"No PDF found in attachments. MEDIA_ROOT: {settings.MEDIA_ROOT}")
    return None


def generate_sku(product_name):
    """Generate SKU from product name if not provided"""
    # Take first 3 letters of each word, uppercase, max 10 chars
    words = product_name.strip().split()
    sku_parts = []
    for word in words[:3]:  # Max 3 words
        if len(word) >= 3:
            sku_parts.append(word[:3].upper())
        else:
            sku_parts.append(word.upper())
    
    sku = ''.join(sku_parts)[:10]
    
    # Add random number for uniqueness
    import random
    sku += str(random.randint(100, 999))
    
    return sku


def debug_rfq_attachments(request, rfq_id):
    """
    Debug view to check RFQ attachments
    Usage: Add this to your urls.py and visit the URL to see attachment details
    """
    if request.session.get('user_email') and request.session.get('user_role') in ['Purchase_Manager', 'Admin']:
        try:
            from Purchase.models import RFQResponse
            rfq = RFQResponse.objects.get(rfq=ObjectId(rfq_id))
            
            debug_info = {
                'rfq_id': str(rfq_id),
                'has_attachments': hasattr(rfq, 'attachments'),
                'attachments_type': type(rfq.attachments).__name__ if hasattr(rfq, 'attachments') else 'N/A',
                'attachments_value': str(rfq.attachments) if hasattr(rfq, 'attachments') else 'N/A',
                'media_root': settings.MEDIA_ROOT,
            }
            
            # Try to get PDF path
            if hasattr(rfq, 'attachments'):
                pdf_path = get_pdf_path(rfq.attachments)
                debug_info['pdf_path_found'] = pdf_path
                debug_info['pdf_exists'] = os.path.exists(pdf_path) if pdf_path else False
            
            # List all attributes of RFQ
            debug_info['rfq_attributes'] = [attr for attr in dir(rfq) if not attr.startswith('_')]
            
            from django.http import JsonResponse
            return JsonResponse(debug_info, json_dumps_params={'indent': 2})
            
        except Exception as e:
            from django.http import JsonResponse
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return redirect('Users:login')


def PO(request, rfq_id):
    if request.session.get('user_email') and request.session.get('user_role') in ['Purchase_Manager', 'Admin']:
        user = request.session.get('user_email')
        try:
            from Purchase.models import RFQResponse, PurchaseOrder, ProductItem, Supplier, Farmer, Category, Subcategory
            rfq = RFQResponse.objects.get(rfq=ObjectId(rfq_id))
        except RFQResponse.DoesNotExist:
            messages.error(request, "RFQ not found")
            return redirect("Purchase:purchase_order_detail")

        # Extract data from PDF attachment
        extracted_data = {}
        source_type = None
        
        # Debug: Log RFQ attachments info
        logger.info(f"RFQ ID: {rfq_id}")
        logger.info(f"RFQ has attachments attribute: {hasattr(rfq, 'attachments')}")
        if hasattr(rfq, 'attachments'):
            logger.info(f"RFQ attachments type: {type(rfq.attachments)}")
            logger.info(f"RFQ attachments value: {rfq.attachments}")
        
        pdf_path = get_pdf_path(rfq.attachments) if hasattr(rfq, 'attachments') else None
        
        if pdf_path and os.path.exists(pdf_path):
            logger.info(f"Processing PDF at: {pdf_path}")
            try:
                extracted_data = extract_data_from_pdf(pdf_path)
                
                if extracted_data.get('source_type'):
                    source_type = extracted_data['source_type']
                elif extracted_data.get('supplier_name'):
                    source_type = 'supplier'
                elif extracted_data.get('farmer_name'):
                    source_type = 'farmer'
                    
                messages.success(request, f"Data extracted successfully from PDF! Found {len(extracted_data.get('products', []))} products.")
                logger.info(f"Successfully extracted {len(extracted_data.get('products', []))} products from PDF")
            except Exception as e:
                logger.error(f"Error processing PDF: {e}", exc_info=True)
                messages.error(request, f"Error processing PDF: {str(e)}")
        else:
            logger.warning(f"No PDF found. pdf_path={pdf_path}, RFQ attachments={getattr(rfq, 'attachments', 'NO ATTRIBUTE')}")
            messages.warning(request, "No PDF attachment found, using RFQ data. Please check if the PDF is uploaded correctly.")

        # Prepare RFQ items for template
        rfq_items = []
        if hasattr(rfq, 'items') and rfq.items:
            rfq_items = rfq.items
        else:
            if hasattr(rfq, 'product_name') and rfq.product_name:
                rfq_items = [{
                    'product_name': getattr(rfq, 'product_name', 'Product'),
                    'sku': getattr(rfq, 'sku', ''),
                    'quantity': getattr(rfq, 'quantity', 1),
                    'price': getattr(rfq, 'price', 0),
                    'uom': getattr(rfq, 'uom', 'PCS'),
                }]

        # Match categories and subcategories from extracted data
        if extracted_data.get('products'):
            for product in extracted_data['products']:
                if product.get('category_name'):
                    try:
                        category = Category.objects.filter(name__icontains=product['category_name'][:5]).first()
                        if category:
                            product['category_id'] = str(category.id)
                    except Exception as e:
                        logger.error(f"Error matching category: {e}")
                
                if product.get('subcategory_name'):
                    try:
                        subcategory = Subcategory.objects.filter(name__icontains=product['subcategory_name'][:5]).first()
                        if subcategory:
                            product['subcategory_id'] = str(subcategory.id)
                    except Exception as e:
                        logger.error(f"Error matching subcategory: {e}")

        if request.method == "POST":
            try:
                notes = request.POST.get("notes", "")
                source_type = request.POST.get("source_type")
                supplier_id = request.POST.get("supplier_id")
                farmer_id = request.POST.get("farmer_id")
                warehouse_name = request.POST.get("warehouse_name")
                subtotal = float(request.POST.get("subtotal", 0))
                gst_amount = float(request.POST.get("gst_amount", 0))
                total_amount = float(request.POST.get("total_amount", 0))
                
                # Validate required fields
                if not source_type:
                    messages.error(request, "Please select a source type")
                    return redirect("Purchase:po", rfq_id=rfq_id)
                
                # Get or create warehouse
                warehouse = None
                if warehouse_name:
                    try:
                        warehouse = Warehouse.objects.filter(warehouse_name__icontains=warehouse_name).first()
                        if not warehouse:
                            warehouse = Warehouse.objects.filter(name__icontains=warehouse_name).first()
                        
                        if not warehouse:
                            # Create new warehouse
                            warehouse = Warehouse(
                                warehouse_name=warehouse_name,
                                location=extracted_data.get('warehouse_location', 'Main Location'),
                                capacity=1000,
                                is_active=True
                            )
                            warehouse.save()
                    except Exception as e:
                        logger.error(f"Error with warehouse: {e}")
                        try:
                            warehouse = Warehouse(
                                name=warehouse_name,
                                location=extracted_data.get('warehouse_location', 'Main Location'),
                                capacity=1000,
                                is_active=True
                            )
                            warehouse.save()
                        except Exception as e2:
                            logger.error(f"Error creating warehouse: {e2}")
                            messages.error(request, f"Error with warehouse: {str(e2)}")
                            return redirect("Purchase:po", rfq_id=rfq_id)
                
                # Prepare items for purchase order
                items = []
                product_index = 0
                
                while f"products[{product_index}][product_name]" in request.POST:
                    category_id = request.POST.get(f"products[{product_index}][category]")
                    subcategory_id = request.POST.get(f"products[{product_index}][subcategory]")
                    product_warehouse_name = request.POST.get(f"products[{product_index}][warehouse]") or warehouse_name
                    
                    if not category_id or not subcategory_id:
                        messages.error(request, f"Please select both category and subcategory for product {product_index + 1}")
                        return redirect("Purchase:po", rfq_id=rfq_id)
                    
                    try:
                        category = Category.objects.get(id=ObjectId(category_id))
                        subcategory = Subcategory.objects.get(id=ObjectId(subcategory_id))
                        
                        # Get or create product warehouse
                        product_warehouse = warehouse
                        if product_warehouse_name and product_warehouse_name != warehouse_name:
                            try:
                                product_warehouse = Warehouse.objects.filter(warehouse_name__icontains=product_warehouse_name).first()
                                if not product_warehouse:
                                    product_warehouse = Warehouse.objects.filter(name__icontains=product_warehouse_name).first()
                                if not product_warehouse:
                                    product_warehouse = warehouse
                            except Exception as e:
                                logger.error(f"Error with product warehouse: {e}")
                                product_warehouse = warehouse
                        
                        product_name = request.POST.get(f"products[{product_index}][product_name]")
                        sku = request.POST.get(f"products[{product_index}][sku]")
                        
                        if not sku or sku.strip() == "":
                            sku = generate_sku(product_name)
                        
                        quantity = int(float(request.POST.get(f"products[{product_index}][quantity]", 1)))
                        price = float(request.POST.get(f"products[{product_index}][price]", 0))
                        gst_amount_val = float(request.POST.get(f"products[{product_index}][gst_amount]", 18))
                        gst_value = float(request.POST.get(f"products[{product_index}][gst_value]", 0))
                        line_total = float(request.POST.get(f"products[{product_index}][line_total]", 0))
                        subtotal_val = float(request.POST.get(f"products[{product_index}][subtotal]", 0))
                        
                        product_data = {
                            'product_name': product_name,
                            'sku': sku,
                            'quantity': quantity,
                            'price': price,
                            'uom': request.POST.get(f"products[{product_index}][uom]", "PCS"),
                            'gst_amount': gst_amount_val,
                            'gst_value': gst_value,
                            'subtotal': subtotal_val,
                            'line_total': line_total,
                            'category': category,
                            'subcategory': subcategory,
                            'warehouse': product_warehouse,
                            'description': f"Product from purchase order - {product_name}",
                        }
                        items.append(ProductItem(**product_data))
                        product_index += 1
                        
                    except (Category.DoesNotExist, Subcategory.DoesNotExist) as e:
                        messages.error(request, f"Invalid category or subcategory for product {product_index + 1}")
                        return redirect("Purchase:po", rfq_id=rfq_id)
                    except Exception as e:
                        logger.error(f"Error processing product {product_index}: {e}")
                        messages.error(request, f"Error processing product {product_index + 1}: {str(e)}")
                        return redirect("Purchase:po", rfq_id=rfq_id)
                
                # Validate that we have at least one item
                if not items:
                    messages.error(request, "At least one product item is required")
                    return redirect("Purchase:po", rfq_id=rfq_id)
                
                # Get supplier or farmer based on selection
                supplier = None
                farmer = None
                
                try:
                    if source_type == 'supplier' and supplier_id:
                        supplier = Supplier.objects.get(id=ObjectId(supplier_id))
                    elif source_type == 'farmer' and farmer_id:
                        farmer = Farmer.objects.get(id=ObjectId(farmer_id))
                        
                except (Supplier.DoesNotExist, Farmer.DoesNotExist):
                    messages.error(request, "Selected supplier/farmer not found")
                    return redirect("Purchase:po", rfq_id=rfq_id)
                
                # Validate that either supplier or farmer is selected
                if not supplier and not farmer:
                    messages.error(request, "Please select either a supplier or farmer")
                    return redirect("Purchase:po", rfq_id=rfq_id)
                
                # Create purchase order
                purchase_order = PurchaseOrder(
                    rfq=rfq,
                    supplier=supplier,
                    farmer=farmer,
                    warehouse=warehouse,
                    items=items,
                    notes=notes,
                    subtotal=subtotal,
                    gst_amount=gst_amount,
                    total_amount=total_amount,
                    status="Pending",
                    created_by=user,
                )
                purchase_order.save()
                
                # Update RFQ status
                rfq.status = 'Completed'
                rfq.save()

                messages.success(request, "Purchase Order created successfully!")
                return redirect("Purchase:purchase_order_detail")
                
            except Exception as e:
                logger.error(f"Error creating purchase order: {e}")
                messages.error(request, f"Error creating purchase order: {str(e)}")
                return redirect("Purchase:po", rfq_id=rfq_id)

        # Prepare context for template
        context = {
            "rfq": rfq,
            "extracted_data": extracted_data,
            "source_type": source_type,
            "rfq_items": rfq_items,
            "suppliers": Supplier.objects.all(),
            "farmers": Farmer.objects.all(),
            "warehouses": Warehouse.objects.all(),
            "categories": Category.objects.all(),
            "subcategories": Subcategory.objects.all(),
        }
        
        return render(request, "PO.html", context)
    else:
        return redirect('Users:login')
    
#------------------------------------------------------------------------------------------------Purchase Order DEtails-----------------------------------------------------------------------------------------------------------------------------------
# Show all POs
def purchase_order_detail(request):
    if request.session.get("user_email") and request.session.get("user_role") in ["Purchase_Manager", "Admin"]:
        user = request.session.get("user_email")
        role = request.session.get("user_role")

        try:
            if role == "Admin":
                # Use select_related or prefetch_related to avoid N+1 queries and handle missing references
                purchase_orders = PurchaseOrder.objects.all().order_by("-created_at")
            else:  # Purchase_Manager
                purchase_orders = PurchaseOrder.objects.filter(created_by=user).order_by("-created_at")
            
            # Filter out purchase orders with broken references
            valid_purchase_orders = []
            for po in purchase_orders:
                try:
                    # Try to access the referenced fields to check if they exist
                    _ = po.supplier if hasattr(po, 'supplier') else None
                    _ = po.farmer if hasattr(po, 'farmer') else None
                    _ = po.warehouse if hasattr(po, 'warehouse') else None
                    _ = po.rfq if hasattr(po, 'rfq') else None
                    valid_purchase_orders.append(po)
                except Exception as e:
                    # Log the error and skip this purchase order
                    print(f"Skipping Purchase Order {po.id} due to broken reference: {e}")
                    continue

            return render(
                request,
                "purchase_order_detail.html",
                {
                    "purchase_orders": valid_purchase_orders,
                    "role": role,
                },
            )
        except Exception as e:
            print(f"Error in purchase_order_detail: {e}")
            # Return empty list if there's an error
            return render(
                request,
                "purchase_order_detail.html",
                {
                    "purchase_orders": [],
                    "role": role,
                    "error_message": "Error loading purchase orders. Please contact administrator."
                },
            )
    return redirect("Users:login_user")


# Update PO (only status for now)
def purchase_order_update(request, pk):
    if request.session.get('user_email') and request.session.get('user_role') == 'Purchase_Manager' or 'Admin':
        po = PurchaseOrder.objects.get(id=ObjectId(pk))

        if request.method == "POST":
            po.status = "Received"
            po.save()
            messages.success(request, f"Purchase Order {po.id} updated successfully")
            return redirect("Purchase:purchase_order_detail")
        return render(request, "po_order_update.html")
    return redirect('Users:login_user')


# Cancel PO
def purchase_order_cancel(request, pk):
    if request.session.get('user_email') and request.session.get('user_role') == 'Purchase_Manager' or 'Admin':
        po = PurchaseOrder.objects.get(id=ObjectId(pk))
        if request.method == "POST":
            po.status = "Cancelled"
            po.save()
            messages.warning(request, f"Purchase Order {po.id} has been cancelled")
            return redirect("Purchase:purchase_order_detail")
        return redirect("Purchase:purchase_order_detail")
    return redirect('Users:login_user')

from bson import ObjectId
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib import messages
from django.shortcuts import redirect
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from datetime import datetime
from django.conf import settings

def po_sent_mail(request, pk):
    if request.session.get('user_email') and request.session.get('user_role') in ['Purchase_Manager', 'Admin']:
        try:
            po = PurchaseOrder.objects.get(id=ObjectId(pk))

            recipient_email = None
            recipient_name = None
            recipient_type = None

            if po.supplier:
                recipient_email = po.supplier.email
                recipient_name = po.supplier.supplier_name
                recipient_type = "Supplier"
            elif po.farmer:
                recipient_email = po.farmer.email
                recipient_name = po.farmer.full_name
                recipient_type = "Farmer"

            if not recipient_email:
                messages.error(request, "No email found for this Purchase Order recipient")
                return redirect('Purchase:purchase_order_detail')

            # PDF context
            context = {
                'po': po,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Your Company Name'),
                'company_address': getattr(settings, 'COMPANY_ADDRESS', 'Your Company Address'),
                'company_phone': getattr(settings, 'COMPANY_PHONE', 'Your Company Phone'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'Your Company Email'),
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'po_number': f"PO/{po.created_at.strftime('%Y/%m')}/{str(po.id)[-6:]}" if getattr(po, 'created_at', None) else f"PO/{str(po.id)[-6:]}",
            }

            # Generate PDF
            html_string = render_to_string('po_pdf_template.html', context)
            font_config = FontConfiguration()
            html = HTML(string=html_string)
            css = CSS(string="""@page { size: A4; margin: 1in; }""")
            pdf_file = BytesIO()
            html.write_pdf(pdf_file, stylesheets=[css], font_config=font_config)
            pdf_file.seek(0)

            # Email content
            subject = f"Purchase Order - ID:{str(po.id)}"
            email_context = {
                'po': po,
                'recipient_name': recipient_name,
                'recipient_type': recipient_type,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Your Company Name'),
            }
            html_body = render_to_string('po_email_template.html', email_context)
            text_body = render_to_string('po_email_template.txt', email_context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach_alternative(html_body, "text/html")
            email.attach(f"PurchaseOrder_{po.id}.pdf", pdf_file.read(), "application/pdf")
            email.send()

            messages.success(request, f"Purchase Order sent successfully to {recipient_name} ({recipient_type}).")
        except Exception as e:
            messages.error(request, f"Error preparing PO email: {str(e)}")
        return redirect('Purchase:purchase_order_detail')
    return redirect('Users:login_user')

#______________________________________________________ Creating GRN ______________________________________________________________________________________________
def create_grn(request):
    if request.session.get('user_email') and request.session.get('user_role') in ['Inventory_Manager', 'Admin']:
        if request.method == "POST":
            po_id = request.POST.get("po_id")
            received_item_ids = request.POST.getlist("received_items[]")
            quantities = request.POST.getlist("quantities[]")
            tracking_number = request.POST.get("tracking_number", "").strip()
            received_at = request.POST.get("received_at")
            notes = request.POST.get("notes", "").strip()

            if not po_id:
                messages.error(request, "Please select a Purchase Order.")
                return redirect("Purchase:create_grn")

            try:
                po = PurchaseOrder.objects.get(id=ObjectId(po_id))
            except PurchaseOrder.DoesNotExist:
                messages.error(request, "Purchase Order not found.")
                return redirect("Purchase:create_grn")

            # VALIDATION 1: Check if GRN already exists for this PO
            existing_grn = GRN.objects.filter(purchase_order=po).first()
            if existing_grn:
                messages.error(request, f"GRN already exists for this Purchase Order (GRN ID: {existing_grn.id})")
                return redirect("Purchase:create_grn")

            # VALIDATION 2: PO status must be "Received"
            if po.status != "Received":
                messages.error(request, f"GRN can only be created for received orders. Current status: {po.status}")
                return redirect("Purchase:create_grn")

            if not po.items:
                messages.error(request, "No items found in the Purchase Order.")
                return redirect("Purchase:create_grn")

            # Validate warehouse existence
            if not getattr(po, 'warehouse', None):
                messages.error(request, "Warehouse information is missing from the Purchase Order.")
                return redirect("Purchase:create_grn")

            # Process GRN items
            grn_items = []
            total_received_amount = 0.0
            items_processed = 0
            inventory_items_to_process = []

            for i, quantity_str in enumerate(quantities):
                try:
                    quantity_received = float(quantity_str)

                    if quantity_received <= 0:
                        continue

                    if i < len(po.items):
                        po_item = po.items[i]

                        # Cap quantity to PO quantity
                        if quantity_received > po_item.quantity:
                            quantity_received = po_item.quantity
                            messages.warning(request, f"Quantity adjusted for {po_item.product_name}")

                        # Create GRN item
                        grn_item = ProductItem()
                        grn_item.product_name = po_item.product_name
                        grn_item.quantity = quantity_received
                        grn_item.price = po_item.price
                        grn_item.sku = getattr(po_item, 'sku', None)
                        grn_item.uom = getattr(po_item, 'uom', None)
                        grn_item.category = getattr(po_item, 'category', None)
                        grn_item.subcategory = getattr(po_item, 'subcategory', None)
                        grn_item.description = getattr(po_item, 'description', None)
                        grn_item.warehouse = getattr(po, 'warehouse', None)

                        grn_items.append(grn_item)

                        item_total = quantity_received * po_item.price
                        total_received_amount += item_total
                        items_processed += 1

                        # Prepare data for inventory update
                        inventory_items_to_process.append({
                            'product_name': po_item.product_name,
                            'sku': getattr(po_item, 'sku', f"SKU-{po_item.product_name[:10]}"),
                            'category': getattr(po_item, 'category', None),
                            'subcategory': getattr(po_item, 'subcategory', None),
                            'quantity': int(quantity_received),
                            'price': po_item.price,
                            'uom': getattr(po_item, 'uom', 'pcs'),
                            'warehouse': getattr(po, 'warehouse', None),
                            'description': getattr(po_item, 'description', ''),
                        })

                except (ValueError, IndexError) as e:
                    continue

            if items_processed == 0:
                messages.error(request, "No valid items were processed.")
                return redirect("Purchase:create_grn")

            # Parse datetime
            received_datetime = datetime.utcnow()
            if received_at:
                try:
                    received_datetime = datetime.strptime(received_at, "%Y-%m-%dT%H:%M")
                except ValueError:
                    pass

            # Create GRN
            try:
                grn_data = {
                    'purchase_order': po,
                    'warehouse': getattr(po, 'warehouse', None),
                    'items': grn_items,
                    'total_amount': round(total_received_amount, 2),
                    'tracking_number': tracking_number,
                    'received_at': received_datetime,
                    'notes': notes,
                    'created_by': request.user.username if request.user.is_authenticated else "System",
                    'created_at': datetime.utcnow()
                }

                if hasattr(po, 'supplier') and po.supplier:
                    grn_data['supplier'] = po.supplier

                if hasattr(po, 'farmer') and po.farmer:
                    grn_data['farmer'] = po.farmer

                grn = GRN(**grn_data)
                grn.save()

                # ============================================
                # INVENTORY UPDATE LOGIC (SKU + Product Name + Warehouse)
                # ============================================
                inventory_success_count = 0
                inventory_errors = []

                for item_data in inventory_items_to_process:
                    try:
                        sku = item_data['sku']
                        product_name = item_data['product_name']
                        warehouse = item_data['warehouse']

                        # Skip if SKU or warehouse is missing
                        if not sku or not warehouse:
                            error_msg = f"Skipping {product_name}: Missing SKU or warehouse"
                            inventory_errors.append(error_msg)
                            continue

                        # Find Product document for this specific warehouse
                        warehouse_product = Product.objects.filter(warehouse=warehouse).first()
                        
                        existing_item_index = None
                        
                        # Check if this SKU + Product Name already exists in this warehouse
                        if warehouse_product and hasattr(warehouse_product, 'items') and warehouse_product.items:
                            for idx, item in enumerate(warehouse_product.items):
                                # Match by BOTH SKU AND Product Name in the SAME warehouse
                                if (getattr(item, 'sku', None) == sku and 
                                    getattr(item, 'product_name', '').lower() == product_name.lower()):
                                    existing_item_index = idx
                                    break

                        if warehouse_product and existing_item_index is not None:
                            # UPDATE: Same SKU + Product Name in Same Warehouse
                            existing_item = warehouse_product.items[existing_item_index]
                            existing_item.quantity += item_data['quantity']  # Add to stock
                            existing_item.price = item_data['price']  # Update to latest price
                            existing_item.uom = item_data['uom']  # Update UOM
                            
                            # Update other fields
                            if item_data.get('category'):
                                existing_item.category = item_data['category']
                            if item_data.get('subcategory'):
                                existing_item.subcategory = item_data['subcategory']
                            if item_data.get('description'):
                                existing_item.description = item_data['description']
                            
                            # Recalculate total amount
                            warehouse_product.total_amount = sum(
                                item.quantity * item.price for item in warehouse_product.items
                            )
                            warehouse_product.save()
                            
                            inventory_success_count += 1
                            print(f"✅ Updated: {product_name} (SKU: {sku}) in {warehouse.warehouse_name} | New Qty: {existing_item.quantity}")

                        else:
                            # CREATE: New entry (either new warehouse or new SKU+Product in existing warehouse)
                            new_item = ProductItems(
                                product_name=product_name,
                                sku=sku,
                                category=item_data.get('category'),
                                subcategory=item_data.get('subcategory'),
                                quantity=item_data['quantity'],
                                price=item_data['price'],
                                uom=item_data['uom'],
                                description=item_data.get('description', ''),
                                warehouse=warehouse
                            )
                            
                            if warehouse_product:
                                # Add new item to existing warehouse Product document
                                warehouse_product.items.append(new_item)
                                warehouse_product.total_amount = sum(
                                    item.quantity * item.price for item in warehouse_product.items
                                )
                                warehouse_product.save()
                                print(f"✅ Created: {product_name} (SKU: {sku}) in existing warehouse {warehouse.warehouse_name} | Qty: {item_data['quantity']}")
                            else:
                                # Create new Product document for this warehouse
                                warehouse_product = Product(
                                    warehouse=warehouse,
                                    supplier=getattr(po, 'supplier', None),
                                    farmer=getattr(po, 'farmer', None),
                                    items=[new_item],
                                    total_amount=item_data['quantity'] * item_data['price'],
                                    created_at=datetime.utcnow()
                                )
                                warehouse_product.save()
                                print(f"✅ Created: {product_name} (SKU: {sku}) in NEW warehouse {warehouse.warehouse_name} | Qty: {item_data['quantity']}")
                            
                            inventory_success_count += 1

                    except Exception as inv_error:
                        error_msg = f"Error processing {item_data['product_name']}: {str(inv_error)}"
                        inventory_errors.append(error_msg)
                        print(f"❌ {error_msg}")

                # Success message
                success_msg = f"GRN created successfully! Items: {items_processed}, Amount: ${total_received_amount:.2f}"
                if inventory_success_count > 0:
                    success_msg += f" | {inventory_success_count} products added/updated in inventory."

                messages.success(request, success_msg)

                # Show any inventory errors as warnings
                for error in inventory_errors:
                    messages.warning(request, error)

                return redirect("Purchase:create_grn")

            except Exception as e:
                messages.error(request, f"Error creating GRN: {str(e)}")
                return redirect("Purchase:create_grn")

        # GET request - Load available POs
        try:
            received_pos = PurchaseOrder.objects.filter(status="Received").order_by('-created_at')
            available_pos = []
            
            for po in received_pos:
                try:
                    # Check if GRN already exists
                    existing_grn = GRN.objects.filter(purchase_order=po).first()
                    if not existing_grn:
                        # Validate references
                        _ = po.warehouse.warehouse_name if po.warehouse else "No Warehouse"
                        _ = po.supplier.supplier_name if po.supplier else None
                        _ = po.farmer.full_name if po.farmer else None
                        available_pos.append(po)
                except Exception as e:
                    print(f"Skipping PO {po.id} due to broken reference: {e}")
                    continue

            return render(request, "create_grn.html", {"purchase_orders": available_pos})

        except Exception as e:
            messages.error(request, f"Error loading purchase orders: {str(e)}")
            return render(request, "create_grn.html", {"purchase_orders": []})
    else:
        return redirect('Users:login_user')