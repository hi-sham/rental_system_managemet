from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AuditLog, Lease, Payment, Property, Receipt, RentCharge, Tenant, Unit
from .services import generate_rent_schedule, post_payment, synchronize_occupancy, void_payment


class RentWorkflowTests(TestCase):
    def setUp(self):
        self.property = Property.objects.create(
            name="Kampala Heights",
            code="KH",
            address="Ntinda, Kampala",
            district="Kampala",
            total_units=2,
        )
        self.unit = Unit.objects.create(
            property=self.property,
            unit_number="A-204",
            rent_amount=Decimal("800000"),
        )
        self.tenant = Tenant.objects.create(full_name="John Musoke", phone="+256700000000")
        self.lease = Lease.objects.create(
            lease_number="LS-2026-001",
            tenant=self.tenant,
            unit=self.unit,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 10, 31),
            rent_amount=Decimal("800000"),
            due_day=1,
            security_deposit_required=Decimal("800000"),
            security_deposit_received=Decimal("800000"),
            status=Lease.Status.ACTIVE,
        )
        generate_rent_schedule(self.lease)
        synchronize_occupancy(self.unit)

    def payment_data(self, amount, reference="MTN-123"):
        return {
            "lease": self.lease,
            "amount": Decimal(amount),
            "payment_date": date(2026, 8, 3),
            "payment_method": Payment.Method.MTN_MOMO,
            "reference": reference,
            "notes": "",
        }

    def test_schedule_is_generated_for_every_month_and_is_idempotent(self):
        self.assertEqual(self.lease.rent_charges.count(), 3)
        self.assertEqual(generate_rent_schedule(self.lease), [])
        self.assertEqual(self.lease.rent_charges.count(), 3)

    def test_partial_payment_updates_only_the_first_charge(self):
        payment = post_payment(cleaned_data=self.payment_data("500000"))
        first = self.lease.rent_charges.order_by("period").first()
        self.assertEqual(payment.allocated_amount, Decimal("500000"))
        self.assertEqual(first.balance, Decimal("300000"))
        self.assertEqual(first.status, RentCharge.Status.PARTIAL)
        self.assertTrue(Receipt.objects.filter(payment=payment, number=payment.receipt_number).exists())

    def test_advance_payment_is_allocated_across_future_periods(self):
        payment = post_payment(cleaned_data=self.payment_data("2400000"))
        self.assertEqual(payment.allocations.count(), 3)
        self.assertEqual(payment.unallocated_amount, Decimal("0"))
        self.assertFalse(self.lease.rent_charges.exclude(status=RentCharge.Status.PAID).exists())

    def test_unallocated_amount_is_retained_as_tenant_credit(self):
        payment = post_payment(cleaned_data=self.payment_data("2500000"))
        self.assertEqual(payment.allocated_amount, Decimal("2400000"))
        self.assertEqual(payment.unallocated_amount, Decimal("100000"))

    def test_void_reverses_allocations_without_deleting_records(self):
        payment = post_payment(cleaned_data=self.payment_data("800000"))
        void_payment(payment=payment, reason="Duplicate Mobile Money callback")
        payment.refresh_from_db()
        first = self.lease.rent_charges.order_by("period").first()
        first.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.VOID)
        self.assertEqual(first.status, RentCharge.Status.UNPAID)
        self.assertTrue(payment.allocations.exists())
        self.assertTrue(AuditLog.objects.filter(action="payment_voided", object_id=str(payment.pk)).exists())

    def test_financial_records_cannot_be_deleted(self):
        payment = post_payment(cleaned_data=self.payment_data("800000"))
        with self.assertRaises(ValidationError):
            payment.delete()
        with self.assertRaises(ValidationError):
            Payment.objects.filter(pk=payment.pk).delete()
        with self.assertRaises(ValidationError):
            payment.receipt.delete()

    def test_active_lease_marks_unit_occupied(self):
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, Unit.Status.OCCUPIED)


class PageSmokeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="manager", password="safe-test-password")
        self.property = Property.objects.create(
            name="Kampala Heights", code="KH", address="Ntinda, Kampala", district="Kampala", total_units=2
        )
        self.unit = Unit.objects.create(
            property=self.property, unit_number="A-204", rent_amount=Decimal("800000")
        )
        self.tenant = Tenant.objects.create(full_name="John Musoke", phone="+256700000000")
        self.lease = Lease.objects.create(
            lease_number="LS-2026-001",
            tenant=self.tenant,
            unit=self.unit,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 10, 31),
            rent_amount=Decimal("800000"),
            due_day=1,
            status=Lease.Status.ACTIVE,
        )
        generate_rent_schedule(self.lease)
        self.payment = post_payment(
            cleaned_data={
                "lease": self.lease,
                "amount": Decimal("500000"),
                "payment_date": date(2026, 8, 3),
                "payment_method": Payment.Method.MTN_MOMO,
                "reference": "MTN-123",
                "notes": "",
            }
        )

    def test_core_pages_render(self):
        urls = (
            reverse("dashboard"),
            reverse("property_list"),
            reverse("property_detail", args=[self.property.pk]),
            reverse("unit_list"),
            reverse("unit_detail", args=[self.unit.pk]),
            reverse("tenant_list"),
            reverse("tenant_detail", args=[self.tenant.pk]),
            reverse("lease_list"),
            reverse("lease_detail", args=[self.lease.pk]),
            reverse("payment_list"),
            reverse("payment_create"),
            reverse("receipt_detail", args=[self.payment.pk]),
            reverse("arrears"),
            reverse("maintenance_list"),
            reverse("expense_list"),
            reverse("reports"),
            reverse("audit_logs"),
            reverse("global_search") + "?q=John",
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_payment_post_endpoint_generates_receipt(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("payment_create"),
            {
                "lease": self.lease.pk,
                "amount": "300000",
                "payment_date": "2026-08-08",
                "payment_method": Payment.Method.AIRTEL_MONEY,
                "reference": "AIRTEL-456",
                "notes": "Balance payment",
            },
        )
        created = Payment.objects.get(reference="AIRTEL-456")
        self.assertRedirects(response, reverse("receipt_detail", args=[created.pk]))
        self.assertTrue(created.receipt_number.startswith("RC-2026-"))
