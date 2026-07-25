"""
URL configuration for rentalproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from rentalapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',login_view,name='index_page'),
    path('add_Tenant/',add_Tenant_view,name ='add_Tenant_page'),
    path('add_Booking/',add_Booking_view,name ='add_Booking_page'),
    path('add_Location/',add_Location_view,name ='add_Location_page'),
    path('add_Payment/',add_Payment_view,name ='add_Payment_page'),
    path('add_broker/',add_broker_view,name = 'add_broker_page'),
    path('add_landlord/',add_landlord_view, name='add_landlord_page'),
    path('add_property/',add_property_view, name= 'add_property_page'),
    path('add_MaintenanceRequest/',add_MaintenanceRequest_view, name ='add_MaintenanceRequest_page'),
    path('add_Complaint/', add_complaint_view, name='add_Complaint_page'),
    path('add_Unit/', add_Unit_view, name='add_Unit_page'),
    path('add_Notification/',add_Notification_view,name ='add_Notification_page'),

    #edits
    path('edit_property/<int:id>/',edit_property_view,name ='edit_property_page'),
    path('edit_payment/<int:id>/', edit_Payment_view, name='edit_Payment_page'),
    path('edit_Booking/<int:id>/',edit_Booking_view, name = 'edit_Booking_page'),
    path('edit_broker/<int:id>/',edit_broker_view, name = 'edit_broker_page'),
    path('edit_Location/<int:id>/', edit_Location_view, name='edit_Location_page'),
    path('edit_landlord/<int:id>/', edit_landlord_view, name='edit_landlord_page'),
    path('edit_Tenant/<int:id>/', edit_Tenant_view, name='edit_Tenant_page'),
    path('edit_MaintenanceRequest/<int:id>/', edit_MaintenanceRequest_view, name='edit_MaintenanceRequest_page'),
    path('edit_Complaint/<int:id>/', edit_Complaint_view, name='edit_Complaint_page'),
    path('edit_Unit/<int:id>/', edit_Unit_view, name='edit_Unit_page'),
    path('edit_Notification/<int:id>/', edit_Notification_view, name='edit_Notification_page'),


    #delete
    path('delete_property/<int:id>/',delete_property_view,name='delete_property'),
    path('delete_Payment/<int:id>/', delete_Payment_view, name='delete_Payment'),
    path('delete_Location/<int:id>/', delete_location_view, name='delete_Location'),
    path('delete_landlord/<int:id>/', delete_landlord_view, name='delete_landlord'),
    path('delete_unit/<int:id>/', delete_unit_view, name='delete_unit'),
    path('delete_tenant/<int:id>/', delete_tenant_view, name='delete_tenant'),
    path('delete_broker/<int:id>/', delete_broker_view, name='delete_broker'),
    path('delete_Booking/<int:id>/', delete_booking_view, name='delete_Booking'),
    path('delete_MaintenanceRequest/<int:id>/', delete_MaintenanceRequest_view, name='delete_MaintenanceRequest'),
    path('delete_complaint/<int:id>/', delete_complaint_view, name='delete_complaint'),
    path('delete_Notification/<int:id>/', delete_Notifications_view, name= 'delete_Notification_page'),
]


