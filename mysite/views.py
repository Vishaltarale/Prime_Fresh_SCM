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

def supplier_dash(request):
    suppliers = Supplier.objects.all()
    active = 0
    inactive = 0
    total = suppliers.count()
    # active = suppliers.filter(status="Active").count()
    inactive = total - active
    print(inactive)
    return render(request, "supplier_dash.html", {
        "suppliers": suppliers,
        "total_suppliers": total,
        "active_suppliers": active,
        "inactive_suppliers": inactive,
    })

def base(request):
    if request.session['user_email'] is not None:
        return render(request ,'base.html')
    else:
        return redirect("Users:login_user")

def admin_register(request):
    return render(request,"admin_register.html")

def admin_save(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 == password2:
            admin1(
                username=username,
                email=email,
                password=password1
            ).save()
            return redirect("mysite:admin_login")
        else:
            return redirect("mysite:admin_register")
    return render(request, "admin_register.html")

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
    if request.session['email'] is not None:
        data = request.session['email'].split('@')[0]
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
        return redirect("mysite:admin_login")
    
def admin_profile(request):
    email = request.session.get('email')
    if email:
        data = admin1.objects(email=email).first()
        if data:
            return render(request, "admin_profile.html", {'data': data})
    return redirect("mysite:admin_login")  # fallback if session or data not found

def admin_logout(request):
    request.session.get('email',None)
    return redirect("mysite:admin_login")
     

def index(request):
    # Session-based user login check
    if request.session.get('user_email') is not None:
        user_email = request.session['user_email']

        # Fetch all products
        data = Product.objects.all()

        # Filter only user-created orders
        orders = Order.objects(created_by=user_email).order_by('order_date')

        # Count pending orders
        pending_orders_count = Order.objects(status="Pending").count()

        # ----------------- Chart Data Preparation ------------------
        # Collect data per date and status
        chart_data = defaultdict(lambda: {'Pending': 0, 'Completed': 0, 'Processing': 0, 'Cancelled': 0})
        for order in orders:
            date_str = order.order_date.strftime('%Y-%m-%d')
            chart_data[date_str][order.status] += 1

        # Extract labels and values
        dates = sorted(chart_data.keys())  # sort for consistent x-axis
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

        ax.set_title('Order Status Trend Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Orders')
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Convert chart to base64 for embedding in template
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()

        products = Product.objects()
        category_totals = defaultdict(float)
        for product in products:
            if product.category and product.category.name:
                category_totals[product.category.name] += product.quantity_available

        today = date.today()
        events = []
        for item in products:
            if item.quantity_available > 100:
                events.append({
                    'icon': 'fas fa-sync',
                    'type': 'info',
                    'title': f"Restocked: {item.name}",
                    'message': f"{item.quantity_available} units restocked.",
                    'time': "Today"
                })
            if hasattr(item, 'expiry_date') and item.expiry_date:
                days_to_expiry = (item.expiry_date - today).days
                if 0 <= days_to_expiry <= 5:
                    events.append({
                        'icon': 'fas fa-exclamation-triangle',
                        'type': 'warning',
                        'title': "Perishable Alert",
                        'message': f"{item.name} expires in {days_to_expiry} days.",
                        'time': "Today"
                    })
            if item.quantity_available == 0:
                events.append({
                    'icon': 'fas fa-times-circle',
                    'type': 'danger',
                    'title': "Out of Stock",
                    'message': f"{item.name} is out of stock.",
                    'time': "Today"
                })

        # ----------------- Render Dashboard ------------------
        return render(request, "index.html", {
            'data': data,
            'Orders': orders,
            'suppliers': Supplier.objects.all(),
            'warehouses': Warehouse.objects.all(),
            'pending_orders_count': pending_orders_count,
            'chart_image': image_base64,
             'products': products,
            'category_totals': dict(category_totals),
            'events': events,
        })
    # Redirect if session invalid
    return redirect('Users:login_user')

# Inventory Dashboard
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from product_Items.models import Product
from collections import defaultdict

def inventory(request):
    if request.session.get('user_email') is not None:
        products = Product.objects()  # MongoEngine's .objects returns a queryset

        # Dynamically calculate total quantity by category
        category_totals = defaultdict(float)
        for product in products:
            if product.category and product.category.name:
                category_totals[product.category.name] += product.quantity_available

        # Prepare pie chart
        chart = None
        if category_totals:
            labels = list(category_totals.keys())
            sizes = list(category_totals.values())
            colors = ['#34D399', '#F59E0B', '#60A5FA', '#F87171', '#A78BFA', '#4ADE80']
            explode = [0.05] * len(labels)

            plt.figure(figsize=(5, 5))
            wedges, texts, autotexts = plt.pie(
                sizes,
                labels=labels,
                explode=explode,
                autopct='%1.1f%%',
                shadow=True,
                startangle=140,
                colors=colors[:len(labels)],
                wedgeprops={'edgecolor': 'white', 'linewidth': 2}
            )

            centre_circle = plt.Circle((0, 0), 0.70, fc='white')
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
            plt.axis('equal')
            plt.title("Stock Distribution by Category")

            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', transparent=True)
            buffer.seek(0)
            chart = base64.b64encode(buffer.read()).decode('utf-8')
            buffer.close()
            plt.close()

        # Events
        today = date.today()
        events = []
        for item in products:
            if item.quantity_available > 100:
                events.append({
                    'icon': 'fas fa-sync',
                    'type': 'info',
                    'title': f"Restocked: {item.name}",
                    'message': f"{item.quantity_available} units restocked.",
                    'time': "Today"
                })
            if hasattr(item, 'expiry_date') and item.expiry_date:
                days_to_expiry = (item.expiry_date - today).days
                if 0 <= days_to_expiry <= 5:
                    events.append({
                        'icon': 'fas fa-exclamation-triangle',
                        'type': 'warning',
                        'title': "Perishable Alert",
                        'message': f"{item.name} expires in {days_to_expiry} days.",
                        'time': "Today"
                    })
            if item.quantity_available == 0:
                events.append({
                    'icon': 'fas fa-times-circle',
                    'type': 'danger',
                    'title': "Out of Stock",
                    'message': f"{item.name} is out of stock.",
                    'time': "Today"
                })

        return render(request, "inventory.html", {
            'products': products,
            'category_totals': dict(category_totals),
            'events': events,
            'chart': chart
        })
    else:
        return redirect("Users:user_login")


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
    return render(request,"farmer.html")

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


            farmer = Farmer(
                full_name=full_name,
                email=email,
                phone=phone,
                address=address,
                village=village,
                district=district,
                state=state,
                registration_date=registration_date,
                verified=False  # default
            )
            farmer.save()
            return redirect("mysite:admin_index")
    return render(request, "farmer_registration.html")

#SUPPLIERRGISTRATION
def supplier(request):
    return render(request,"supplier.html")

def supplier_register(request):
    if request.method == "POST":
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
                verified=False  # default status
            )
            supplier.save()
            return redirect("mysite:admin_index")
    return render(request, "supplier.html")

