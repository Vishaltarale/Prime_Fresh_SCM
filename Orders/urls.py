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
    #Delete
    path("orderdeletes",views.orderdelete,name="orderdelete"),

    #ADMIN_CUSTOMER_ORDERS
    path('admins_customer_orders',views.admin_customer_orders,name="admin_customer_orders"),

    #INVOICE
    path("generates_invoice", views.generate_invoice, name="generate_invoice"),

    path('Orderss/generate-pdf/<str:order_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf')


    
]
