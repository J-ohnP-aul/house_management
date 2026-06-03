from django import forms
from .models import Property, Unit

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'name', 
            'location', 
            'description', 
            'water_included', 
            'electricity_included',
            'active' # Un-commented to match your widget, or remove both if you don't want it on creation form
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Property Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 123 Main St'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Property details...'}),
            'water_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'electricity_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        # Enforcing inclusion of 'description' and 'active' to match your model attributes
        fields = ['parent_property', 'unit_number', 'monthly_rent', 'status', 'description', 'active']
        
        widgets = {
            'parent_property': forms.Select(attrs={'class': 'form-control'}),
            'unit_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit Number i.e A1'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly Rent'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Unit details...'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }