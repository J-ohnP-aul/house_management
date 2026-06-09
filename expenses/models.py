from django.conf import settings
from django.db import models

from properties.models import Property


class Expense(models.Model):
    OFFICE = 'OFFICE'
    UTILITY = 'UTILITY'
    REPAIR = 'REPAIR'
    SUPPLIES = 'SUPPLIES'
    SALARY = 'SALARY'
    OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (OFFICE, 'Office'),
        (UTILITY, 'Utility'),
        (REPAIR, 'Repair'),
        (SUPPLIES, 'Supplies'),
        (SALARY, 'Salary'),
        (OTHER, 'Other'),
    ]

    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    PAID = 'PAID'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (PAID, 'Paid'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name='expenses',
        blank=True,
        null=True,
    )
    vendor = models.CharField(max_length=120, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=OTHER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        vendor = f"{self.vendor} - " if self.vendor else ''
        return f"{vendor}{self.get_category_display()} {self.amount} on {self.expense_date}"
