from django.db import models


class Property(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to='properties/',
        blank=True,
        null=True
    )
    
    description = models.TextField(
        blank=True,
        null=True
    )

    water_included = models.BooleanField(
        default=True
    )

    electricity_included = models.BooleanField(
        default=True
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return self.name


class Unit(models.Model):

    VACANT = 'VACANT'
    RESERVED = 'RESERVED'
    OCCUPIED = 'OCCUPIED'

    STATUS_CHOICES = (
        (VACANT, 'Vacant'),
        (RESERVED, 'Reserved'),
        (OCCUPIED, 'Occupied'),
    )

    parent_property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name='units'
    )
    unit_number = models.CharField(
        max_length=50, 
    )
    monthly_rent = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=VACANT
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    active = models.BooleanField(
        default=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    @property
    def current_tenant(self): #unit.current_tenant usage
        tenancy = self.tenancies_by_unit.filter(
            status='ACTIVE'
        ).first()

        return tenancy.tenant if tenancy else None
    
    class Meta:
        ordering = ['parent_property', 'unit_number']
        unique_together = ('parent_property', 'unit_number')
    def __str__(self):
        return f"{self.parent_property.name} - {self.unit_number}"