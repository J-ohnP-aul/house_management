from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Case, When, Value, IntegerField, FloatField, ExpressionWrapper, F

from .models import Property, Unit
from .forms import PropertyForm, UnitForm
from tenants.models import Tenant

# Create your views here.
@login_required
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('property_list')
    else:
        form = PropertyForm()
    return render(request, 'property/p_create.html', {'form': form})

@login_required
def property_list(request):
    properties = Property.objects.order_by('-created_at').annotate(
        units_count=Count('units'),
        occupied_count=Sum(
            Case(
                When(units__status=Unit.OCCUPIED, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        vacant_count=Sum(
            Case(
                When(units__status=Unit.VACANT, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
    ).annotate(
        occupancy_pct=ExpressionWrapper(
            Case(
                When(units_count=0, then=Value(0.0)),
                default=F('occupied_count') * 100.0 / F('units_count'),
                output_field=FloatField(),
            ),
            output_field=FloatField(),
        )
    )
    return render(request, 'property/p_list.html', {'properties': properties})

@login_required
def property_detail(request, id):
    property = get_object_or_404(Property, id=id)
    return render(request, 'property/p_detail.html', {'property':property})

@login_required
def property_update(request, id):
    property = get_object_or_404(Property, id=id)
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            form.save()
            return redirect('property_detail', slug=property.slug)
    else:
        form = PropertyForm(instance=property)
    return render(request, 'property/p_update.html', {'form':form})
@login_required
def unit_list(request):
    units = Unit.objects.order_by('-unit_number')
    return render(request, 'units/u_list.html', {'units':units})

@login_required
def unit_create(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('unit_list')
    else:
        form = UnitForm()
    return render(request, 'units/u_create.html', {'form':form})    

def unit_detail(request, id):
    unit = get_object_or_404(Unit, id=id)
    # tenant = 
    return render(request, 'units/u_detail.html', {'unit':unit})