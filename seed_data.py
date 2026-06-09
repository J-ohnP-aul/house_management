"""
Django seed script for House Rental Management System.
Run this script from the project root with:

    python manage.py shell < seed_data.py

This script assumes the Django environment is already configured by manage.py.
"""

import os
import random
from datetime import date, timedelta
from decimal import Decimal

import django
from django.db import transaction
from faker import Faker

# Initialize Faker with Kenyan locale where available.
try:
    fake = Faker('en_KE')
except Exception:
    fake = Faker('en_US')

# Use a deterministic random seed if desired. Comment out for fully random data.
random.seed()

# Helper functions for realistic Kenyan data generation.

def generate_kenyan_phone(existing_numbers):
    """Generate a unique Kenyan mobile number starting with 07."""
    while True:
        phone_no = f"07{random.randint(10_000_000, 99_999_999)}"
        if phone_no not in existing_numbers:
            existing_numbers.add(phone_no)
            return phone_no


def generate_unique_id(existing_ids):
    """Generate a unique realistic Kenyan ID number."""
    while True:
        id_no = str(random.randint(10_000_000, 99_999_999))
        if id_no not in existing_ids:
            existing_ids.add(id_no)
            return id_no


def random_move_in_date(start_date, end_date):
    """Return a random date between two dates."""
    delta = (end_date - start_date).days
    if delta < 1:
        return start_date
    return start_date + timedelta(days=random.randint(0, delta))


def random_moved_out_date(move_in_date, today_date):
    """Return a valid move-out date after move-in but no later than today."""
    earliest = move_in_date + timedelta(days=1)
    if earliest >= today_date:
        return today_date
    return random_move_in_date(earliest, today_date)


def build_tenant_record(existing_phones, existing_ids):
    """Create a realistic Tenant instance without saving."""
    from tenants.models import Tenant

    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"
    phone_no = generate_kenyan_phone(existing_phones)
    id_no = generate_unique_id(existing_ids)
    emergency_no = generate_kenyan_phone(existing_phones)
    return Tenant(
        full_name=full_name,
        phone_no=phone_no,
        id_no=id_no,
        emergency_no=emergency_no,
        active=True,
    )


def build_reservation_record(unit, existing_phones, existing_ids):
    """Create a realistic Reservation instance for a vacant unit."""
    from tenants.models import Reservation

    full_name = fake.name()
    phone_no = generate_kenyan_phone(existing_phones)
    id_no = generate_unique_id(existing_ids)
    expected_movein_date = fake.date_between_dates(
        date_start=date.today() + timedelta(days=7),
        date_end=date.today() + timedelta(days=90),
    )
    status = random.choice([Reservation.PENDING, Reservation.CANCELLED])
    return Reservation(
        unit=unit,
        full_name=full_name,
        phone_no=phone_no,
        id_no=id_no,
        deposit_amount=Decimal(f"{random.uniform(5_000, 20_000):.2f}"),
        status=status,
        expected_movein_date=expected_movein_date,
    )


def get_next_unit_number(parent_property):
    """Return the next unique unit number for a property."""
    existing_numbers = {unit.unit_number for unit in parent_property.units.all()}
    index = 1
    while True:
        candidate = f"U{index}"
        if candidate not in existing_numbers:
            return candidate
        index += 1


def main():
    """Seed the database with tenants, tenancies, and reservations."""
    from properties.models import Property, Unit
    from tenants.models import Tenant, Tenancy, Reservation

    today = date.today()
    three_years_ago = today - timedelta(days=3 * 365)

    # Query existing property and unit records.
    properties = list(Property.objects.all())
    units = list(Unit.objects.all())

    if len(properties) < 2:
        raise RuntimeError('Seed requires at least 2 Property records in the database.')

    # The total units needed to support required seed-data counts.
    required_units = 33 + 14 + 10
    if len(units) < required_units:
        units_to_create = required_units - len(units)
        print(f'Adding {units_to_create} units to meet seed requirements.')
        for i in range(units_to_create):
            parent_property = properties[i % len(properties)]
            unit_number = get_next_unit_number(parent_property)
            unit = Unit(
                parent_property=parent_property,
                unit_number=unit_number,
                monthly_rent=Decimal(f"{random.uniform(8_000, 35_000):.2f}"),
                status=Unit.VACANT,
                description='Seed data unit',
                active=True,
            )
            unit.save()
            units.append(unit)

    # Track unique phone and ID values across tenants and reservations.
    existing_phone_numbers = set(Tenant.objects.values_list('phone_no', flat=True))
    existing_id_numbers = set(Tenant.objects.values_list('id_no', flat=True))

    with transaction.atomic():
        # Create 60 tenants.
        tenants = []
        for _ in range(60):
            tenant = build_tenant_record(existing_phone_numbers, existing_id_numbers)
            tenant.save()
            tenants.append(tenant)

        # Use 47 tenants for tenancy records, leaving some tenants without tenancy.
        tenancy_tenants = random.sample(tenants, 47)
        active_tenants = set(random.sample(tenancy_tenants, 33))
        moved_out_tenants = [t for t in tenancy_tenants if t not in active_tenants]

        # Select units eligible for active tenancies.
        active_candidates = [u for u in units if u.status != Unit.OCCUPIED]
        if len(active_candidates) < 33:
            raise RuntimeError('Not enough non-occupied units available for 33 active tenancies.')
        active_units = random.sample(active_candidates, 33)

        # Reserve a separate set of units for moved-out tenancies.
        moved_out_candidates = [u for u in units if u not in active_units]
        if len(moved_out_candidates) < 14:
            moved_out_units = [random.choice(units) for _ in range(14)]
        else:
            moved_out_units = random.sample(moved_out_candidates, 14)

        # Create moved-out tenancy records first.
        moved_out_tenancies = []
        for tenant, unit in zip(moved_out_tenants, moved_out_units):
            move_in_date = random_move_in_date(three_years_ago, today - timedelta(days=30))
            move_out_date = random_moved_out_date(move_in_date, today)
            tenancy = Tenancy(
                tenant=tenant,
                unit=unit,
                status=Tenancy.MOVED_OUT,
                move_in_date=move_in_date,
                move_out_date=move_out_date,
            )
            tenancy.save()
            moved_out_tenancies.append(tenancy)

        # Create active tenancy records.
        active_tenancies = []
        for tenant, unit in zip(active_tenants, active_units):
            move_in_date = random_move_in_date(three_years_ago, today)
            tenancy = Tenancy(
                tenant=tenant,
                unit=unit,
                status=Tenancy.ACTIVE,
                move_in_date=move_in_date,
                move_out_date=None,
            )
            tenancy.save()
            active_tenancies.append(tenancy)

        # Create 10 reservations on currently vacant units with no active tenancy.
        vacant_units = list(
            Unit.objects.filter(status=Unit.VACANT)
            .exclude(tenancies_by_unit__status=Tenancy.ACTIVE)
            .distinct()
        )
        if len(vacant_units) < 10:
            raise RuntimeError('Not enough vacant units available for 10 reservations.')

        reservation_units = random.sample(vacant_units, 10)
        reservations = []
        for unit in reservation_units:
            reservation = build_reservation_record(unit, existing_phone_numbers, existing_id_numbers)
            reservation.save()
            reservations.append(reservation)

    # Final summary after successful transaction.
    print('\nSeed script completed successfully:')
    print(f'Properties: {len(properties)}')
    print(f'Units: {len(units)}')
    print('Tenants Created: 60')
    print(f'Active Tenancies: {len(active_tenancies)}')
    print(f'Moved Out Tenancies: {len(moved_out_tenancies)}')
    print(f'Reservations Created: {len(reservations)}')


def setup_django():
    """Initialize Django when running the script directly."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PMS.settings')
    django.setup()


if __name__ == '__main__':
    setup_django()
    main()
