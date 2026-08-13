import builtins
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Landlord(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="landlord_profile",
    )
    full_name = models.CharField(max_length=140, blank=True)
    phone = models.CharField(max_length=20)
    national_id = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ("full_name", "id")

    def __str__(self):
        return self.full_name or (self.user.get_full_name() if self.user else "Unnamed owner")


class Property(TimeStampedModel):
    TYPE_CHOICES = (
        ("apartments", "Apartments"),
        ("commercial", "Commercial"),
        ("mixed_use", "Mixed use"),
        ("villas", "Villas"),
        ("other", "Other"),
    )
    STATUS_CHOICES = (("active", "Active"), ("inactive", "Inactive"))

    owner = models.ForeignKey(
        Landlord,
        on_delete=models.PROTECT,
        related_name="properties",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    address = models.TextField()
    district = models.CharField(max_length=80, blank=True)
    property_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="apartments")
    description = models.TextField(blank=True)
    total_units = models.PositiveIntegerField(default=0, help_text="Planned or declared unit count")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "properties"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("property_detail", args=[self.pk])

    @property
    def unit_count(self):
        return self.units.count()

    @property
    def occupied_count(self):
        return self.units.filter(status=Unit.Status.OCCUPIED).count()

    @property
    def vacant_count(self):
        return self.units.filter(status=Unit.Status.AVAILABLE).count()

    @property
    def expected_monthly_rent(self):
        return self.units.aggregate(total=Sum("rent_amount"))["total"] or Decimal("0")


class Building(TimeStampedModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="buildings")
    name = models.CharField(max_length=100)
    floors = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("property__name", "name")
        constraints = [
            models.UniqueConstraint(fields=("property", "name"), name="unique_building_per_property")
        ]

    def __str__(self):
        return f"{self.property} · {self.name}"


class Unit(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        APPLICATION_PENDING = "application_pending", "Application pending"
        OCCUPIED = "occupied", "Occupied"
        NOTICE_GIVEN = "notice_given", "Notice given"
        MAINTENANCE = "maintenance", "Under maintenance"
        BLOCKED = "blocked", "Blocked"

    TYPE_CHOICES = (
        ("studio", "Studio"),
        ("apartment", "Apartment"),
        ("house", "House"),
        ("shop", "Shop"),
        ("office", "Office"),
        ("other", "Other"),
    )

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="units")
    building = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        related_name="units",
        null=True,
        blank=True,
    )
    unit_number = models.CharField(max_length=20)
    floor = models.CharField(max_length=30, blank=True)
    unit_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="apartment")
    bedrooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    rent_amount = models.DecimalField(max_digits=14, decimal_places=2)
    service_charge = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.AVAILABLE)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("property__name", "unit_number")
        constraints = [
            models.UniqueConstraint(fields=("property", "unit_number"), name="unique_unit_per_property")
        ]

    def __str__(self):
        return f"{self.property} · {self.unit_number}"

    def get_absolute_url(self):
        return reverse("unit_detail", args=[self.pk])

    @builtins.property
    def current_lease(self):
        return self.leases.filter(status=Lease.Status.ACTIVE).select_related("tenant").first()


class Tenant(TimeStampedModel):
    class Status(models.TextChoices):
        PROSPECTIVE = "prospective", "Prospective"
        ACTIVE = "active", "Active"
        NOTICE_GIVEN = "notice_given", "Notice given"
        FORMER = "former", "Former"
        BLOCKED = "blocked", "Blocked"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tenant_profile",
    )
    full_name = models.CharField(max_length=140, blank=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    nationality = models.CharField(max_length=80, default="Ugandan", blank=True)
    national_id = models.CharField(max_length=30, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ("full_name", "id")

    def __str__(self):
        return self.full_name or (self.user.get_full_name() if self.user else self.phone)

    def get_absolute_url(self):
        return reverse("tenant_detail", args=[self.pk])

    @property
    def active_lease(self):
        return self.leases.filter(status=Lease.Status.ACTIVE).select_related("unit__property").first()


class Lease(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending approval"
        ACTIVE = "active", "Active"
        EXPIRING = "expiring", "Expiring soon"
        EXPIRED = "expired", "Expired"
        TERMINATED = "terminated", "Terminated"
        RENEWED = "renewed", "Renewed"

    FREQUENCY_CHOICES = (("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annual", "Annual"))

    lease_number = models.CharField(max_length=30, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="leases")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="leases")
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount = models.DecimalField(max_digits=14, decimal_places=2)
    billing_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="monthly")
    due_day = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(28)]
    )
    security_deposit_required = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    security_deposit_received = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notice_period_days = models.PositiveSmallIntegerField(default=30)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-start_date", "lease_number")

    def __str__(self):
        return f"{self.lease_number} · {self.tenant}"

    def clean(self):
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError({"end_date": "The lease end date must be after the start date."})
        if self.security_deposit_received > self.security_deposit_required:
            raise ValidationError(
                {"security_deposit_received": "Received deposit cannot exceed the required deposit."}
            )
        if self.status == self.Status.ACTIVE and self.unit_id:
            conflicts = Lease.objects.filter(unit_id=self.unit_id, status=self.Status.ACTIVE)
            if self.pk:
                conflicts = conflicts.exclude(pk=self.pk)
            if conflicts.exists():
                raise ValidationError({"unit": "This unit already has an active lease."})

    @property
    def balance(self):
        return sum((charge.balance for charge in self.rent_charges.all()), Decimal("0"))

    @property
    def deposit_balance(self):
        return self.security_deposit_required - self.security_deposit_received


class ProtectedFinancialQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError("Financial records cannot be deleted. Void or reverse the transaction instead.")


