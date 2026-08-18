from django.contrib import admin
from django.urls import path,include
from .import views


app_name = "settings"

urlpatterns = [
    path("settings",views.settings,name="settings"),
]