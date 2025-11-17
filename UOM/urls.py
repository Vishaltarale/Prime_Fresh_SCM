from django.contrib import admin
from django.urls import path,include
from .import views


app_name = "UOM"

urlpatterns = [
    path("unit_of_measurement",views.unit_of_measurement,name="unit_of_measurement"),
    path("uom_register",views.uom_register,name="uom_register"),

    #Conversational_Matrix
    path("conversion_matrix",views.conversion_matrix,name="conversion_matrix"),
    path('conversion_register',views.conversion_register,name="conversion_register"),

]