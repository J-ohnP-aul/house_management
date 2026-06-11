# rent/forms.py
from django import forms
from rent.models import RentCycle

class RentCycleForm(forms.ModelForm):
    class Meta:
        model = RentCycle
        fields = ["month", "year", "notes"]
        widgets = {
            "month": forms.Select(choices=[(i, i) for i in range(1, 13)]),
            "year": forms.NumberInput(attrs={"min": 2020, "max": 2030}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }