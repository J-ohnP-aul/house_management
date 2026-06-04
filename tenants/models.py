from django.db import models
from django.core.exceptions import ValidationError
from properties.models import Unit

class Tenant(models.Model):
    full_name = models.CharField(max_length=50)
    phone_no = models.CharField(max_length=15, blank=False, unique=True)
    id_no = models.CharField(max_length=20, unique=True)
    emergency_no = models.CharField(max_length=15, null=True, blank=True)
    active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        return self.tenancies.filter(status=Tenancy.ACTIVE).exists()

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name
    
    @property
    def current_tenant(self):
        tenancy = self.tenancies_by_unit.filter(
            status='ACTIVE'
        ).first()

        return tenancy.tenant if tenancy else None
    

class Tenancy(models.Model):
    ACTIVE = 'ACTIVE'
    MOVED_OUT = 'MOVED_OUT'
    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (MOVED_OUT, 'Moved Out'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE, db_index=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='tenancies_by_unit')
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='tenancies')
    move_in_date = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-move_in_date']

    def __str__(self):
        return f"{self.tenant} - {self.unit}"

    def clean(self):
        super().clean()
        if self.move_out_date and self.move_out_date < self.move_in_date:
            raise ValidationError("Move out date cannot be before move in date.")
            
        if self.status == self.ACTIVE:
            existing = Tenancy.objects.filter(
                unit=self.unit,
                status=self.ACTIVE
            )
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("This unit already has an active tenancy.")
                
    def save(self, *args, **kwargs):
        # 1. Run all validations first
        self.full_clean()
        
        # 2. Update the related unit status *before* committing the save
        if self.status == self.ACTIVE:
            self.unit.status = Unit.OCCUPIED
        else:
            self.unit.status = Unit.VACANT
        self.unit.save(update_fields=['status'])

        # 3. Finalize saving the tenancy record
        super().save(*args, **kwargs)


class Reservation(models.Model):
    PENDING = 'PENDING'
    CONVERTED = 'CONVERTED'
    CANCELLED = 'CANCELLED'
    STATUS_CHOICE = (
        (PENDING, 'Pending'),
        (CONVERTED, 'Converted'),
        (CANCELLED, 'Cancelled'),
    )
    
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='reservations')
    full_name = models.CharField(max_length=50)
    phone_no = models.CharField(max_length=15, null=True, blank=True)
    id_no = models.CharField(max_length=20, null=True, blank=True)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICE, default=PENDING)
    expected_movein_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    tenancy = models.OneToOneField(
        Tenancy,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='reservation'
    )
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.unit}"
    
    def clean(self):
        super().clean()
        existing = Reservation.objects.filter(
            unit=self.unit,
            status=self.PENDING
        )
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError("This unit already has a pending reservation.")
            
        active_tenancy = Tenancy.objects.filter(
            unit=self.unit,
            status=Tenancy.ACTIVE
        )
        if active_tenancy.exists():
            raise ValidationError("Cannot reserve an occupied unit.")
            
    def save(self, *args, **kwargs):
        # 1. Run validations
        self.full_clean()
        
        # 2. Update unit state *before* committing save
        if self.status == self.PENDING:
            self.unit.status = Unit.RESERVED
        elif self.status == self.CANCELLED:
            self.unit.status = Unit.VACANT
        self.unit.save(update_fields=['status'])
        
        # 3. Save reservation
        super().save(*args, **kwargs)