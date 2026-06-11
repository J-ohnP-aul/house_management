from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Case, When, Value, IntegerField, FloatField, ExpressionWrapper, F

from .models import Property, Unit
from .forms import PropertyForm, UnitForm
from tenants.models import Tenant, Tenancy

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
    units = property.units.all()
    total_units = units.count()
    occupied_units = units.filter(status=Unit.OCCUPIED).count()
    reserved_units = units.filter(status=Unit.RESERVED).count()
    vacant_units = units.filter(status=Unit.VACANT).count()
    occupancy_pct = int((occupied_units / total_units) * 100) if total_units else 0
    active_tenants = Tenant.objects.filter(
        tenancies__unit__parent_property=property,
        tenancies__status=Tenancy.ACTIVE
    ).distinct().count()
    moved_out_tenants = Tenant.objects.filter(
        tenancies__unit__parent_property=property,
        tenancies__status=Tenancy.MOVED_OUT
    ).distinct().count()
    recent_activity = Tenancy.objects.filter(
        unit__parent_property=property
    ).select_related('tenant', 'unit').order_by('-updated_at')[:5]

    return render(request, 'property/p_detail.html', {
        'property': property,
        'units': units,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'reserved_units': reserved_units,
        'vacant_units': vacant_units,
        'occupancy_pct': occupancy_pct,
        'active_tenants': active_tenants,
        'moved_out_tenants': moved_out_tenants,
        'recent_activity': recent_activity,
    })

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
    return render(request, 'property/p_create.html', {'form':form})

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
    return render(request, 'units/unit_form.html', {'form': form})

@login_required
def unit_edit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            return redirect('unit_list')
    else:
        form = UnitForm(instance=unit)
    return render(request, 'units/unit_form.html', {'form': form})
def unit_detail(request, id):
    unit = get_object_or_404(Unit, id=id)
    # tenant = 
    return render(request, 'units/u_detail.html', {'unit':unit})