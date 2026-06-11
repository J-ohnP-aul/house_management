from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class RentCycle(models.Model):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STATUS_CHOICES = [
        (OPEN, "Open"),
        (CLOSED, "Closed"),
    ]

    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="generated_rent_cycles"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("month", "year")
        ordering = ["-year", "-month"]
        verbose_name = "Rent Cycle"
        verbose_name_plural = "Rent Cycles"

    def __str__(self):
        return f"{self.get_month_display()} {self.year} - {self.get_status_display()}"

    def get_month_display(self):
        return timezone.datetime(self.year, self.month, 1).strftime("%B")

    def is_already_generated(self):
        """Check if any ledger entry exists for this cycle."""
        return self.ledger_entries.exists()

    def close(self):
        """Mark cycle as closed (no further rent entries can be added)."""
        self.status = self.CLOSED
        self.save(update_fields=["status"])


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
        "tenants.Tenancy",  # string reference to avoid circular import
        on_delete=models.PROTECT,
        related_name="ledger_entries"
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    description = models.CharField(max_length=255)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Link to rent cycle – required for RENT entries, optional for others
    rent_cycle = models.ForeignKey(
        RentCycle,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        null=True,
        blank=True
    )
    
    billing_year = models.PositiveIntegerField()
    billing_month = models.PositiveSmallIntegerField()
    
    entry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["entry_date", "id"]
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"

    def __str__(self):
        return f"{self.entry_type} - {self.description} - {self.entry_date}"

    def clean(self):
        # No both debit and credit
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("An entry cannot have both debit and credit.")
        # Must have at least one
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("An entry must have either debit or credit.")
        # Rent entries must be linked to a rent cycle
        if self.entry_type == self.RENT and not self.rent_cycle:
            raise ValidationError("Rent entries must be linked to a RentCycle.")
        # For non-rent entries, rent_cycle is optional but if provided must exist
        if self.rent_cycle and self.rent_cycle.status == RentCycle.CLOSED and self.entry_type == self.RENT:
            raise ValidationError("Cannot add rent entry to a closed rent cycle.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHODS = [
        ("MPESA", "M-Pesa"),
        ("CASH", "Cash"),
        ("BANK", "Bank Transfer"),
        ("TILL", "Till"),
        ("PAYBILL", "Paybill"),
    ]

    tenancy = models.ForeignKey(
        "tenants.Tenancy",
        on_delete=models.PROTECT,
        related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_payments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: Link to a specific rent cycle if payment is intended for a particular month
    rent_cycle = models.ForeignKey(
        RentCycle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments"
    )

    class Meta:
        ordering = ["-payment_date"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.tenancy} - {self.amount} on {self.payment_date}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Create corresponding ledger entry automatically
            LedgerEntry.objects.create(
                tenancy=self.tenancy,
                entry_type=LedgerEntry.PAYMENT,
                description=f"Payment via {self.get_payment_method_display()} (Ref: {self.reference or 'N/A'})",
                credit=self.amount,
                entry_date=self.payment_date,
                billing_year=self.payment_date.year,
                billing_month=self.payment_date.month,
                rent_cycle=self.rent_cycle,  # can be None
            )