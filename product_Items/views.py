from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Product, Category, Subcategory
from datetime import datetime
from UOM.models import UOM,UOMConversionMatrix
from Location.models import Warehouse
from mysite.models import Supplier,Farmer

# Create your views here.
def products(request):
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    uoms = UOM.objects.all()
    warehouses = Warehouse.objects.all()
    suppliers = Supplier.objects.all()
    farmers = Farmer.objects.all()
    return render(request, 'products.html', {
        'categories': categories,
        'subcategories': subcategories,
        'uoms': uoms,
        'warehouses': warehouses,
        'suppliers': suppliers,
        'farmers': farmers
    })

from uuid import uuid4
from datetime import datetime
from UOM.models import UOMConversionMatrix

def product_register(request):
    if request.method == "POST":
            name = request.POST.get("name")
            sku = request.POST.get("sku")
            category_id = request.POST.get("category")
            subcategory_id = request.POST.get("subcategory")
            uom_id = request.POST.get("from_uom")
            price_per_unit = float(request.POST.get("price_per_unit"))
            quantity_available = int(request.POST.get("quantity_available"))
            description = request.POST.get("description", "")
            warehouse_id = request.POST.get("warehouse")

            # Source Logic (Farmer or Supplier)
            source_type = request.POST.get("source_type")
            supplier = None
            farmer = None

            if source_type == "supplier":
                supplier_id = request.POST.get("supplier_id")
                supplier = Supplier.objects.get(id=supplier_id)
            elif source_type == "farmer":
                farmer_id = request.POST.get("farmer_id")
                farmer = Farmer.objects.get(id=farmer_id)

            # Reference fields
            category = Category.objects.get(id=category_id)
            subcategory = Subcategory.objects.get(id=subcategory_id)
            uom = UOM.objects.get(id=uom_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)

            # Create and save the product
            product = Product(
                name=name,
                sku=sku,
                category=category,
                subcategory=subcategory,
                uom=uom,
                price_per_unit=price_per_unit,
                quantity_available=quantity_available,
                description=description,
                warehouse=warehouse,
                supplier=supplier,  # May be None
                farmer=farmer       # May be None
            )
            product.save()

            return redirect("product_Items:products")  # or wherever your product list is
    return redirect("product_Items:products")

#SUBCATEGORY
def subcategory(request):
    categories = Category.objects.all()
    return render(request,"subcategory.html",{'categories':categories})

def subcategory_register(request):
    if request.method == "POST":
            name = request.POST.get("name")
            category_id = request.POST.get("category")
            
            category = Category.objects.get(id=category_id)
            
            subcategory = Subcategory(name=name, category=category)
            subcategory.save()

            messages.success(request, "Subcategory registered successfully.")
            return redirect("mysite:admin_index")
    
    categories = Category.objects.all()
    return render(request, "subcategory.html", {"categories": categories})

#CATEGORY
def category(request):
      return render(request,"category.html")

def category_register(request):
    if request.method == "POST":
            name = request.POST.get("name")
            description = request.POST.get("description")

            if Category.objects(name=name).first():
                messages.warning(request, "Category with this name already exists.")
                return redirect("product_Items:category_register")

            category = Category(name=name, description=description)
            category.save()

            messages.success(request, "Category registered successfully.")
            return redirect("mysite:admin_index")
    
    return render(request, "category_registration.html")