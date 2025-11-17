from django.contrib import admin
from django.urls import path,include
from .import views


app_name = "product_Items"

urlpatterns = [
    path("products",views.products,name="products"),
    path("product_register",views.product_register,name="product_register"),

    #Subcategory
    path("subcategory",views.subcategory,name="subcategory"),
    path("subcategory_register",views.subcategory_register,name="subcategory_register"),

    #Category
    path("category",views.category,name="category"),
    path("category_register",views.category_register,name="category_register"),
]