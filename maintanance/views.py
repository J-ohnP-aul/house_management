from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Maintenance
from .forms import MaintenanceForm   # fixed spelling


@login_required
def maintenance_list(request):
    queryset = Maintenance.objects.all()
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')

    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(unit__unit_number__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if category_filter:
        queryset = queryset.filter(category=category_filter)

    total_count = queryset.count()
    pending_count = queryset.filter(status='PENDING').count()
    in_progress_count = queryset.filter(status='IN_PROGRESS').count()
    completed_count = queryset.filter(status='COMPLETED').count()

    return render(request, 'maintanance/m_list.html', {
        'maintenance_list': queryset,
        'total_count': total_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
    })

@login_required
def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance request created.')
            return redirect('m_list')
    else:
        form = MaintenanceForm()
    return render(request, 'maintanance/m_form.html', {'form': form, 'title': 'Create Maintenance'})

@login_required
def maintenance_update(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    if request.method == 'POST':
        form = MaintenanceForm(request.POST, instance=maintenance)   # fixed: use instance=maintenance
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance updated successfully.')
            return redirect('m_list')
    else:
        form = MaintenanceForm(instance=maintenance)
    return render(request, 'maintanance/m_form.html', {'form': form, 'title': 'Update Maintenance'})

@login_required
def maintenance_delete(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    maintenance.delete()
    messages.success(request, 'Maintenance request deleted.')
    return redirect('m_list')

@login_required
def maintenance_detail(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    return render(request, 'maintanance/m_detail.html', {'maintenance': maintenance})
