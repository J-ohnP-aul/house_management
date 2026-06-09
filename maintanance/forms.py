from django import forms
from .models import Maintenance

class MaintenanceForm(forms.ModelForm):
    class Meta:                    
        model = Maintenance
        fields = [
            'unit',
            'title',
            'description',
            'category',
            'priority',
            'status',
            'completion_date',      
            'cost'
        ]
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-control'}),   # unit is FK → use Select
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maintenance title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'completion_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cost'}),
        }