#CUSTOMERREGITRATION
def customer(request):
    return render(request,"customer.html")

def customer_register(request):
    if request.method == "POST":
            full_name = request.POST.get("full_name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")
            address = request.POST.get("address")
            city = request.POST.get("city")
            state = request.POST.get("state")
            registration_date = request.POST.get("registration_date")
            # Save to MongoDB
            customer = Customer(
                full_name=full_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                registration_date=registration_date
            )
            customer.save()

            return redirect("mysite:admin_index")
    return render(request, "customer.html")

#ENTITY_LIST DYnamic templating views
MODEL_MAP = {
    'employee': Employee,
    'customer': Customer,
    'supplier': Supplier,
    'farmer': Farmer,
    'office': OfficeLocation,
    'warehouse': Warehouse,
    'Orders' : Order,
    'Product' : Product
}

def list_entity(request, entity):
    config = {
        'employee': {
            'title': 'Employees',
            'data': Employee.objects.all(),
            'headers': ['Name', 'Email', 'Phone', 'Role', 'Joining Date', 'Address','Actions'],
            'fields': ['full_name', 'email', 'phone', 'role', 'joining_date','address', 'actions']
        },
        'customer': {
            'title': 'Customers',
            'data': Customer.objects.all(),
            'headers': ['Name', 'Email', 'Phone', 'Address','City','State','Registration_date','Actions'],
            'fields': ['full_name', 'email', 'phone', 'address','city','state','registration_date','actions']
        },
        'supplier': {
            'title': 'Suppliers',
            'data': Supplier.objects.all(),
            'headers': ['Name','Company', 'Email', 'Phone','Address','State','District','Registration_date','Actions'],
            'fields': ['supplier_name', 'company_name', 'email', 'phone', 'address','state','district','registration_date','actions']
        },
        'farmer': {
            'title': 'Farmers',
            'data': Farmer.objects.all(),
            'headers': ['Name', 'Email', 'Phone','addrees','village','District','State','Registration_date','Actions'],
            'fields': ['full_name', 'email', 'phone','address', 'village','district','state','registration_date','actions']
        },
        'office': {
            'title': 'Offices',
            'data': OfficeLocation.objects.all(),
            'headers': ['Office Name', 'Address', 'City', 'State', 'Pincode','Actions'],
            'fields': ['office_name', 'address', 'city', 'state', 'pincode','actions']
        },
        'warehouse': {
            'title': 'Warehouses',
            'data': Warehouse.objects.all(),
            'headers': ['Warehouse Name', 'Address', 'City', 'State', 'Pincode','Actions'],
            'fields': ['warehouse_name', 'address', 'city', 'state', 'pincode','actions']
        },
        'Orders':{
            'title':'Orders',
            'data': Order.objects.all(),
            'headers': ['customer_name','order_date','status','total_amount','payment_status','delivery_address','created_by','Actions'],
            'fields' : ['customer_name','order_date','status','total_amount','payment_status','delivery_address','created_by','actions']
        },
        'Product':{
            'title' : 'Product',
            'data' : Product.objects.all(),
            'headers' : ['name','sku','category','subcategory','uom','warehouse','price_per_unit','quantity_available','description','created_at','supplier','farmer','Actions'],
            'fields' : ['name','sku','category','subcategory','uom','warehouse','price_per_unit','quantity_available','description','created_at','supplier','farmer','actions']
        }
    }

    if entity not in config:
        return render(request, '404.html', status=404)

    context = config[entity]
    context['entity'] = entity

    return render(request, 'list_entity.html', context)

def edit_entity(request, entity, object_id):
    Model = MODEL_MAP.get(entity)
    if not Model:
        return render(request, '404.html', status=404)

    instance = Model.objects(id=object_id).first()
    if not instance:
        return render(request, '404.html', status=404)

    if request.method == 'POST':
        for field in request.POST:
            if hasattr(instance, field):
                setattr(instance, field, request.POST[field])
        instance.save()
        return redirect('mysite:list_entity', entity=entity)

    return render(request, 'edit_entity_form.html', {
        'entity': entity,
        'instance': instance,
        'fields': [field for field in instance._fields if field not in ('id',)]
    })

def delete_entity(request, entity, object_id):
    Model = MODEL_MAP.get(entity)
    if not Model:
        return render(request, '404.html', status=404)

    instance = get_object_or_404(Model, id=object_id)
    instance.delete()
    return redirect('mysite:list_entity', entity=entity)