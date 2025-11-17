from django.contrib import admin
from django.urls import path,include
from django_mongoengine import mongo_admin
from .import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "Purchase"

urlpatterns = [

path("purchase_dash",views.rfq_dashboard,name="purchase_dash"),
path("RFQGenerations",views.RFQGenerations,name="RFQGenerations"),

#RFQMODIFICATIONS
path("RFQEdit",views.RFQEdit,name="RFQEdit"),
path("rfq_sent_email",views.rfq_sent_email,name="rfq_sent_email"),
path("RFQDelete",views.RFQDelete,name="RFQDelete"),

#Response
path("rfq_responses_list",views.rfq_responses_list,name="rfq_responses_list"),

#For order confirm and cancel
# path("confirm_pur_ord",views.confirm_pur_ord,name="confirm_pur_ord"),


path("po/<str:rfq_id>/", views.PO, name="po"),
path("purchase_order_detail/", views.purchase_order_detail, name="purchase_order_detail"),
path("purchase_order_update/<str:pk>/", views.purchase_order_update, name="purchase_order_update"),
path("purchase_order_cancel/<str:pk>/", views.purchase_order_cancel, name="purchase_order_cancel"),

#purchase order sent mail
path("po_sent_mail/<str:pk>/", views.po_sent_mail, name="po_sent_mail"),

#GRN
path("create_grn",views.create_grn,name="create_grn"),

 ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)