class RentCharge(TimeStampedModel):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Partially paid"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="rent_charges")
    period = models.DateField(help_text="First day of the billing period")
    due_date = models.DateField()
    description = models.CharField(max_length=140, default="Monthly rent")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)

    objects = ProtectedFinancialQuerySet.as_manager()

    class Meta:
        ordering = ("due_date", "id")
        constraints = [
            models.UniqueConstraint(fields=("lease", "period"), name="unique_rent_period_per_lease")
        ]

    def __str__(self):
        return f"{self.lease.lease_number} · {self.period:%b %Y}"

    def delete(self, *args, **kwargs):
        raise ValidationError("Rent charges cannot be deleted. Void the charge instead.")

    @property
    def allocated_amount(self):
        return self.allocations.filter(payment__status=Payment.Status.POSTED).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")

    @property
    def balance(self):
        return max(self.amount - self.allocated_amount, Decimal("0"))

    def refresh_status(self):
        if self.status == self.Status.VOID:
            return
        paid = self.allocated_amount
        new_status = self.Status.PAID if paid >= self.amount else self.Status.PARTIAL if paid else self.Status.UNPAID
        if new_status != self.status:
            RentCharge.objects.filter(pk=self.pk).update(status=new_status, updated_at=timezone.now())
            self.status = new_status


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        MTN_MOMO = "mtn_momo", "MTN Mobile Money"
        AIRTEL_MONEY = "airtel_money", "Airtel Money"
        BANK = "bank", "Bank transfer/deposit"
        CHEQUE = "cheque", "Cheque"
        CARD = "card", "Card"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        VOID = "void", "Void"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="payments", null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField(default=timezone.localdate)
    payment_method = models.CharField(max_length=30, choices=Method.choices, default=Method.MTN_MOMO)
    reference = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.POSTED)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_rent_payments",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    void_reason = models.TextField(blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="voided_rent_payments",
        null=True,
        blank=True,
    )

    objects = ProtectedFinancialQuerySet.as_manager()

    class Meta:
        ordering = ("-payment_date", "-id")

    def __str__(self):
        return self.receipt_number or self.reference or f"Payment {self.pk}"

    def delete(self, *args, **kwargs):
        raise ValidationError("Payments cannot be deleted. Void the payment with a reason instead.")

    @property
    def allocated_amount(self):
        return self.allocations.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    @property
    def unallocated_amount(self):
        return max(self.amount - self.allocated_amount, Decimal("0"))


class PaymentAllocation(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="allocations")
    charge = models.ForeignKey(RentCharge, on_delete=models.PROTECT, related_name="allocations")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProtectedFinancialQuerySet.as_manager()

    class Meta:
        ordering = ("charge__due_date", "id")
        constraints = [
            models.UniqueConstraint(fields=("payment", "charge"), name="unique_payment_charge_allocation")
        ]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Allocation amount must be greater than zero."})
        if self.payment_id and self.charge_id and self.payment.lease_id != self.charge.lease_id:
            raise ValidationError("The payment and charge must belong to the same lease.")

    def __str__(self):
        return f"{self.payment} → {self.charge}"

    def delete(self, *args, **kwargs):
        raise ValidationError("Payment allocations are permanent financial records.")


class Receipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="receipt")
    number = models.CharField(max_length=30, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    objects = ProtectedFinancialQuerySet.as_manager()

    class Meta:
        ordering = ("-issued_at",)

    def __str__(self):
        return self.number

    def delete(self, *args, **kwargs):
        raise ValidationError("Receipts are permanent records and cannot be deleted.")


class MaintenanceRequest(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        REVIEWED = "reviewed", "Reviewed"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In progress"
        AWAITING_PARTS = "awaiting_parts", "Awaiting parts"
        COMPLETED = "completed", "Completed"
        VERIFIED = "verified", "Verified"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="maintenance_requests", null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="maintenance_requests")
    request_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    category = models.CharField(max_length=50, default="general")
    title = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.NEW)
    assigned_to = models.CharField(max_length=140, blank=True)
    estimated_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.request_number or self.title


class Expense(TimeStampedModel):
    CATEGORY_CHOICES = (
        ("repairs", "Repairs"),
        ("plumbing", "Plumbing"),
        ("electrical", "Electrical"),
        ("cleaning", "Cleaning"),
        ("security", "Security"),
        ("utilities", "Utilities"),
        ("staff", "Staff"),
        ("taxes", "Taxes"),
        ("other", "Other"),
    )
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="expenses")
    expense_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    supplier = models.CharField(max_length=140, blank=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    expense_date = models.DateField(default=timezone.localdate)
    payment_method = models.CharField(max_length=30, choices=Payment.Method.choices, default=Payment.Method.CASH)
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=(("posted", "Posted"), ("void", "Void")), default="posted"
    )
    void_reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_property_expenses",
    )

    objects = ProtectedFinancialQuerySet.as_manager()

    class Meta:
        ordering = ("-expense_date", "-id")

    def __str__(self):
        return self.expense_number or self.description

    def delete(self, *args, **kwargs):
        raise ValidationError("Expenses cannot be deleted. Void the expense instead.")


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=50)
    object_label = models.CharField(max_length=255)
    old_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.action} · {self.object_label}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    level = models.CharField(
        max_length=20,
        choices=(("info", "Info"), ("warning", "Warning"), ("danger", "Danger"), ("success", "Success")),
        default="info",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.message[:50]


# Legacy records retained for migration compatibility and gradual product expansion.
class Complaint(models.Model):
    STATUS = (("Open", "Open"), ("Resolved", "Resolved"), ("Closed", "Closed"))
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default="Open")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class Booking(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Cancelled", "Cancelled"),
        ("Completed", "Completed"),
    )
    booking_date = models.DateField()
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.customer_name


class Broker(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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


# Backwards-compatible imports used by older code and migrations.
landlord = Landlord
broker = Broker
