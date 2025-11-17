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
    # path("Order_update",views.Order_update,name="Order_update"),

    path("ordertransportchallen",views.ordertransportchallen,name="ordertransportchallen"),

      # Actions in TC
    path('TCEdit',views.TCEdit,name="TCEdit"),
    path('TC_sent_email',views.TC_sent_email,name="TC_sent_email"),
    path("transport_challan_pdf_download",views.transport_challan_pdf_download,name="transport_challan_pdf_download"),

    # final bill creation for customer
    path("create_final_bill",views.create_final_bill,name="create_final_bill"),

    #Customer Replies
    path("customer_replies",views.customer_replies,name="customer_replies"),
    


      #transport challan view
      path("transport_challan_view",views.transport_challan_view,name="transport_challan_view"),


    #Delete
    path("orderdelete",views.orderdelete,name="orderdelete"),

    #ADMIN_CUSTOMER_ORDERS
    path('admin_customer_orders',views.admin_customer_orders,name="admin_customer_orders"),

    #INVOICE
    path("generate_invoice", views.generate_invoice, name="generate_invoice"),

     path('Orders/generate-pdf/<str:order_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    
]
