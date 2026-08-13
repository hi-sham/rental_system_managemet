import calendar
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import AuditLog, Expense, Lease, MaintenanceRequest, Payment, PaymentAllocation, Receipt, RentCharge, Unit


def _next_month(value):
    return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


def _due_date(year, month, due_day):
    return date(year, month, min(due_day, calendar.monthrange(year, month)[1]))


@transaction.atomic
def generate_rent_schedule(lease):
    """Create an immutable monthly schedule. Existing periods are never duplicated."""
    period = lease.start_date.replace(day=1)
    final_period = lease.end_date.replace(day=1)
    month_step = {"monthly": 1, "quarterly": 3, "annual": 12}.get(lease.billing_frequency)
    if not month_step:
        raise ValidationError("Unsupported billing frequency.")
    created = []
    while period <= final_period:
        calculated_due_date = _due_date(period.year, period.month, lease.due_day)
        charge, was_created = RentCharge.objects.get_or_create(
            lease=lease,
            period=period,
            defaults={
                "due_date": max(lease.start_date, calculated_due_date),
                "description": f"Rent · {period:%B %Y}",
                "amount": lease.rent_amount,
            },
        )
        if was_created:
            created.append(charge)
        for _ in range(month_step):
            period = _next_month(period)
    return created


def audit(*, actor, action, instance, old_value=None, new_value=None, request=None):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
    ip_address = (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) if request else None
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=instance._meta.verbose_name,
        object_id=str(instance.pk),
        object_label=str(instance),
        old_value=old_value or {},
        new_value=new_value or {},
        ip_address=ip_address,
    )


@transaction.atomic
def post_payment(*, cleaned_data, actor=None, request=None):
    lease = cleaned_data["lease"]
    payment = Payment.objects.create(
        lease=lease,
        amount=cleaned_data["amount"],
        payment_date=cleaned_data["payment_date"],
        payment_method=cleaned_data["payment_method"],
        reference=cleaned_data.get("reference", ""),
        notes=cleaned_data.get("notes", ""),
        received_by=actor if getattr(actor, "is_authenticated", False) else None,
    )
    payment.receipt_number = f"RC-{payment.payment_date.year}-{payment.pk:06d}"
    payment.save(update_fields=("receipt_number", "updated_at"))
    Receipt.objects.create(payment=payment, number=payment.receipt_number)

    remaining = payment.amount
    charges = lease.rent_charges.exclude(status=RentCharge.Status.VOID).order_by("due_date", "id")
    for charge in charges:
        if remaining <= 0:
            break
        outstanding = charge.balance
        if outstanding <= 0:
            continue
        allocation = min(remaining, outstanding)
        PaymentAllocation.objects.create(payment=payment, charge=charge, amount=allocation)
        remaining -= allocation
        charge.refresh_status()

    audit(
        actor=actor,
        action="payment_posted",
        instance=payment,
        new_value={
            "amount": str(payment.amount),
            "lease": lease.lease_number,
            "allocated": str(payment.allocated_amount),
            "unallocated": str(payment.unallocated_amount),
        },
        request=request,
    )
    return payment


@transaction.atomic
def void_payment(*, payment, reason, actor=None, request=None):
    if payment.status == Payment.Status.VOID:
        raise ValidationError("This payment has already been voided.")
    old_value = {"status": payment.status, "amount": str(payment.amount), "reference": payment.reference}
    payment.status = Payment.Status.VOID
    payment.void_reason = reason
    payment.voided_at = timezone.now()
    payment.voided_by = actor if getattr(actor, "is_authenticated", False) else None
    payment.save(update_fields=("status", "void_reason", "voided_at", "voided_by", "updated_at"))
    for allocation in payment.allocations.select_related("charge"):
        allocation.charge.refresh_status()
    audit(
        actor=actor,
        action="payment_voided",
        instance=payment,
        old_value=old_value,
        new_value={"status": payment.status, "reason": reason},
        request=request,
    )
    return payment


def assign_reference(instance):
    if isinstance(instance, MaintenanceRequest) and not instance.request_number:
        instance.request_number = f"MR-{timezone.localdate().year}-{instance.pk:05d}"
        instance.save(update_fields=("request_number", "updated_at"))
    elif isinstance(instance, Expense) and not instance.expense_number:
        instance.expense_number = f"EX-{timezone.localdate().year}-{instance.pk:05d}"
        instance.save(update_fields=("expense_number", "updated_at"))


def synchronize_occupancy(unit):
    active = unit.leases.filter(status=Lease.Status.ACTIVE).exists()
    target = Unit.Status.OCCUPIED if active else Unit.Status.AVAILABLE
    if unit.status not in (Unit.Status.MAINTENANCE, Unit.Status.BLOCKED) and unit.status != target:
        unit.status = target
        unit.save(update_fields=("status", "updated_at"))
