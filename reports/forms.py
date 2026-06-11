import calendar
from django import forms
from django.utils import timezone
from properties.models import Property
from tenants.models import Tenant

MONTH_CHOICES = [('', 'All months')] + [(i, calendar.month_name[i]) for i in range(1, 13)]
CURRENT_YEAR = timezone.now().year
YEAR_CHOICES = [('', 'All years')] + [(year, year) for year in range(CURRENT_YEAR - 5, CURRENT_YEAR + 2)]


class ReportFilterForm(forms.Form):
    property = forms.ModelChoiceField(
        queryset=Property.objects.order_by('name'),
        required=False,
        empty_label='All properties',
        label='Property',
    )
    search = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search tenants, units, properties...'}),
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=False,
        label='Month',
    )
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=False,
        label='Year',
    )
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.order_by('full_name'),
        required=False,
        empty_label='All tenants',
        label='Tenant',
    )

    def clean_month(self):
        month = self.cleaned_data.get('month')
        return int(month) if month else None

    def clean_year(self):
        year = self.cleaned_data.get('year')
        return int(year) if year else None
