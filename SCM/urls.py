"""
URL configuration for SCM project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django_mongoengine import mongo_admin

urlpatterns = [
    path('mongo-admin/', mongo_admin.site.urls),
    path('',include('mysite.urls')),
    path('Orders/',include('Orders.urls')),
    path('Customer/',include('Customer.urls')),
    path('product_Items/',include('product_Items.urls')),
    path('UOM/',include('UOM.urls')),
    path("Location/",include('Location.urls')),
    path('Users/',include('Users.urls')),
    path('Settings/',include('settings.urls')),
    path("Purchase/",include("Purchase.urls"))
]
