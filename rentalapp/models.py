from django.db import models
from django.contrib.auth.models import User


class Property(models.Model):
    names = models.CharField(max_length=100)
    address = models.TextField()
    property_type = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    total_units = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.names


class Unit(models.Model):
    propertyy = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit_number = models.CharField(max_length=20)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_occupied = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.propertyy} - {self.unit_number}"


class Tenant(models.Model):
    user_name = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    national_id = models.CharField(max_length=30)
    emergency_contact = models.CharField(max_length=100)

    def __str__ (self):
        return self.user_name.username




class Payment(models.Model):
  
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    reference = models.CharField(max_length=100)

    def __str__(self):
        return self.reference


class MaintenanceRequest(models.Model):
    STATUS = (
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Complaint(models.Model):
    STATUS = (
        ("Open", "Open"),
        ("Resolved", "Resolved"),
        ("Closed", "Closed"),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default="Open")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:30]


class Booking(models.Model):
    booking_date = models.DateField()
    check_in_date = models.DateField()
    check_out_date = models.DateField()

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.customer_name



class landlord(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    national_id = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    email = models.EmailField()
    occupation = models.CharField(max_length=100)

    def __str__(self):
        return self.user.get_full_name()  




class broker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    national_id = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.user.get_full_name()        



class Location(models.Model):
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    village = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.city}, {self.district}"        