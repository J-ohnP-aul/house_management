from django.db import models

# Create your models here.
class Property(models.Model):
    ELECTRICITY = 'ELECTRICITY'
    WATER = 'WATER'
    BOTH = 'BOTH'
    
    UTILITY_BILLING_CHOICES = [
        (ELECTRICITY, 'electricity'),
        (WATER, 'water'),
        (BOTH, 'Water & electricity')
    ]
    name = models.CharField(max_length=40)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    picture = models.ImageField(upload_to='properties')
    location = models.CharField(max_length=20)
    utility = models.CharField(max_length=40, choices=UTILITY_BILLING_CHOICES, default=BOTH)
    created_at = models.DateField(auto_now_add=True)