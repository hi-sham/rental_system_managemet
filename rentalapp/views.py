from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q, Sum
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    ExpenseForm,
    LeaseForm,
    MaintenanceRequestForm,
    PaymentForm,
    PropertyForm,
    TenantForm,
    UnitForm,
    VoidPaymentForm,
)
from .models import (
    AuditLog,
    Expense,
    Lease,
    MaintenanceRequest,
    Notification,
    Payment,
    Property,
    RentCharge,
    Tenant,
    Unit,
)
from .services import assign_reference, audit, generate_rent_schedule, post_payment, synchronize_occupancy, void_payment


def _actor(request):
    return request.user if request.user.is_authenticated else None


def post_login_required(view):
    """Keep the development preview readable, but never allow anonymous writes."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method == "POST" and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return view(request, *args, **kwargs)

    return wrapped


def _form_errors(request, form):
    messages.error(request, "Please correct the highlighted fields and try again.")
    return form


def dashboard(request):
    today = timezone.localdate()
    period = today.replace(day=1)
    properties = list(Property.objects.filter(status="active").prefetch_related("units"))
    units = Unit.objects.select_related("property")
    total_units = units.count()
    occupied_units = units.filter(status=Unit.Status.OCCUPIED).count()
    vacant_units = units.filter(status=Unit.Status.AVAILABLE).count()
    maintenance_units = units.filter(status=Unit.Status.MAINTENANCE).count()
    occupancy_rate = round((occupied_units / total_units * 100), 1) if total_units else 0

    current_charges = list(
        RentCharge.objects.filter(period=period).select_related("lease__tenant", "lease__unit__property")
    )
    expected_rent = sum((item.amount for item in current_charges), Decimal("0"))
    collected_rent = sum((item.allocated_amount for item in current_charges), Decimal("0"))
    collection_rate = round((collected_rent / expected_rent * 100), 1) if expected_rent else 0

    overdue_charges = [
        charge
        for charge in RentCharge.objects.filter(due_date__lte=today)
        .exclude(status__in=(RentCharge.Status.PAID, RentCharge.Status.VOID))
        .select_related("lease__tenant", "lease__unit__property")
        if charge.balance > 0
    ]
    outstanding = sum((charge.balance for charge in overdue_charges), Decimal("0"))
    affected_tenants = len({charge.lease.tenant_id for charge in overdue_charges})
    arrears_buckets = _arrears_buckets(overdue_charges, today)

    maintenance_counts = {
        key: MaintenanceRequest.objects.filter(status=key).count()
        for key in (
            MaintenanceRequest.Status.NEW,
            MaintenanceRequest.Status.ASSIGNED,
            MaintenanceRequest.Status.IN_PROGRESS,
            MaintenanceRequest.Status.AWAITING_PARTS,
        )
    }
    maintenance_counts["completed"] = MaintenanceRequest.objects.filter(
        status__in=(MaintenanceRequest.Status.COMPLETED, MaintenanceRequest.Status.VERIFIED, MaintenanceRequest.Status.CLOSED),
        updated_at__year=today.year,
        updated_at__month=today.month,
    ).count()

    recent_activity = []
    for payment in Payment.objects.select_related("lease__tenant", "lease__unit").all()[:6]:
        recent_activity.append(
            {
                "time": payment.created_at,
                "icon": "ph-wallet",
                "tone": "success" if payment.status == Payment.Status.POSTED else "danger",
                "title": "Rent payment received" if payment.status == Payment.Status.POSTED else "Payment voided",
                "detail": f"{payment.lease.unit.unit_number if payment.lease else 'Unassigned'} · UGX {payment.amount:,.0f}",
                "url": reverse("receipt_detail", args=[payment.pk]),
            }
        )
    for item in MaintenanceRequest.objects.select_related("unit").all()[:6]:
        recent_activity.append(
            {
                "time": item.created_at,
                "icon": "ph-wrench",
                "tone": "warning",
                "title": "Maintenance request created",
                "detail": f"{item.unit.unit_number} · {item.title}",
                "url": reverse("maintenance_list"),
            }
        )
    recent_activity = sorted(recent_activity, key=lambda item: item["time"], reverse=True)[:7]

    expiring_leases = Lease.objects.filter(
        status__in=(Lease.Status.ACTIVE, Lease.Status.EXPIRING),
        end_date__range=(today, today + timedelta(days=45)),
    ).select_related("tenant", "unit__property")[:5]

    months = []
    cursor = period
    for _ in range(6):
        months.append(cursor)
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    months.reverse()
    month_totals = defaultdict(Decimal)
    for row in (
        Payment.objects.filter(status=Payment.Status.POSTED, payment_date__gte=months[0])
        .values("payment_date__year", "payment_date__month")
        .annotate(total=Sum("amount"))
    ):
        month_totals[(row["payment_date__year"], row["payment_date__month"])] = row["total"]
    collection_trend = [
        {"label": month.strftime("%b"), "amount": month_totals[(month.year, month.month)]} for month in months
    ]
    max_collection = max((item["amount"] for item in collection_trend), default=Decimal("0"))
    for item in collection_trend:
        item["height"] = round(item["amount"] / max_collection * 100) if max_collection else 4

    context = {
        "today": today,
        "properties_count": len(properties),
        "total_units": total_units,
        "occupied_units": occupied_units,
        "vacant_units": vacant_units,
        "maintenance_units": maintenance_units,
        "occupancy_rate": occupancy_rate,
        "expected_rent": expected_rent,
        "collected_rent": collected_rent,
        "collection_rate": collection_rate,
        "outstanding": outstanding,
        "affected_tenants": affected_tenants,
        "arrears_buckets": arrears_buckets,
        "maintenance_counts": maintenance_counts,
        "recent_activity": recent_activity,
        "expiring_leases": expiring_leases,
        "collection_trend": collection_trend,
    }
    return render(request, "dashboard.html", context)


@post_login_required
def property_list(request):
    form = PropertyForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            audit(actor=_actor(request), action="property_created", instance=item, request=request)
            messages.success(request, f"{item.name} was added successfully.")
            return redirect(item)
        _form_errors(request, form)
    queryset = Property.objects.select_related("owner").prefetch_related("units")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(address__icontains=query) | Q(district__icontains=query))
    if status:
        queryset = queryset.filter(status=status)
    properties = list(queryset)
    for item in properties:
        item.display_units = len(item.units.all())
        item.display_occupied = sum(unit.status == Unit.Status.OCCUPIED for unit in item.units.all())
        item.display_vacant = sum(unit.status == Unit.Status.AVAILABLE for unit in item.units.all())
        item.display_rent = sum((unit.rent_amount for unit in item.units.all()), Decimal("0"))
    return render(request, "properties/list.html", {"properties": properties, "form": form, "query": query, "status": status})


def property_detail(request, pk):
    item = get_object_or_404(Property.objects.select_related("owner"), pk=pk)
    units = list(item.units.select_related("building").all())
    active_leases = Lease.objects.filter(unit__property=item, status=Lease.Status.ACTIVE).select_related("tenant", "unit")
    charges = list(RentCharge.objects.filter(lease__unit__property=item).select_related("lease"))
    collected = Payment.objects.filter(
        lease__unit__property=item, status=Payment.Status.POSTED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    outstanding = sum((charge.balance for charge in charges if charge.due_date <= timezone.localdate()), Decimal("0"))
    context = {
        "property": item,
        "units": units,
        "active_leases": active_leases,
        "occupied": sum(unit.status == Unit.Status.OCCUPIED for unit in units),
        "vacant": sum(unit.status == Unit.Status.AVAILABLE for unit in units),
        "expected": sum((unit.rent_amount for unit in units), Decimal("0")),
        "collected": collected,
        "outstanding": outstanding,
        "maintenance": item.units.values_list("maintenance_requests", flat=True).count(),
    }
    return render(request, "properties/detail.html", context)


@post_login_required
def unit_list(request):
    form = UnitForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            audit(actor=_actor(request), action="unit_created", instance=item, request=request)
            messages.success(request, f"Unit {item.unit_number} was added.")
            return redirect("unit_detail", pk=item.pk)
        _form_errors(request, form)
    queryset = Unit.objects.select_related("property", "building")
    property_id = request.GET.get("property", "")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if property_id:
        queryset = queryset.filter(property_id=property_id)
    if status:
        queryset = queryset.filter(status=status)
    if query:
        queryset = queryset.filter(Q(unit_number__icontains=query) | Q(property__name__icontains=query))
    return render(
        request,
        "units/list.html",
        {
            "units": queryset,
            "form": form,
            "properties": Property.objects.filter(status="active"),
            "selected_property": property_id,
            "selected_status": status,
            "query": query,
            "status_choices": Unit.Status.choices,
        },
    )


def unit_detail(request, pk):
    unit = get_object_or_404(Unit.objects.select_related("property", "building"), pk=pk)
    leases = unit.leases.select_related("tenant").all()
    current_lease = leases.filter(status=Lease.Status.ACTIVE).first()
    return render(
        request,
        "units/detail.html",
        {
            "unit": unit,
            "leases": leases,
            "current_lease": current_lease,
            "maintenance_requests": unit.maintenance_requests.select_related("tenant")[:8],
        },
    )


@post_login_required
def tenant_list(request):
    form = TenantForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            audit(actor=_actor(request), action="tenant_created", instance=item, request=request)
            messages.success(request, f"{item} was registered.")
            return redirect(item)
        _form_errors(request, form)
    queryset = Tenant.objects.prefetch_related("leases__unit__property")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query:
        queryset = queryset.filter(
            Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(national_id__icontains=query)
        )
    if status:
        queryset = queryset.filter(status=status)
    tenants = list(queryset)
    for tenant in tenants:
        tenant.display_lease = next((lease for lease in tenant.leases.all() if lease.status == Lease.Status.ACTIVE), None)
        tenant.display_balance = sum((lease.balance for lease in tenant.leases.all()), Decimal("0"))
    return render(
        request,
        "tenants/list.html",
        {"tenants": tenants, "form": form, "query": query, "selected_status": status, "status_choices": Tenant.Status.choices},
    )


def _tenant_ledger(tenant):
    events = []
    leases = tenant.leases.prefetch_related("rent_charges", "payments")
    for lease in leases:
        for charge in lease.rent_charges.exclude(status=RentCharge.Status.VOID):
            events.append(
                {
                    "date": charge.due_date,
                    "sort": 0,
                    "description": charge.description,
                    "reference": lease.lease_number,
                    "debit": charge.amount,
                    "credit": None,
                    "url": reverse("lease_detail", args=[lease.pk]),
                }
            )
        for payment in lease.payments.filter(status=Payment.Status.POSTED):
            events.append(
                {
                    "date": payment.payment_date,
                    "sort": 1,
                    "description": payment.get_payment_method_display(),
                    "reference": payment.receipt_number,
                    "debit": None,
                    "credit": payment.amount,
                    "url": reverse("receipt_detail", args=[payment.pk]),
                }
            )
    events.sort(key=lambda event: (event["date"], event["sort"], event["reference"] or ""))
    balance = Decimal("0")
    for event in events:
        balance += event["debit"] or Decimal("0")
        balance -= event["credit"] or Decimal("0")
        event["balance"] = balance
    return list(reversed(events)), balance


def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    ledger, balance = _tenant_ledger(tenant)
    active_lease = tenant.active_lease
    return render(
        request,
        "tenants/detail.html",
        {
            "tenant": tenant,
            "active_lease": active_lease,
            "leases": tenant.leases.select_related("unit__property"),
            "ledger": ledger,
            "balance": max(balance, Decimal("0")),
            "credit": abs(min(balance, Decimal("0"))),
        },
    )


@post_login_required
def lease_list(request):
    form = LeaseForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            lease = form.save()
            try:
                generated = generate_rent_schedule(lease)
            except Exception:
                lease.delete()
                raise
            synchronize_occupancy(lease.unit)
            audit(
                actor=_actor(request),
                action="lease_created",
                instance=lease,
                new_value={"charges_generated": len(generated)},
                request=request,
            )
            messages.success(request, f"{lease.lease_number} was created with {len(generated)} rent charges.")
            return redirect("lease_detail", pk=lease.pk)
        _form_errors(request, form)
    queryset = Lease.objects.select_related("tenant", "unit__property").prefetch_related("rent_charges")
    status = request.GET.get("status", "")
    if status:
        queryset = queryset.filter(status=status)
    return render(
        request,
        "leases/list.html",
        {"leases": queryset, "form": form, "selected_status": status, "status_choices": Lease.Status.choices},
    )


def lease_detail(request, pk):
    lease = get_object_or_404(Lease.objects.select_related("tenant", "unit__property"), pk=pk)
    charges = list(lease.rent_charges.prefetch_related("allocations__payment"))
    return render(
        request,
        "leases/detail.html",
        {
            "lease": lease,
            "charges": charges,
            "payments": lease.payments.prefetch_related("allocations").all(),
            "total_charged": sum((item.amount for item in charges), Decimal("0")),
            "total_paid": sum((item.allocated_amount for item in charges), Decimal("0")),
        },
    )


def payment_list(request):
    payments = Payment.objects.select_related("lease__tenant", "lease__unit__property", "received_by").prefetch_related("allocations")
    method = request.GET.get("method", "")
    query = request.GET.get("q", "").strip()
    if method:
        payments = payments.filter(payment_method=method)
    if query:
        payments = payments.filter(
            Q(reference__icontains=query)
            | Q(receipt_number__icontains=query)
            | Q(lease__tenant__full_name__icontains=query)
            | Q(lease__unit__unit_number__icontains=query)
        )
    return render(
        request,
        "payments/list.html",
        {"payments": payments, "method_choices": Payment.Method.choices, "selected_method": method, "query": query},
    )


@post_login_required
def payment_create(request):
    initial = {}
    if request.GET.get("lease"):
        initial["lease"] = request.GET["lease"]
    form = PaymentForm(request.POST or None, initial=initial)
    if request.method == "POST":
        if form.is_valid():
            payment = post_payment(cleaned_data=form.cleaned_data, actor=_actor(request), request=request)
            if payment.unallocated_amount:
                messages.warning(
                    request,
                    f"Payment posted. UGX {payment.unallocated_amount:,.0f} remains as unallocated tenant credit.",
                )
            else:
                messages.success(request, f"Payment posted and receipt {payment.receipt_number} generated.")
            return redirect("receipt_detail", pk=payment.pk)
        _form_errors(request, form)
    return render(request, "payments/form.html", {"form": form})


def receipt_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related("lease__tenant", "lease__unit__property", "received_by").prefetch_related(
            "allocations__charge"
        ),
        pk=pk,
    )
    previous_balance = Decimal("0")
    if payment.lease:
        previous_balance = sum(
            (
                charge.amount
                - (
                    charge.allocations.filter(
                        payment__status=Payment.Status.POSTED, payment__payment_date__lt=payment.payment_date
                    ).aggregate(total=Sum("amount"))["total"]
                    or Decimal("0")
                )
                for charge in payment.lease.rent_charges.filter(due_date__lte=payment.payment_date)
            ),
            Decimal("0"),
        )
    return render(request, "payments/receipt.html", {"payment": payment, "previous_balance": max(previous_balance, Decimal("0"))})


@post_login_required
def payment_void(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    form = VoidPaymentForm(request.POST)
    if form.is_valid():
        void_payment(payment=payment, reason=form.cleaned_data["reason"], actor=_actor(request), request=request)
        messages.success(request, f"{payment.receipt_number} was voided. The original record has been retained.")
    else:
        messages.error(request, "A clear void reason of at least five characters is required.")
    return redirect("receipt_detail", pk=payment.pk)


def _arrears_buckets(charges, today):
    buckets = {
        "current": {"label": "Current", "amount": Decimal("0")},
        "1_30": {"label": "1–30 days", "amount": Decimal("0")},
        "31_60": {"label": "31–60 days", "amount": Decimal("0")},
        "61_90": {"label": "61–90 days", "amount": Decimal("0")},
        "90_plus": {"label": "90+ days", "amount": Decimal("0")},
    }
    for charge in charges:
        days = max((today - charge.due_date).days, 0)
        key = "current" if days == 0 else "1_30" if days <= 30 else "31_60" if days <= 60 else "61_90" if days <= 90 else "90_plus"
        buckets[key]["amount"] += charge.balance
    total = sum((item["amount"] for item in buckets.values()), Decimal("0"))
    for item in buckets.values():
        item["percentage"] = round(item["amount"] / total * 100) if total else 0
    return buckets


def arrears(request):
    today = timezone.localdate()
    charges = [
        charge
        for charge in RentCharge.objects.filter(due_date__lte=today)
        .exclude(status__in=(RentCharge.Status.PAID, RentCharge.Status.VOID))
        .select_related("lease__tenant", "lease__unit__property")
        if charge.balance > 0
    ]
    tenants = {}
    for charge in charges:
        key = charge.lease_id
        row = tenants.setdefault(
            key,
            {
                "lease": charge.lease,
                "due": Decimal("0"),
                "paid": Decimal("0"),
                "balance": Decimal("0"),
                "oldest_due": charge.due_date,
            },
        )
        row["due"] += charge.amount
        row["paid"] += charge.allocated_amount
        row["balance"] += charge.balance
        row["oldest_due"] = min(row["oldest_due"], charge.due_date)
    rows = sorted(tenants.values(), key=lambda row: (row["oldest_due"], -row["balance"]))
    total = sum((row["balance"] for row in rows), Decimal("0"))
    return render(
        request,
        "payments/arrears.html",
        {"rows": rows, "total": total, "buckets": _arrears_buckets(charges, today), "today": today},
    )


@post_login_required
def maintenance_list(request):
    form = MaintenanceRequestForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            assign_reference(item)
            audit(actor=_actor(request), action="maintenance_created", instance=item, request=request)
            messages.success(request, f"Request {item.request_number} was created.")
            return redirect("maintenance_list")
        _form_errors(request, form)
    queryset = MaintenanceRequest.objects.select_related("unit__property", "tenant")
    status = request.GET.get("status", "")
    if status:
        queryset = queryset.filter(status=status)
    return render(
        request,
        "maintenance/list.html",
        {"requests": queryset, "form": form, "selected_status": status, "status_choices": MaintenanceRequest.Status.choices},
    )


@post_login_required
def expense_list(request):
    form = ExpenseForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            item = form.save(commit=False)
            item.approved_by = _actor(request)
            item.save()
            assign_reference(item)
            audit(actor=_actor(request), action="expense_recorded", instance=item, request=request)
            messages.success(request, f"Expense {item.expense_number} was recorded.")
            return redirect("expense_list")
        _form_errors(request, form)
    expenses = Expense.objects.select_related("property", "approved_by")
    total = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return render(request, "expenses/list.html", {"expenses": expenses, "form": form, "total": total})


def reports(request):
    rows = []
    for property_item in Property.objects.prefetch_related("units", "expenses"):
        income = Payment.objects.filter(
            lease__unit__property=property_item, status=Payment.Status.POSTED
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        expenses_total = property_item.expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        units = list(property_item.units.all())
        rows.append(
            {
                "property": property_item,
                "units": len(units),
                "occupied": sum(unit.status == Unit.Status.OCCUPIED for unit in units),
                "income": income,
                "expenses": expenses_total,
                "net": income - expenses_total,
            }
        )
    return render(request, "reports/index.html", {"rows": rows})


def audit_log_list(request):
    return render(request, "audit/list.html", {"logs": AuditLog.objects.select_related("actor")[:200]})


def global_search(request):
    query = request.GET.get("q", "").strip()
    context = {"query": query, "properties": [], "units": [], "tenants": [], "leases": [], "payments": []}
    if query:
        context.update(
            {
                "properties": Property.objects.filter(Q(name__icontains=query) | Q(address__icontains=query))[:8],
                "units": Unit.objects.filter(Q(unit_number__icontains=query) | Q(property__name__icontains=query)).select_related("property")[:8],
                "tenants": Tenant.objects.filter(Q(full_name__icontains=query) | Q(phone__icontains=query))[:8],
                "leases": Lease.objects.filter(Q(lease_number__icontains=query) | Q(tenant__full_name__icontains=query)).select_related("tenant", "unit")[:8],
                "payments": Payment.objects.filter(Q(receipt_number__icontains=query) | Q(reference__icontains=query)).select_related("lease__tenant")[:8],
            }
        )
    return render(request, "search/results.html", context)


# Compatibility names retained for old bookmarks and templates.
login_view = dashboard
add_property_view = property_list
add_Unit_view = unit_list
add_Tenant_view = tenant_list
add_Payment_view = payment_list
add_MaintenanceRequest_view = maintenance_list
