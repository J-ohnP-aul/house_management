from django.db.models import Q
from django.utils import timezone
from django.db.models import Sum
from datetime import date
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404, render, redirect, get_object_or_404
from django.contrib import messages
from .models import Tenancy, Tenant, Reservation
from .forms import TenantForm, ReservationForm, TenancyForm
from properties.models import Property, Unit

# Create your views here.
@login_required
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

@login_required
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

@login_required
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

@login_required
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    tenancy = tenant.current_tenancy
    return render(request, 'tenants/tenant_detail.html', {'tenant': tenant, 'tenancy':tenancy})

@login_required
def reservation_list(request):
    now = date.today()
    context = {
        'total_reservations': Reservation.objects.count(),
        'pending_count': Reservation.objects.filter(status='PENDING').count(),
        'total_deposits': Reservation.objects.aggregate(Sum('deposit_amount'))['deposit_amount__sum'] or 0,
        'movein_this_month': Reservation.objects.filter(
            expected_movein_date__year=now.year,
            expected_movein_date__month=now.month
        ).count(),
        'pending_reservations': Reservation.objects.filter(status='PENDING'),
        'converted_reservations': Reservation.objects.filter(status='CONVERTED'),
        'cancelled_reservations': Reservation.objects.filter(status='CANCELLED'),
        'all_reservations_sorted': Reservation.objects.order_by('-expected_movein_date'),
    }
    return render(request, 'tenants/reservation_list.html', context)

@login_required
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

@login_required
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

from django.db import transaction

@login_required
def reservation_convert(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, status=Reservation.PENDING)
    if request.method == 'POST':
        with transaction.atomic():
            tenant, _ = Tenant.objects.get_or_create(
                phone_no=reservation.phone_no,
                defaults={
                    'full_name': reservation.full_name,
                    'id_no': reservation.id_no or '',
                }
            )
            tenancy = Tenancy.objects.create(
                tenant=tenant,
                unit=reservation.unit,
                move_in_date=reservation.expected_movein_date,
                status=Tenancy.ACTIVE
            )
            Reservation.objects.filter(pk=reservation.pk).update(
                status=Reservation.CONVERTED,
                tenancy=tenancy
            )
        messages.success(request, f'Reservation converted to tenancy for {tenant.full_name}.')
        return redirect('tenancy_list')
    
    return render(request, 'tenants/reservation_convert_confirm.html', {'reservation': reservation})

@login_required
def tenancy_create(request):
    if request.method == 'POST':
        form =  TenancyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenancy created successfully.')
            return redirect('tenancy_list')
    else:
        return render(request, 'tenants/tenancy_form.html', {'form': TenancyForm()})

@login_required    
def tenancy_list(request):
    tenancies = Tenancy.objects.select_related('tenant', 'unit', 'unit__parent_property').all()
    active_count = tenancies.filter(status=Tenancy.ACTIVE).count()
    moved_out_count = tenancies.filter(status=Tenancy.MOVED_OUT).count()
    total_units = Unit.objects.count()
    occupied_units = Tenancy.objects.filter(status=Tenancy.ACTIVE).values('unit').distinct().count()
    occupancy_rate = round((occupied_units / total_units)*100 if total_units else 0)
    context = {
        'tenancies': tenancies,
        'active_count': active_count,
        'moved_out_count': moved_out_count,
        'occupancy_rate': occupancy_rate,
    }
    return render(request, 'tenants/tenancy_list.html', context)

@login_required    
def tenancy_update(request, pk):
    tenancy = get_object_or_404(Tenancy, pk=pk)
    if request.method == 'POST':
        form = TenancyForm(request.POST, instance=tenancy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenancy updated successfully.')
            return redirect('tenancy_list')
    else:
        form = TenancyForm(instance=tenancy)
    return render(request, 'tenants/tenancy_form.html', {'form': form})

@login_required
def tenancy_moved_out(request, pk):
    tenancy = get_object_or_404(Tenancy, pk=pk)
    tenancy.status = Tenancy.MOVED_OUT
    tenancy.moved_out_date = timezone.now()
    tenancy.save()
    messages.success(request, 'Tenant marked as moved out successfully.')
    return redirect('tenant_list')

@login_required
def tenant_history(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    tenancies = tenant.tenancies.select_related('unit', 'unit__parent_property').order_by('-move_in_date')
    return render(request, 'tenants/tenant_history.html', {'tenant': tenant, 'tenancies': tenancies})