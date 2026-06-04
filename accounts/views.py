# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from .models import User
from .forms import CustomUserCreationForm
from properties.models import Property, Unit
from tenants.models import Tenant


def home(request):
    """Home page - redirects based on authentication"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')

@login_required
def dashboard(request):
    units = Unit.objects.all()
    properties = Property.objects.all()
    tenants = Tenant.objects.all()

    occupied_units = units.filter(status=Unit.OCCUPIED).count()
    vacant_units = units.filter(status=Unit.VACANT).count()
    reserved_units = units.filter(status=Unit.RESERVED).count()
    total_units_count = units.count()
    occupancy_rate = int((occupied_units / total_units_count) * 100) if total_units_count else 0
    reserved_rate = int((reserved_units / total_units_count) * 100) if total_units_count else 0
    vacant_rate = int((vacant_units / total_units_count) * 100) if total_units_count else 0
    
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
        'monthly_income': 0,
        'monthly_expenses': 0,
        'outstanding_arrears': 0,
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