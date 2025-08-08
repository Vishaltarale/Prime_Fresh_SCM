from django.urls import path,include
from .import views

app_name="Users"

urlpatterns = [
    # path('user_reg',views.user_reg,name="user_reg"),
    
    path("user_register",views.user_register,name="user_register"),

    #USER_LOGIN
    path("login_user",views.login_user,name="login_user"),
    path("login_user_save",views.login_user_save,name="login_user_save"),

    #LOGOUT
    path('user_logout',views.user_logout,name="user_logout"),

    #USER_PROFILE
    path('user_profile',views.user_profile,name="user_profile"),
]
