from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from rentalapp import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="dashboard"), name="logout"),
    path("search/", views.global_search, name="global_search"),
    path("properties/", views.property_list, name="property_list"),
    path("properties/<int:pk>/", views.property_detail, name="property_detail"),
    path("units/", views.unit_list, name="unit_list"),
    path("units/<int:pk>/", views.unit_detail, name="unit_detail"),
    path("tenants/", views.tenant_list, name="tenant_list"),
    path("tenants/<int:pk>/", views.tenant_detail, name="tenant_detail"),
    path("leases/", views.lease_list, name="lease_list"),
    path("leases/<int:pk>/", views.lease_detail, name="lease_detail"),
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/record/", views.payment_create, name="payment_create"),
    path("payments/<int:pk>/receipt/", views.receipt_detail, name="receipt_detail"),
    path("payments/<int:pk>/void/", views.payment_void, name="payment_void"),
    path("arrears/", views.arrears, name="arrears"),
    path("maintenance/", views.maintenance_list, name="maintenance_list"),
    path("expenses/", views.expense_list, name="expense_list"),
    path("reports/", views.reports, name="reports"),
    path("audit-logs/", views.audit_log_list, name="audit_logs"),

    # Non-breaking aliases for the original prototype routes.
    path("add_property/", views.property_list, name="add_property_page"),
    path("add_Unit/", views.unit_list, name="add_Unit_page"),
    path("add_Tenant/", views.tenant_list, name="add_Tenant_page"),
    path("add_Payment/", views.payment_list, name="add_Payment_page"),
    path("add_MaintenanceRequest/", views.maintenance_list, name="add_MaintenanceRequest_page"),
]
