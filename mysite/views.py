from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib.auth.models import User
from .models import Student,FruitInventory
from Orders.models import Order
from mysite.models import Employee,Farmer,Supplier,Customer
from datetime import date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from collections import defaultdict
from .models import FruitInventory
from Orders.models import Order
from Location.models import Warehouse,OfficeLocation
from mysite.models import admin1,Supplier
from Location.models import Warehouse
from product_Items.models import Product,Category,Subcategory
from UOM.models import UOM
from bson import ObjectId
import matplotlib.pyplot as plt

from django.shortcuts import render
from Users.decorators import dashboard_access

def supplier_dash(request):
    if request.session.get("user_email") is not None:
        suppliers = Supplier.objects.all()
        active = 0
        inactive = 0
        total = suppliers.count()
        active = suppliers.filter(status="Approve").count()
        inactive = total - active
        print(inactive)
        return render(request, "supplier_dash.html", {
            "suppliers": suppliers,
            "total_suppliers": total,
            "active_suppliers": active,
            "inactive_suppliers": inactive,
        })
    else:
        return redirect("Users:login_user")

def base(request):
    if request.session['user_email'] is not None:
        return render(request ,'base.html')
    else:
        return redirect("Users:login_user")

# def admin_register(request):
#     return render(request,"admin_register.html")

# def admin_save(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         email = request.POST.get("email")
#         password1 = request.POST.get("password1")
#         password2 = request.POST.get("password2")

#         if password1 == password2:
#             admin1(
#                 username=username,
#                 email=email,
#                 password=password1
#             ).save()
#             return redirect("mysite:admin_login")
#         else:
#             return redirect("mysite:admin_register")
#     return render(request, "admin_register.html")

#ADMIN_LOGIN
def admin_login(request):
    return render(request,"admin_login.html")

def admin_login_dash(request):
    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")

        data = admin1.objects(email=email, password=password).first()
        
        if data:
            request.session['email'] = email
            return redirect("mysite:admin_index")
        
    return render(request, "admin_login.html")

#USER_REGISTERATION
def user_reg(request):
    return render(request,'user_reg.html')

#ADMIN_PANEL
def admin_index(request):
    if request.session['user_email'] is not None:
        data = request.session['user_email'].split('@')[0]
        context = {
            'data':data,
            'employee_count': Employee.objects.count(),
            'customer_count': Customer.objects.count(),
            'supplier_count': Supplier.objects.count(),
            'farmer_count': Farmer.objects.count(),
            'office_count': OfficeLocation.objects.count(),
            'warehouse_count': Warehouse.objects.count(),
            'orders' : Order.objects.count(),
            'products' : Product.objects.count(),
        }
        
        return render(request, 'admin_dash.html', context)
    else:
        return redirect("mysite:login_user")
    
def admin_profile(request):
    email = request.session.get('user_email')
    if email:
        data = admin1.objects(email=email).first()
        if data:
            return render(request, "admin_profile.html", {'data': data})
    return redirect("mysite:login_user") 

def admin_logout(request):
    request.session.get('user_email',None)
    return redirect("mysite:login_user")
     

