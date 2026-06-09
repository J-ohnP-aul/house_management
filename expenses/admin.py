from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'property', 'category', 'status', 'amount', 'expense_date', 'created_by')
    list_filter = ('status', 'category', 'expense_date')
    search_fields = ('vendor', 'description', 'property__name')
    date_hierarchy = 'expense_date'
    ordering = ('-expense_date',)
