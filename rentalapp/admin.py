from django.contrib import admin
from .models import *

admin.site.register(Property)
admin.site.register(Unit)
admin.site.register(Tenant)
admin.site.register(Payment)
admin.site.register(Complaint)
admin.site.register(MaintenanceRequest)
admin.site.register(Notification)
admin.site.register(Location)
admin.site.register(broker)
admin.site.register(Booking)

# Register your models here.