def index(request):
    if request.session.get('user_email') is not None:
        user_email = request.session['user_email']
        user_role = request.session.get('user_role')  # Get user role from session

        products = Product.objects()

        # Determine which orders to show based on user role
        if user_role == "Admin":
            # Admin sees all orders
            orders = Order.objects.all().order_by('order_date')
            Admin_orders = Order.objects.all()
            chart_orders = Order.objects.all()  # Use all orders for chart
        else:
            # Other users (Customer, Sales_Manager, etc.) see only their own orders
            orders = Order.objects(created_by=user_email).order_by('order_date')
            Admin_orders = []  # Empty for non-admin users
            chart_orders = Order.objects(created_by=user_email)  # Use user's orders for chart

        # Count pending orders based on user role
        if user_role == "Admin":
            pending_orders_count = Order.objects(status="Pending").count()
        else:
            pending_orders_count = Order.objects(created_by=user_email, status="Pending").count()

        # ----------------- Chart Data Preparation ------------------
        chart_data = defaultdict(lambda: {'Pending': 0, 'Completed': 0, 'Processing': 0, 'Cancelled': 0})
        
        # Use chart_orders instead of orders for chart generation
        for order in chart_orders:
            date_str = order.order_date.strftime('%Y-%m-%d')
            chart_data[date_str][order.status] += 1

        dates = sorted(chart_data.keys())
        statuses = ['Pending', 'Completed', 'Processing', 'Cancelled']
        status_colors = {
            'Pending': '#facc15',
            'Completed': '#22c55e',
            'Processing': '#3b82f6',
            'Cancelled': '#ef4444'
        }

        # ----------------- Line Chart Plotting ------------------
        fig, ax = plt.subplots(figsize=(10, 5))
        for status in statuses:
            values = [chart_data[date][status] for date in dates]
            ax.plot(dates, values, marker='o', label=status, color=status_colors[status])

        # Update chart title based on user role
        if user_role == "Admin":
            chart_title = 'All Orders Status Trend Over Time'
        else:
            chart_title = 'My Orders Status Trend Over Time'
        
        ax.set_title(chart_title)
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Orders')
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_image = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()

        # ----------------- Category Totals ------------------
        category_totals = defaultdict(float)
        for product in products:
            for item in product.items:
                if item.category and getattr(item.category, "name", None):
                    category_totals[item.category.name] += item.quantity

        # ----------------- Inventory Events ------------------
        today = date.today()
        events = []
        for product in products:
            for item in product.items:
                if item.quantity > 100:
                    events.append({
                        'icon': 'fas fa-sync',
                        'type': 'info',
                        'title': f"Restocked: {item.product_name}",
                        'message': f"{item.quantity} units restocked.",
                        'time': "Today"
                    })
                if hasattr(item, 'expiry_date') and item.expiry_date:
                    days_to_expiry = (item.expiry_date - today).days
                    if 0 <= days_to_expiry <= 5:
                        events.append({
                            'icon': 'fas fa-exclamation-triangle',
                            'type': 'warning',
                            'title': "Perishable Alert",
                            'message': f"{item.product_name} expires in {days_to_expiry} days.",
                            'time': "Today"
                        })
                if item.quantity == 0:
                    events.append({
                        'icon': 'fas fa-times-circle',
                        'type': 'danger',
                        'title': "Out of Stock",
                        'message': f"{item.product_name} is out of stock.",
                        'time': "Today"
                    })

        return render(request, "index.html", {
            'data': products,
            'Orders': orders,
            'suppliers': Supplier.objects.all(),
            'warehouses': Warehouse.objects.all(),
            'pending_orders_count': pending_orders_count,
            'chart_image': chart_image,
            'products': products,
            'category_totals': dict(category_totals),
            'events': events,
            'Admin_orders': Admin_orders
        })
    else:
        return redirect('Users:login_user')

