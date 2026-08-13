from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Building,
    Expense,
    Lease,
    MaintenanceRequest,
    Payment,
    Property,
    Tenant,
    Unit,
)


class StyledModelForm(forms.ModelForm):
    """Apply a compact, consistent Bootstrap treatment to every operational form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                widget.attrs.setdefault("class", "form-select" if isinstance(widget, forms.Select) else "form-control")
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 3)
            if isinstance(widget, forms.DateInput):
                widget.attrs.setdefault("type", "date")


class PropertyForm(StyledModelForm):
    class Meta:
        model = Property
        fields = (
            "name",
            "code",
            "owner",
            "property_type",
            "status",
            "address",
            "district",
            "total_units",
            "description",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class BuildingForm(StyledModelForm):
    class Meta:
        model = Building
        fields = ("property", "name", "floors", "notes")


class UnitForm(StyledModelForm):
    class Meta:
        model = Unit
        fields = (
            "property",
            "building",
            "unit_number",
            "floor",
            "unit_type",
            "bedrooms",
            "bathrooms",
            "rent_amount",
            "service_charge",
            "status",
            "notes",
        )


class TenantForm(StyledModelForm):
    class Meta:
        model = Tenant
        fields = (
            "full_name",
            "phone",
            "alternative_phone",
            "email",
            "nationality",
            "national_id",
            "emergency_contact",
            "emergency_phone",
            "status",
        )


class LeaseForm(StyledModelForm):
    class Meta:
        model = Lease
        fields = (
            "lease_number",
            "tenant",
            "unit",
            "start_date",
            "end_date",
            "rent_amount",
            "billing_frequency",
            "due_day",
            "security_deposit_required",
            "security_deposit_received",
            "notice_period_days",
            "status",
            "notes",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit"].queryset = Unit.objects.exclude(status=Unit.Status.BLOCKED).select_related("property")


class PaymentForm(StyledModelForm):
    class Meta:
        model = Payment
        fields = ("lease", "amount", "payment_date", "payment_method", "reference", "notes")
        widgets = {"payment_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lease"].required = True
        self.fields["lease"].queryset = Lease.objects.filter(
            status__in=(Lease.Status.ACTIVE, Lease.Status.EXPIRING)
        ).select_related("tenant", "unit__property")
        self.fields["payment_date"].initial = timezone.localdate()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("amount") is not None and cleaned["amount"] <= 0:
            self.add_error("amount", "Payment amount must be greater than zero.")
        if cleaned.get("payment_method") != Payment.Method.CASH and not cleaned.get("reference"):
            self.add_error("reference", "Enter the provider or bank transaction reference.")
        return cleaned


class VoidPaymentForm(forms.Form):
    reason = forms.CharField(
        min_length=5,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Reason for voiding"}),
    )


class MaintenanceRequestForm(StyledModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = (
            "unit",
            "tenant",
            "category",
            "title",
            "description",
            "priority",
            "status",
            "assigned_to",
            "estimated_cost",
            "actual_cost",
        )


class ExpenseForm(StyledModelForm):
    class Meta:
        model = Expense
        fields = (
            "property",
            "category",
            "supplier",
            "description",
            "amount",
            "expense_date",
            "payment_method",
            "reference",
        )
        widgets = {"expense_date": forms.DateInput(attrs={"type": "date"})}

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise ValidationError("Expense amount must be greater than zero.")
        return amount
