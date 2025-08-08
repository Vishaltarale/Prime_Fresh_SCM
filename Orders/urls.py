from django.contrib import admin
from django.urls import path,include
from .import views

app_name = "Orders"

urlpatterns = [
    path("Order_dash",views.Order_dash,name="Order_dash"),
    path("Create_order",views.Create_order,name="Create_order"),
    path("Order_save",views.Order_save,name="Order_save"),

        #order edit
    path("orderedit",views.orderedit,name='orderedit'),
    path("Order_updates",views.Order_update,name="Order_update"),


    
]