#__________________________________________________________INVENTORY MANAGEMENT DASHBOARD_____________________________________________________________________________________
def inventory(request):
    if request.session.get('user_email') is None:
        return redirect('Users:login_user')

    # Check if warehouse filter is applied via GET parameter
    warehouse_filter = request.GET.get('warehouse', None)
    
    # ============================
    # STEP 1: Get all products
    # ============================
    products = Product.objects()

    # ============================
    # STEP 2: Aggregate Products (with warehouse filtering)
    # ============================
    global_products = defaultdict(lambda: {
        'product_name': '',
        'sku': '',
        'category': None,
        'subcategory': None,
        'total_quantity': 0,
        'price': 0,
        'uom': '',
        'warehouses': []  # Track which warehouses have this product
    })

    for product in products:
        warehouse_name = getattr(product.warehouse, 'warehouse_name', 'Unknown') if product.warehouse else 'Unknown'
        
        # Skip if warehouse filter is applied and doesn't match
        if warehouse_filter and warehouse_filter != warehouse_name:
            continue
            
        for item in product.items:
            sku = getattr(item, 'sku', None)
            product_name = getattr(item, 'product_name', '')

            if not sku or not product_name:
                continue

            key = sku  # Use SKU as unique identifier

            # Fill details
            global_products[key]['product_name'] = product_name
            global_products[key]['sku'] = sku
            global_products[key]['category'] = getattr(item, 'category', None)
            global_products[key]['subcategory'] = getattr(item, 'subcategory', None)
            global_products[key]['total_quantity'] += getattr(item, 'quantity', 0)
            global_products[key]['price'] = getattr(item, 'price', 0)
            global_products[key]['uom'] = getattr(item, 'uom', '')

            # Add warehouse info
            if warehouse_name not in global_products[key]['warehouses']:
                global_products[key]['warehouses'].append(warehouse_name)

    # Convert dict → list for template
    aggregated_products = [
        {
            'product_name': data['product_name'],
            'sku': data['sku'],
            'category': data['category'],
            'subcategory': data['subcategory'],
            'quantity': data['total_quantity'],
            'price': data['price'],
            'uom': data['uom'],
            'warehouses': ', '.join(data['warehouses'])
        }
        for data in global_products.values()
    ]
    aggregated_products.sort(key=lambda x: x['product_name'])

    # ============================
    # STEP 3: Category Totals (for chart)
    # ============================
    category_totals = defaultdict(float)
    for prod_data in aggregated_products:
        if prod_data['category'] and getattr(prod_data['category'], "name", None):
            category_totals[prod_data['category'].name] += prod_data['quantity']

    # ============================
    # STEP 4: Generate Category Pie Chart
    # ============================
    chart = None
    if category_totals:
        labels = list(category_totals.keys())
        sizes = list(category_totals.values())
        colors = ['#34D399', '#F59E0B', '#60A5FA', '#F87171', '#A78BFA', '#4ADE80']
        explode = [0.05] * len(labels)

        plt.figure(figsize=(5, 5))
        plt.pie(
            sizes, labels=labels, explode=explode, autopct='%1.1f%%',
            shadow=True, startangle=140, colors=colors[:len(labels)],
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )
        plt.gca().add_artist(plt.Circle((0, 0), 0.70, fc='white'))  # Donut style
        plt.axis('equal')
        plt.title("Stock Distribution by Category")

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', transparent=True)
        buffer.seek(0)
        chart = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

    # ============================
    # STEP 5: Warehouse-wise Events (Alerts)
    # ============================
    events = {}
    today = date.today()

    for product in products:
        warehouse_name = getattr(product.warehouse, 'warehouse_name', 'Unknown')

        # Skip if warehouse filter is applied and doesn't match
        if warehouse_filter and warehouse_filter != warehouse_name:
            continue
            
        for item in product.items:
            sku = getattr(item, 'sku', None)
            product_name = getattr(item, 'product_name', '')
            quantity = getattr(item, 'quantity', 0)

            if not sku or not product_name:
                continue

            key = f"{sku}_{warehouse_name}"  # unique product+warehouse key

            # CASE 1: Out of Stock (Red)
            if quantity == 0:   
                events[key] = {
                    'icon': 'fas fa-times-circle',
                    'type': 'danger',
                    'message': f"{product_name} with SKU {sku} is Out of stock in warehouse {warehouse_name} ",
                    'time': "Today"
                }

            # CASE 2: Low Stock (Yellow)
            elif 0 < quantity < 500:
                events[key] = {
                    'icon': 'fas fa-exclamation-triangle',
                    'type': 'warning',
                    'message': f"{product_name} with SKU {sku} has low stock ({quantity}) in warehouse {warehouse_name} ",
                    'time': "Today"
                }

            # CASE 3: Stock Added (Green) → replaces "Out of Stock"
            else:
                events[key] = {
                    'icon': 'fas fa-plus-circle',
                    'type': 'success',
                    'message': f"{product_name} with SKU {sku} is added to warehouse {warehouse_name} with {quantity} units ",
                    'time': "Today"
                }

    # Convert dict → list (unique alerts only)
    events = list(events.values())

    # ============================
    # STEP 6: Render Template
    # ============================
    return render(request, "inventory.html", {
        'aggregated_products': aggregated_products,
        'category_totals': dict(category_totals),
        'events': events,
        'chart': chart,
        'warehouses': Warehouse.objects.all()
    })
