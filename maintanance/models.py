from django.db import models
from properties.models import Unit

# Create your models here.
class Maintenance(models.Model):
    PENDING = 'PENDING'
    INPROGRESS = 'INPROGRESS'
    COMPLETE = 'COMPLETE'
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (INPROGRESS, 'Inprogress'),
        (COMPLETE, 'Complete')
    )
    MAINTENANCE_CATEGORIES = (
        ('PLUMBING', 'Plumbing'),
        ('ELECTRICAL', 'Electrical'),
        ('PAINTING', 'Painting'),
        ('WINDOW', 'Window Repairs'),
        ('GENERAL', 'General Repairs'),
    )
    PRIORITY_CHOICES =(
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ("LOW", "Low"),
    )
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='maintaned_unit')
    title = models.CharField(max_length=50)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=MAINTENANCE_CATEGORIES, blank=False)
    priority =  models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    # reported_by = models
    request_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    cost =  models.DecimalField( max_digits=12,decimal_places=2)
    
    class Meta:
        ordering = ['-request_date']
    
    