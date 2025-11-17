from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Category, Subcategory
from datetime import datetime
from UOM.models import UOM,UOMConversionMatrix
from Location.models import Warehouse
from mysite.models import Supplier,Farmer

from product_Items.models import main_product


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

from django.shortcuts import redirect, render
from .models import Product  # adjust import

def product_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")

        # Generate unique SKU
        sku = generate_sku(name)

        # Save product
        product = main_product(name=name, category=category, sku=sku)
        product.save()

        return redirect("product_items:products")

    return render(request, "products/product_register.html")


def generate_sku(product_name):
    # Step 1: Get first 3 letters as prefix
    prefix = product_name.strip().upper()[:3]
    
    # Step 2: Find last used SKU with same prefix
    last_product = main_product.objects(sku__startswith=prefix).order_by("-sku").first()
    
    if last_product:
        # Extract numeric part (last 3 chars)
        last_number = int(last_product.sku[-3:])
        new_number = last_number + 1
    else:
        new_number = 1  # Start from 001
    
    # Step 3: Format into 3-digit string
    sku = f"{prefix}{new_number:03d}"
    return sku

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