# ---------------------------------------------------------------#ADMIN PANEL VIEWS-------------------------------------------------------------------------------
#EMPLOYEEREGISTER
def employee(request):
    return render(request,"employee.html")

def employee_register(request):
    if request.method == "POST":
            full_name = request.POST['full_name']
            email = request.POST['email']
            phone = request.POST['phone']
            role = request.POST['role']
            joining_date = request.POST['joining_date']
            address = request.POST['address']

            employee = Employee(
                full_name=full_name,
                email=email,
                phone=phone,
                role=role,
                joining_date=joining_date,
                address=address
            )
            employee.save()
            return redirect('mysite:admin_index')
    return render(request, "employee.html")

#FARMERREGISTRATION
def farmer(request):
    if request.session.get('user_email') and request.session.get("user_role") == "Admin" or request.session.get("user_role") == "Purchase_Manager" or request.session.get("user_role") == "Inventory_Manager":
        return render(request,"farmer.html")
    else:
        return redirect("Users:login_user")

def farmer_register(request):
        if request.method == "POST":
                full_name = request.POST.get("full_name")
                email = request.POST.get("email")
                phone = request.POST.get("phone")
                address = request.POST.get("address")
                village = request.POST.get("village")
                district = request.POST.get("district")
                state = request.POST.get("state")
                registration_date = request.POST.get("registration_date")
                created_by = request.session.get('user_email')
                if request.session.get('user_role') == 'Admin':
                    farmer = Farmer(
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        address=address,
                        village=village,
                        district=district,
                        state=state,
                        registration_date=registration_date,
                        verified=True , # default
                        status='Approve',  # default
                        created_by=created_by
                    )
                    farmer.save()
                    return redirect("mysite:admin_index")
                elif request.session.get('user_role') == 'Purchase_Manager' or request.session.get('user_role') == 'Inventory_Manager':
                    farmer = Farmer(
                            full_name=full_name,
                            email=email,
                            phone=phone,
                            address=address,
                            village=village,
                            district=district,
                            state=state,
                            registration_date=registration_date,
                            verified=True , # default
                            status='Pending',  # default
                            created_by=created_by
                    )
                    farmer.save()
                    return redirect("mysite:admin_index")
                return render(request, "farmer_registration.html")
        return render(request, "farmer_registration.html")


#SUPPLIERRGISTRATION
def supplier(request):
    if request.session.get('user_email') and request.session.get("user_role") == "Admin" or request.session.get("user_role") == "Purchase_Manager" or request.session.get("user_role") == "Inventory_Manager":
        return render(request,"supplier.html")
    else:
        return redirect("Users:login_user")
    
