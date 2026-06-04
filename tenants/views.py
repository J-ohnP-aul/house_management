from django.db.models import Q
from django.utils import timezone

from django.shortcuts import get_object_or_404, render, redirect, get_object_or_404
from django.contrib import messages
from .models import Tenancy, Tenant, Reservation
from .forms import TenantForm, ReservationForm, TenancyForm
from properties.models import Property

# Create your views here.
def tenant_list(request):
    tenants = Tenant.objects.all().prefetch_related('tenancies__unit__parent_property')
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status')
    property_filter = request.GET.get('property')

    if search_query:
        tenants = tenants.filter(
            Q(full_name__icontains=search_query)
            | Q(phone_no__icontains=search_query)
            | Q(id_no__icontains=search_query)
        )

    if property_filter:
        tenants = tenants.filter(tenancies__unit__parent_property_id=property_filter)

    if status_filter == 'active':
        tenants = tenants.filter(tenancies__status=Tenancy.ACTIVE)
    elif status_filter == 'moved_out':
        tenants = tenants.filter(tenancies__status=Tenancy.MOVED_OUT)

    tenants = tenants.distinct()

    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(tenancies__status=Tenancy.ACTIVE).distinct().count()
    moved_out_tenants = Tenant.objects.filter(tenancies__status=Tenancy.MOVED_OUT).distinct().count()

    context = {
        'tenants': tenants,
        'properties': Property.objects.all(),
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'moved_out_tenants': moved_out_tenants,
        'overdue_count': 0,
        'total_arrears': 0,
    }
    return render(request, 'tenants/tenant_list.html', context)

def tenant_create(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenant created successfully.')
            return redirect('tenant_list')
    else:
        form = TenantForm()
    return render(request, 'tenants/tenant_form.html', {'form': form})

def tenant_update(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenant updated successfully.')
            return redirect('tenant_list')
    else:
        form = TenantForm(instance=tenant)
    return render(request, 'tenants/tenant_form.html', {'form': form})

def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    return render(request, 'tenants/tenant_detail.html', {'tenant': tenant})

def reservation_list(request):
    reservations = Reservation.objects.all()
    return render(request, 'tenants/reservation_list.html', {'reservations': reservations})

def reservation_create(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reservation created successfully.')
            return redirect('reservation_list')
    else:
        form = ReservationForm()
    return render(request, 'tenants/reservation_form.html', {'form': form})

def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reservation updated successfully.')
            return redirect('reservation_list')
    else:
        form = ReservationForm(instance=reservation)
    return render(request, 'tenants/reservation_form.html', {'form': form})

def tenancy_create(request):
    if request.method == 'POST':
        form =  TenancyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenancy created successfully.')
            return redirect('tenant_list')
    else:
        return render(request, 'tenants/tenancy_form.html', {'form': TenancyForm()})
    
def tenancy_list(request):
    tenancies = Tenancy.objects.select_related('tenant', 'unit', 'unit__parent_property').all()
    return render(request, 'tenants/tenancy_list.html', {'tenancies': tenancies})

    
def tenancy_update(request, pk):
    tenancy = get_object_or_404(Tenancy, pk=pk)
    if request.method == 'POST':
        form = TenancyForm(request.POST, instance=tenancy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenancy updated successfully.')
            return redirect('tenant_list')
    else:
        form = TenancyForm(instance=tenancy)
    return render(request, 'tenants/tenancy_form.html', {'form': form})

def tenancy_moved_out(request, pk):
    tenancy = get_object_or_404(Tenancy, pk=pk)
    tenancy.status = Tenancy.MOVED_OUT
    tenancy.moved_out_date = timezone.now()
    tenancy.save()
    messages.success(request, 'Tenant marked as moved out successfully.')
    return redirect('tenant_list')

def tenant_history(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    tenancies = tenant.tenancies.select_related('unit', 'unit__property').order_by('-move_in_date')
    return render(request, 'tenants/tenant_history.html', {'tenant': tenant, 'tenancies': tenancies})