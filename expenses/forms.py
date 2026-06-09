from django import forms
from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'property',
            'vendor',
            'category',
            'status',
            'expense_date',
            'amount',
            'description',
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-control'}),
            'vendor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor or supplier'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Expense description'}),
        }
