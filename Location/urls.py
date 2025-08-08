from django.contrib import admin
from django.urls import path,include
from django_mongoengine import mongo_admin
from .import views

app_name = 'Location'

urlpatterns = [
    #Office
    path('office', views.office,name="office"),
    path("office_register",views.office_register,name="office_register"),

    #Location
    path('warehouse',views.warehouse,name="warehouse"),
    path("warehouse_register",views.warehouse_register,name="warehouse_register"),

    #LOCATION
    path("location_dash",views.location_dash,name="location_dash"),

    #FOR REPORTS
    path("reports",views.reports,name="reports"),
    
    #for genereating reports all url i kept here.
    path('inventoryreport/<str:entity>', views.inventory_report, name='inventory_report'),
    path('reports/export/pdf/', views.export_pdf, name='export_pdf'),
    path('reports/export/excel/', views.export_excel, name='export_excel'),

]
