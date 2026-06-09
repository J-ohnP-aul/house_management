from decimal import Decimal
import random
from django.utils import timezone
from maintanance.models import Maintenance
from properties.models import Unit

units = list(Unit.objects.filter(active=True))
if not units:
    raise RuntimeError('No active units found in the database.')

sample_units = random.sample(units, min(12, len(units))) if len(units) >= 12 else [random.choice(units) for _ in range(12)]

titles = [
    'Leaky faucet',
    'Broken light fixture',
    'Cracked window',
    'Paint peeling',
    'Clogged drain',
    'Heater not working',
    'Door lock issue',
    'Roof leak',
    'Electrical outage',
    'Air conditioning issue',
    'Cabinet hinge broken',
    'Smoke detector fault',
]

descriptions = [
    'Requires immediate attention.',
    'Needs a qualified technician.',
    'Tenant reported worsening condition.',
    'Please inspect and repair.',
    'Leak is causing water damage.',
    'No heat in the unit.',
    'Faulty electrical outlet.',
    'Window does not close properly.',
    'Door does not lock securely.',
    'Ventilation issue noticed by tenant.',
    'Ceiling stain spreading.',
    'Appliance making noise.',
]

categories = [choice[0] for choice in Maintenance.MAINTENANCE_CATEGORIES]
priorities = [choice[0] for choice in Maintenance.PRIORITY_CHOICES]
status_weights = {'PENDING': 5, 'INPROGRESS': 3, 'COMPLETE': 2}
status_choices = list(status_weights.keys())

records = []
for index, unit in enumerate(sample_units):
    category = random.choice(categories)
    priority = random.choice(priorities)
    status = random.choices(status_choices, weights=[status_weights[s] for s in status_choices], k=1)[0]
    title = titles[index % len(titles)]
    description = descriptions[index % len(descriptions)]
    cost = Decimal(f"{random.uniform(100.0, 3500.0):.2f}")

    maintenance = Maintenance(
        unit=unit,
        title=title,
        description=description,
        category=category,
        priority=priority,
        status=status,
        cost=cost,
    )

    if status == Maintenance.COMPLETE:
        maintenance.completion_date = timezone.now() - timezone.timedelta(days=random.randint(1, 30))

    records.append(maintenance)

Maintenance.objects.bulk_create(records)
print(f'Created {len(records)} maintenance requests.')
