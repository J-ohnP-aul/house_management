from django.shortcuts import render, redirect, get_object_or_404
from .models import Property, Unit
from .forms import PropertyForm, UnitForm
from django.contrib.auth.decorators import login_required
from tenants.models import Tenant

# Create your views here.
@login_required
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect ('property_list')
    else:
        form = PropertyForm()
    return render(request, 'property/p_create.html', {'form':form})

@login_required
def property_list(request):
    units = Unit.objects.all()
    
    context = {
        'user': request.user,
        'total_properties': properties.count(),
        'total_units': units.count(),
        'occupied_units': units.filter(status='Occupied').count(),
        'vacant_units': units.filter(status='Vacant').count(),
        'reserved_units': units.filter(status='Reserved').count(),
    }
    properties = Property.objects.order_by('-created_at')
    return render(request, 'property/p_list.html', {'properties':properties, 'context':context})

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