def supplier_register(request):
    if request.method == "POST":
        created_by = request.session.get('user_email')
        supplier_name = request.POST.get("supplier_name")
        company_name = request.POST.get("company_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        state = request.POST.get("state")
        district = request.POST.get("district")
        registration_date = request.POST.get("registration_date")
        if request.session.get('user_role') == 'Purchase_Manager':
            supplier = Supplier(
                supplier_name=supplier_name,
                company_name=company_name,
                email=email,
                phone=phone,
                address=address,
                state=state,
                district=district,
                registration_date=registration_date,
                verified=False,  # default status
                status='Pending',  # default
                created_by=created_by
            )
            supplier.save()
            return redirect("mysite:admin_index")
        elif request.session.get('user_role') == 'Admin':
            context ={
                'total_suppliers' : Supplier.objects.count(),
                'active_suppliers' : Supplier.objects.filter(status="Active").count(),
                'inactive_suppliers' : Supplier.objects.filter(status="Inactive").count(),  

            }   
            supplier_name = request.POST.get("supplier_name")
            company_name = request.POST.get("company_name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")
            address = request.POST.get("address")
            state = request.POST.get("state")
            district = request.POST.get("district")
            registration_date = request.POST.get("registration_date")

            supplier = Supplier(
                supplier_name=supplier_name,
                company_name=company_name,
                email=email,
                phone=phone,
                address=address,
                state=state,
                district=district,
                registration_date=registration_date,
                verified=True,  # default status
                status='Approve',  # default
                created_by=created_by
            )
            supplier.save()
            return redirect("mysite:admin_index")   
        return render(request, "supplier.html","context:context")
    return render(request, "supplier.html")

#CUSTOMERREGITRATION
def customer(request):
    return render(request,"customer.html")  

def customer_register(request):
    if request.session.get('user_email') and request.session.get("user_role") == "Admin" or request.session.get("user_role") == "Sales_Manager":
        if request.method == "POST":
                full_name = request.POST.get("full_name")
                email = request.POST.get("email")
                phone = request.POST.get("phone")
                address = request.POST.get("address")
                city = request.POST.get("city")
                state = request.POST.get("state")
                registration_date = request.POST.get("registration_date")
                # Save to MongoDB
                if request.session.get('user_role') == 'Admin':
                    customer = Customer(
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        address=address,
                        city=city,
                        state=state,
                        registration_date=registration_date,
                        status='Approve',  # default
                    )
                    customer.save()

                customer = Customer(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,        
                    city=city,
                    state=state,
                    registration_date=registration_date,
                    status='Pending',  # default
                )
                customer.save()
                return redirect("mysite:admin_index")
        return render(request, "customer.html")
    else:
        return redirect("Users:login_user")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


MODEL_MAP = {
    'employee': Employee,
    'customer': Customer,
    'supplier': Supplier,
    'farmer': Farmer,
    'office': OfficeLocation,
    'warehouse': Warehouse,
    'orders': Order,
    'product': Product
}

def list_entity(request, entity):
    """Dynamic view to list entities with role-based filtering"""
    if request.session.get('user_email') and request.session.get("user_role") == "Customer":
        return redirect('Users:login_user')
    
    config = {
        'customer': {
            'title': 'Customers',
            'data': Customer.objects.all(),
            'headers': ['Name', 'Email', 'Phone', 'Address', 'City', 'State', 'Registration Date', 'Status', 'Actions'],
            'fields': ['full_name', 'email', 'phone', 'address', 'city', 'state', 'registration_date', 'status', 'actions'],
            'can_approve': True
        },
        'supplier': {
            'title': 'Suppliers',
            'data': Supplier.objects.all(),
            'headers': ['Name', 'Company', 'Email', 'Phone', 'Address', 'State', 'District', 'Registration Date', 'Status', 'Actions'],
            'fields': ['supplier_name', 'company_name', 'email', 'phone', 'address', 'state', 'district', 'registration_date', 'status', 'actions'],
            'can_approve': True
        },
        'farmer': {
            'title': 'Farmers',
            'data': Farmer.objects.all(),
            'headers': ['Name', 'Email', 'Phone', 'Address', 'Village', 'District', 'State', 'Registration Date', 'Status', 'Actions'],
            'fields': ['full_name', 'email', 'phone', 'address', 'village', 'district', 'state', 'registration_date', 'status', 'actions'],
            'can_approve': True
        },
        'office': {
            'title': 'Offices',
            'data': OfficeLocation.objects.all(),
            'headers': ['Office Name', 'Address', 'City', 'State', 'Pincode', 'Actions'],
            'fields': ['office_name', 'address', 'city', 'state', 'pincode', 'actions'],
            'can_approve': False
        },
        'warehouse': {
            'title': 'Warehouses',
            'data': Warehouse.objects.all(),
            'headers': ['Warehouse Name', 'Address', 'City', 'State', 'Pincode', 'Actions'],
            'fields': ['warehouse_name', 'address', 'city', 'state', 'pincode', 'actions'],
            'can_approve': False
        },
        'product': {
            'title': 'Products',
            'data': Product.objects.all(),
            'headers': ['Name', 'SKU', 'Category', 'Subcategory', 'UOM', 'Warehouse', 'Price/Unit', 'Quantity', 'Description', 'Created At', 'Supplier', 'Farmer', 'Actions'],
            'fields': ['name', 'sku', 'category', 'subcategory', 'uom', 'warehouse', 'price_per_unit', 'quantity_available', 'description', 'created_at', 'supplier', 'farmer', 'actions'],
            'can_approve': False
        }
    }

    if entity not in config:
        return render(request, '404.html', status=404)

    context = config[entity]
    context['entity'] = entity
    
    # Get user role from session
    user_role = request.session.get('user_role', '')
    context['user_role'] = user_role

    return render(request, 'list_entity.html', context)


def edit_entity(request, entity, object_id):
    if request.session.get('user_email') is None:
        return redirect('Users:login_user')
    """Edit an existing entity"""
    Model = MODEL_MAP.get(entity)
    if not Model:
        return render(request, '404.html', status=404)

    instance = Model.objects(id=object_id).first()
    if not instance:
        return render(request, '404.html', status=404)

    if request.method == 'POST':
        try:
            for field in request.POST:
                if field != 'csrfmiddlewaretoken' and hasattr(instance, field):
                    setattr(instance, field, request.POST[field])
            instance.save()
            messages.success(request, f'{entity.capitalize()} updated successfully!')
            return redirect('mysite:list_entity', entity=entity)
        except Exception as e:
            messages.error(request, f'Error updating {entity}: {str(e)}')

    # Exclude system fields from edit form
    excluded_fields = ['id', '_id', 'verified']
    fields = [field for field in instance._fields if field not in excluded_fields]

    return render(request, 'edit_entity_form.html', {
        'entity': entity,
        'instance': instance,
        'fields': fields
    })


def admin_approve_persons(request, entity, object_id):
    if request.session.get('user_email') is None:
        return redirect('Users:login_user')
    """Approve pending customers, suppliers, or farmers"""
    Model = MODEL_MAP.get(entity)
    if not Model:
        return render(request, '404.html', status=404)

    instance = Model.objects(id=object_id).first()
    if not instance:
        return render(request, '404.html', status=404)
    
    # Check if user is admin
    user_role = request.session.get('user_role', '')
    if user_role != 'Admin':
        messages.error(request, 'You do not have permission to approve.')
        return redirect('mysite:list_entity', entity=entity)
    
    # Approve the entity
    if hasattr(instance, 'status'):
        instance.status = "Approve"
        if hasattr(instance, 'verified'):
            instance.verified = True
        instance.save()
        messages.success(request, f'{entity.capitalize()} approved successfully!')
    else:
        messages.warning(request, f'This {entity} cannot be approved.')
    
    return redirect('mysite:list_entity', entity=entity)


def delete_entity(request, entity, object_id):
    """Delete an entity"""
    Model = MODEL_MAP.get(entity)
    if not Model:
        return render(request, '404.html', status=404)

    instance = Model.objects(id=object_id).first()
    if not instance:
        return render(request, '404.html', status=404)
    
    # Check permissions
    user_role = request.session.get('user_role', '')
    if user_role not in ['Admin', 'Sales_Manager', 'Purchase_Manager']:
        messages.error(request, 'You do not have permission to delete.')
        return redirect('mysite:list_entity', entity=entity)
    
    instance.delete()
    messages.success(request, f'{entity.capitalize()} deleted successfully!')
    return redirect('mysite:list_entity', entity=entity)

#____________________________________________________ADMIN PAGE CONFIRMATION _____________________________________________________________

def adminorderconfirmation(request, order_id):
    # Fetch order by ID
    customers = Customer.objects.all()
    warehouses = Warehouse.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    uoms = UOM.objects.all()

    order = Order.objects(id=ObjectId(order_id)).first()
    if not order:
        return render(request, "404.html", {"message": "Order not found"})

    if request.method == "POST":
        # Mark order as completed
        order.status = "Completed"
        order.save()
        for item in order.items:
            sku = item.sku
            ordered_qty = item.quantity

            product = Product.objects(items__sku=sku).first()
            if product:
                for p_item in product.items:
                    if p_item.sku == sku:
                        if p_item.quantity >= ordered_qty:
                            p_item.quantity -= ordered_qty
                        else:
      
                            return render(request, "error.html", {
                                "message": f"Not enough stock for {p_item.product_name}"
                            })
                product.save()

        return redirect("mysite:admin_index")  

    return render(request, "adminorderconfirmation.html", {"order": order,
        "Customers": customers,
        "warehouses": warehouses,
        "categories": categories,
        "subcategories": subcategories,
        "uoms": uoms,
         })