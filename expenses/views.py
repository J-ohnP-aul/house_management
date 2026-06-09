from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render, get_object_or_404, redirect

from .forms import ExpenseForm
from .models import Expense


@login_required
def expense_list(request):
    queryset = Expense.objects.select_related('property', 'created_by').all()
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    property_filter = request.GET.get('property', '')

    if search_query:
        queryset = queryset.filter(
            Q(vendor__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(property__name__icontains=search_query)
        )
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if category_filter:
        queryset = queryset.filter(category=category_filter)
    if property_filter:
        queryset = queryset.filter(property_id=property_filter)

    total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/expense_list.html', {
        'expense_list': queryset,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'property_filter': property_filter,
        'total_amount': total_amount,
    })


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'Expense added successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Create Expense'})


@login_required
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully.')
            return redirect('expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Update Expense', 'expense': expense})


@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    return render(request, 'expenses/expense_detail.html', {'expense': expense})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    messages.success(request, 'Expense deleted successfully.')
    return redirect('expense_list')
