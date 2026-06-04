# from django.utils import timezone
from django.db import settings

from django.db import models
from django.conf import settings
from tenants.models import Tenancy
    
class LedgerEntry(models.Model):

    RENT = "RENT"
    PAYMENT = "PAYMENT"
    ADJUSTMENT = "ADJUSTMENT"

    ENTRY_TYPES = [
        (RENT, "Rent"),
        (PAYMENT, "Payment"),
        (ADJUSTMENT, "Adjustment"),
    ]

    tenancy = models.ForeignKey(
        Tenancy,
        on_delete=models.PROTECT,
        related_name="ledger_entries"
    )
    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPES
    )
    description = models.CharField(max_length=255)
    debit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    credit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    rent_cycle = models.ForeignKey(
        'RentCyle',
        on_delete=models.PROTECT,
        related_name='ledger_entries',
        null=True,
        blank=True,
        related_name='entries'
    )
    billing_year = models.PositiveIntegerField()
    billing_month = models.PositiveSmallIntegerField()
    entry_date = models.DateField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['entry_date', 'id']
    def __str__(self):
        return f"{self.entry_type} - {self.description} - {self.entry_date}"
 
    
class Payment(models.Model):
    PAYMENT_METHODS =[
        ('MPESA', 'M-pesa'),
        ('CASH', 'Cash'),
        ('BANK', 'Bank Transfer'),
        ('TILL', 'Till'),
        ('PAYBILL', 'Paybill'),
    ]
    tenancy = models.ForeignKey(Tenancy, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-payment_date']
    def __str__(self):
        return f"{self.tenancy} - {self.amount} on {self.payment_date} via {self.payment_method}"
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            LedgerEntry.objects.create(
                tenancy=self.tenancy,
                entry_type=LedgerEntry.PAYMENT,
                description=f"Payment - {self.method}",
                credit=self.amount,
                entry_date=self.payment_date
            )
        
class RentCyle(models.Model):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

    STATUS_CHOICES = (
        (OPEN, "Open"),
        (CLOSED, "Closed"),
    )
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='generated_rent_ cycles')    
    generated_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('month', 'year')
        ordering = ['-year', '-month']
    def __str__(self):
        return f"Rent Cycle - {self.month}/{self.year} - {self.status}"
    