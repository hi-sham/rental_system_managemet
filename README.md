# RentPro

RentPro is a Django and Bootstrap property-operations MVP designed around the professional rental lifecycle:

`Property → Unit → Tenant → Lease → Rent charge → Payment allocation → Receipt → Ledger`

The implementation is Uganda-ready by default: amounts are presented in UGX, MTN Mobile Money and Airtel Money are first-class payment methods, partial and advance rent are allocated precisely, and each posted payment creates a permanent receipt.

## Included workflows

- Operational dashboard for occupancy, rent collection, arrears ageing, maintenance and activity
- Property and unit inventory with vacancy states and drill-down profiles
- Tenant profiles, lease history and computed tenant ledgers
- Lease creation with automatic monthly, quarterly or annual rent schedules
- Oldest-charge-first payment allocation, including partial and advance payments
- Printable rent receipts and unallocated tenant credit
- Audit-safe payment voids; payments, receipts, allocations, charges and expenses cannot be deleted
- Actionable arrears view with ageing buckets and direct payment/ledger actions
- Maintenance workflow, property expenses and property-level performance reporting
- Global search, responsive tables/cards and a Bootstrap offcanvas mobile sidebar
- Django Admin access for controlled back-office maintenance

The larger roadmap in the product brief—utilities and meters, inspections and deposits at move-out, document storage, owner statements, applications, notifications/reminders, communication integrations, and fine-grained role portals—should be delivered as subsequent modules on top of this core.

## Run locally

```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The operational workspace can be viewed without signing in during development, while create/void actions require authentication. Django admin remains available at `/admin/` for existing administrators. Enforce authentication on every read view before production deployment.

## Verify

```bash
./.venv/bin/python manage.py check
./.venv/bin/python manage.py test rentalapp
./.venv/bin/python manage.py makemigrations --check --dry-run
```

## Financial integrity

`Payment` and `PaymentAllocation` are separate records. A payment is allocated across specific rent charges in due-date order. Voiding a payment preserves the payment, receipt and allocations while excluding the voided amount from charge balances. Direct deletion of financial records raises a validation error.

Legal and tax rules are intentionally not hard-coded. Deposit limits, rent-increase rules, notice periods and tax calculations should be introduced as versioned configuration after review against current Ugandan legal and tax guidance.
