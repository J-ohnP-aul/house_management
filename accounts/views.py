# accounts/views.py

from datetime import date
import calendar
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.db.models import Count, Q, Sum

from .models import User
from .forms import CustomUserCreationForm
from properties.models import Property, Unit
from tenants.models import Tenant, Tenancy
from rent.models import Payment, RentCycle
from maintanance.models import Maintenance


def home(request):
    """Home page - redirects based on authentication"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')

@login_required
def dashboard(request):
    units = Unit.objects.all()
    properties = Property.objects.all()
    today = date.today()
    current_year = today.year
    current_month = today.month

    occupied_units = units.filter(status=Unit.OCCUPIED).count()
    vacant_units = units.filter(status=Unit.VACANT).count()
    reserved_units = units.filter(status=Unit.RESERVED).count()
    total_units_count = units.count()
    occupancy_rate = int((occupied_units / total_units_count) * 100) if total_units_count else 0
    reserved_rate = int((reserved_units / total_units_count) * 100) if total_units_count else 0
    vacant_rate = int((vacant_units / total_units_count) * 100) if total_units_count else 0

    monthly_income = Payment.objects.filter(
        payment_date__year=current_year,
        payment_date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    monthly_expenses = Maintenance.objects.filter(
        request_date__year=current_year,
        request_date__month=current_month
    ).aggregate(total=Sum('cost'))['total'] or 0

    net_profit = monthly_income - monthly_expenses
    rent_cycle_count = RentCycle.objects.count()

    maintenance_qs = Maintenance.objects.all()
    pending_maintenance = maintenance_qs.filter(status=Maintenance.PENDING).order_by('-request_date')[:5]
    pending_maintenance_count = maintenance_qs.filter(status=Maintenance.PENDING).count()

    property_qs = Property.objects.annotate(
        units_count=Count('units'),
        occupied_units=Count('units', filter=Q(units__status=Unit.OCCUPIED))
    ).order_by('-created_at')[:5]
    recent_properties = [
        {
            'name': property.name,
            'location': property.location,
            'units_count': property.units_count,
            'occupancy_pct': int((property.occupied_units / property.units_count) * 100) if property.units_count else 0,
        }
        for property in property_qs
    ]

    overdue_tenants = []
    for tenancy in Tenancy.objects.filter(status=Tenancy.ACTIVE).select_related('tenant', 'unit'):
        balance = tenancy.current_balance
        if balance > 0:
            due_day = tenancy.move_in_date.day
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            due_date = date(today.year, today.month, min(due_day, days_in_month))
            overdue_days = (today - due_date).days if today > due_date else 0
            overdue_tenants.append({
                'full_name': tenancy.tenant.full_name,
                'unit_number': tenancy.unit.unit_number,
                'amount_owed': balance,
                'days_overdue': overdue_days or 1,
            })

    overdue_count = len(overdue_tenants)
    outstanding_arrears = sum([tenant['amount_owed'] for tenant in overdue_tenants])

    chart_labels = []
    chart_income = []
    chart_expenses = []
    for offset in range(5, -1, -1):
        year = current_year
        month = current_month - offset
        while month <= 0:
            month += 12
            year -= 1
        chart_labels.append(calendar.month_abbr[month])
        monthly_income_point = Payment.objects.filter(
            payment_date__year=year,
            payment_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_expense_point = Maintenance.objects.filter(
            request_date__year=year,
            request_date__month=month
        ).aggregate(total=Sum('cost'))['total'] or 0
        chart_income.append(int(monthly_income_point))
        chart_expenses.append(int(monthly_expense_point))

    context = {
        'user': request.user,
        'total_properties': properties.count(),
        'total_units_count': total_units_count,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'reserved_units': reserved_units,
        'occupancy_rate': occupancy_rate,
        'reserved_rate': reserved_rate,
        'vacant_rate': vacant_rate,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'net_profit': net_profit,
        'outstanding_arrears': outstanding_arrears,
        'overdue_count': overdue_count,
        'pending_maintenance': pending_maintenance,
        'pending_maintenance_count': pending_maintenance_count,
        'recent_properties': recent_properties,
        'rent_cycle_count': rent_cycle_count,
        'overdue_tenants': overdue_tenants,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_income_json': json.dumps(chart_income),
        'chart_expenses_json': json.dumps(chart_expenses),
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def dashboard_stats(request):
    units = Unit.objects.all()
    total_units_count = units.count()
    occupied_units = units.filter(status=Unit.OCCUPIED).count()
    vacant_units = units.filter(status=Unit.VACANT).count()
    reserved_units = units.filter(status=Unit.RESERVED).count()
    occupancy_rate = int((occupied_units / total_units_count) * 100) if total_units_count else 0
    reserved_rate = int((reserved_units / total_units_count) * 100) if total_units_count else 0
    vacant_rate = int((vacant_units / total_units_count) * 100) if total_units_count else 0

    return JsonResponse({
        'total_units_count': total_units_count,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'reserved_units': reserved_units,
        'occupancy_rate': occupancy_rate,
        'reserved_rate': reserved_rate,
        'vacant_rate': vacant_rate,
    })

@login_required
@user_passes_test(lambda u: u.role == User.OWNER)
def register_user(request):
    """Register new users - Owner only"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.role == User.OWNER)
def user_list(request):
    """List all users - Owner only"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@user_passes_test(lambda u: u.role == User.OWNER)
def edit_user(request, user_id):
    """Edit user - Owner only"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update user fields
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')
        user.role = request.POST.get('role')
        user.save()
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('user_list')
    
    return render(request, 'accounts/edit_user.html', {'edit_user': user})


@login_required
@user_passes_test(lambda u: u.role == User.OWNER)
def deactivate_user(request, user_id):
    """Deactivate/activate user - Owner only"""
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account!')
        return redirect('user_list')
    
    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('user_list')


@login_required
def profile(request):
    """View user profile"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    """Edit own profile"""
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.phone_number = request.POST.get('phone_number')
        request.user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'accounts/edit_profile.html', {'user': request.user})