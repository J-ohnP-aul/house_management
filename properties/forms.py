from django import forms
from django.db import models

from .models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'description', 'location', 'utility', 'image' ]
        