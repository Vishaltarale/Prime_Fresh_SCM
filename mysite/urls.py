from django.contrib import admin
from django.urls import path,include
from .import views


app_name = "mysite"

urlpatterns = [
    path("base",views.base,name="base"),

    path("user_index",views.index,name="index"),
        #ADMIN_RGISTRATION
    path("",views.admin_register,name="admin_register"),
    path("admin_save",views.admin_save,name="admin_save"),

    #supplier dash
    path("supplier_dash",views.supplier_dash,name="supplier_dash"),
    #ADMIN_LOGIN
    path("admin_login",views.admin_login,name="admin_login"),
    path("admin_login_dash",views.admin_login_dash,name="admin_login_dash"),

    #adminprofile and logout
    path("admin_profile",views.admin_profile,name="admin_profile"),
    path("admin_logout",views.admin_logout,name="admin_logout"),

    path("admin_index",views.admin_index,name="admin_index"),
    path("inventory",views.inventory,name="inventory"),

    #ENTITY_LIST DYNAMIC TEMPLATING 
    path('list/<str:entity>/', views.list_entity, name='list_entity'),

    #employeeregistration
    path("employee",views.employee,name="employee"),
    path("employee_register",views.employee_register,name="employee_register"),

    #Farmerregistration
    path("farmer",views.farmer,name="farmer"),
    path("farmer_register",views.farmer_register,name="farmer_register"),

    #SupplierRegitration
    path("supplier",views.supplier,name='supplier'),
    path("supplier_register",views.supplier_register,name="supplier_register"),

    #CustomerRegisteration
    path("customer",views.customer,name="customer"),
    path("customer_register",views.customer_register,name="customer_register"),

    #EDIT AND DELETE FOR THE ENTITY_LIST:
    path('edit_entity/<str:entity>/<str:object_id>', views.edit_entity, name='edit_entity'),
    path('delete_entity/<str:entity>/<str:object_id>', views.delete_entity, name='delete_entity'),

    #UserRegiteration
    path('user_reg',views.user_reg,name="user_reg"),


]