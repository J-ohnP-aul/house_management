from .models import Tenant, Reservation, Tenancy
from django import forms
from properties.models import Unit

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['full_name', 'phone_no', 'id_no', 'emergency_no']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'id_no': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_no': forms.TextInput(attrs={'class': 'form-control'}),
            # 'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),  
        }
        

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['unit', 'full_name','phone_no', 'deposit_amount', 'expected_movein_date', 'notes']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'expected_movein_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = ['unit', 'tenant', 'move_in_date', 'status']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'tenant': forms.Select(attrs={'class': 'form-control'}),
            'move_in_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['unit'].queryset = Unit.objects.filter(
            active=True
        )