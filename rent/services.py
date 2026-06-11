# rent/services.py
from datetime import date
from calendar import monthrange
from rent.models import RentCycle, LedgerEntry
from tenants.models import Tenancy

def generate_rent_for_cycle(cycle: RentCycle, user):
    """
    Creates LedgerEntry (debit) for every active tenancy.
    Returns the number of entries created.
    """
    if cycle.is_already_generated():
        raise ValueError(f"Rent already generated for {cycle.month}/{cycle.year}")

    active_tenancies = Tenancy.objects.filter(status=Tenancy.ACTIVE).select_related("unit")
    entries_created = 0

    for tenancy in active_tenancies:
        due_day = tenancy.move_in_date.day
        # Clamp due day to last valid day of the month (e.g., 31 → 28/29 in Feb)
        _, last_day = monthrange(cycle.year, cycle.month)
        actual_day = min(due_day, last_day)
        entry_date = date(cycle.year, cycle.month, actual_day)

        LedgerEntry.objects.create(
            tenancy=tenancy,
            rent_cycle=cycle,
            entry_type=LedgerEntry.RENT,
            description=f"Rent for {cycle.get_month_display()} {cycle.year}",
            debit=tenancy.monthly_rent,
            entry_date=entry_date,
            billing_year=cycle.year,
            billing_month=cycle.month,
        )
        entries_created += 1

    cycle.close()
    return entries_created