from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from . import views_entities
from . import catalog
from . import orders
from . import reports
from . import dashboard
from . import profile
from . import purchase_orders
from . import analytics
from . import notifications

app_name = 'api'

urlpatterns = [
    path('dashboard/', dashboard.DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('analytics/', analytics.AnalyticsSummaryView.as_view(), name='analytics_summary'),

    path('notifications/', notifications.NotificationListView.as_view(), name='notifications'),
    path('notifications/read-all/', notifications.NotificationMarkAllReadView.as_view(), name='notifications_read_all'),
    path('notifications/<str:notification_id>/read/', notifications.NotificationMarkReadView.as_view(), name='notification_read'),

    path('purchase-orders/', purchase_orders.POListCreateView.as_view(), name='po_list_create'),
    path('purchase-orders/confirmed/', purchase_orders.POConfirmedForGRNView.as_view(), name='po_confirmed_for_grn'),
    path('purchase-orders/<str:po_id>/', purchase_orders.PODetailView.as_view(), name='po_detail'),
    path('purchase-orders/<str:po_id>/send/', purchase_orders.POSendView.as_view(), name='po_send'),
    path('purchase-orders/<str:po_id>/confirm/', purchase_orders.POConfirmView.as_view(), name='po_confirm'),
    path('purchase-orders/<str:po_id>/reject/', purchase_orders.PORejectView.as_view(), name='po_reject'),
    path('purchase-orders/<str:po_id>/payments/', purchase_orders.POPaymentView.as_view(), name='po_payments'),
    path('purchase-orders/<str:po_id>/refund/', purchase_orders.PORefundView.as_view(), name='po_refund'),
    path('po-response/<str:token>/', purchase_orders.POPublicView.as_view(), name='po_public'),

    path('orders/', orders.OrderListCreateView.as_view(), name='orders'),
    path('orders/<str:order_id>/', orders.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<str:order_id>/invoice/', orders.OrderInvoicePdfView.as_view(), name='order_invoice'),

    path('reports/warehouse-stock/<str:warehouse_id>/', reports.WarehouseStockDetailView.as_view(), name='warehouse_stock_detail'),
    path('reports/<str:report_type>/', reports.ReportDataView.as_view(), name='report_data'),
    path('reports/<str:report_type>/export/pdf/', reports.ReportExportPdfView.as_view(), name='report_export_pdf'),
    path('reports/<str:report_type>/export/excel/', reports.ReportExportExcelView.as_view(), name='report_export_excel'),

    path('entities/<str:entity>/meta/', views_entities.EntityMetaView.as_view(), name='entity_meta'),
    path('entities/<str:entity>/', views_entities.EntityListCreateView.as_view(), name='entity_list_create'),
    path('entities/<str:entity>/<str:object_id>/', views_entities.EntityDetailView.as_view(), name='entity_detail'),

    path('catalog/categories/', catalog.CategoryListCreateView.as_view(), name='categories'),
    path('catalog/categories/<str:object_id>/', catalog.CategoryDetailView.as_view(), name='category_detail'),
    path('catalog/subcategories/', catalog.SubcategoryListCreateView.as_view(), name='subcategories'),
    path('catalog/subcategories/<str:object_id>/', catalog.SubcategoryDetailView.as_view(), name='subcategory_detail'),
    path('catalog/uom/', catalog.UOMListCreateView.as_view(), name='catalog_uom'),
    path('catalog/uom/<str:object_id>/', catalog.UOMDetailView.as_view(), name='catalog_uom_detail'),
    path('catalog/conversions/', catalog.ConversionListCreateView.as_view(), name='conversions'),
    path('catalog/conversions/<str:object_id>/', catalog.ConversionDetailView.as_view(), name='conversion_detail'),
    path('catalog/products/', catalog.CatalogProductListCreateView.as_view(), name='catalog_products'),
    path('catalog/products/<str:object_id>/', catalog.CatalogProductDetailView.as_view(), name='catalog_product_detail'),

    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('auth/profile/', profile.MyProfileView.as_view(), name='my_profile'),

    path('warehouses/', views.WarehouseListView.as_view(), name='warehouses'),
    path('suppliers/', views.SupplierListView.as_view(), name='suppliers'),
    path('farmers/', views.FarmerListView.as_view(), name='farmers'),
    path('products/', views.ProductListView.as_view(), name='products'),

    path('grn/', views.GRNListCreateView.as_view(), name='grn_list_create'),
    path('grn/<str:grn_id>/', views.GRNDetailView.as_view(), name='grn_detail'),
    path('grn/<str:grn_id>/confirm/', views.GRNConfirmView.as_view(), name='grn_confirm'),
    path('grn/<str:grn_id>/reject/', views.GRNRejectView.as_view(), name='grn_reject'),
]
