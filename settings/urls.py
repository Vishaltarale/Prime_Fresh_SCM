from django.contrib import admin
from django.urls import path,include
from .import views


app_name = "Settings"

urlpatterns = [
    path("settings",views.settings,name="settings"),
]