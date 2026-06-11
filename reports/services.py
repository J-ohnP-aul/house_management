from datetime import datetime, date
from django.db.models import Count, F, Q, Sum, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from properties.models import Property, Unit
from tenants.models import Tenancy, Tenant
from rent.models import Payment, LedgerEntry
from expenses.models import Expense
from maintanance.models import Maintenance


def _apply_common_filters(queryset, property_obj=None, month=None, year=None, tenant=None):
    model_name = queryset.model.__name__
    if property_obj:
        if model_name == 'Payment':
            queryset = queryset.filter(tenancy__unit__parent_property=property_obj)
        else:
            queryset = queryset.filter(unit__parent_property=property_obj)
    if tenant:
        if model_name == 'Payment':
            queryset = queryset.filter(tenancy__tenant=tenant)
        else:
            queryset = queryset.filter(tenant=tenant)
    if month:
        queryset = queryset.filter(payment_date__month=month)
    if year:
        queryset = queryset.filter(payment_date__year=year)
    return queryset


def dashboard_summary():
    today = date.today()
    current_year = today.year
    current_month = today.month

    total_properties = Property.objects.count()
    total_units = Unit.objects.count()
    occupied_units = Unit.objects.filter(status=Unit.OCCUPIED).count()
    vacant_units = Unit.objects.filter(status=Unit.VACANT).count()
    reserved_units = Unit.objects.filter(status=Unit.RESERVED).count()
    active_tenants = Tenancy.objects.filter(status=Tenancy.ACTIVE).count()

    monthly_income = Payment.objects.filter(
        payment_date__year=current_year,
        payment_date__month=current_month,
    ).aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total']

    monthly_expenses = Expense.objects.filter(
        expense_date__year=current_year,
        expense_date__month=current_month,
    ).aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total']

    net_profit = monthly_income - monthly_expenses

    arrears_queryset = Tenancy.objects.filter(status=Tenancy.ACTIVE).annotate(
        debit_total=Coalesce(Sum('ledger_entries__debit'), Value(0, output_field=DecimalField())),
        credit_total=Coalesce(Sum('ledger_entries__credit'), Value(0, output_field=DecimalField())),
    ).annotate(
        balance=F('debit_total') - F('credit_total')
    ).filter(balance__gt=0)

    outstanding_arrears = arrears_queryset.aggregate(total=Coalesce(Sum('balance'), Value(0, output_field=DecimalField())))['total']
    occupancy_rate = (occupied_units / total_units) * 100 if total_units else 0

    return {
        'total_properties': total_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'reserved_units': reserved_units,
        'active_tenants': active_tenants,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'net_profit': net_profit,
        'outstanding_arrears': outstanding_arrears,
        'occupancy_rate': round(occupancy_rate, 2),
    }


def income_report(property_obj=None, month=None, year=None, tenant=None, search=None):
    if Payment.objects.exists():
        queryset = Payment.objects.select_related('tenancy__tenant', 'tenancy__unit__parent_property')
        queryset = _apply_common_filters(queryset, property_obj, month, year, tenant)
        if search:
            queryset = queryset.filter(
                Q(tenancy__tenant__full_name__icontains=search) |
                Q(tenancy__unit__unit_number__icontains=search) |
                Q(tenancy__unit__parent_property__name__icontains=search)
            )

        report_rows = queryset.values(
            'payment_date__year',
            'payment_date__month',
        ).annotate(
            total_rent_collected=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())),
            number_of_payments=Count('id'),
        ).order_by('-payment_date__year', '-payment_date__month')
    else:
        queryset = LedgerEntry.objects.filter(entry_type=LedgerEntry.PAYMENT).select_related(
            'tenancy__tenant', 'tenancy__unit__parent_property'
        )
        if property_obj:
            queryset = queryset.filter(tenancy__unit__parent_property=property_obj)
        if tenant:
            queryset = queryset.filter(tenancy__tenant=tenant)
        if month:
            queryset = queryset.filter(entry_date__month=month)
        if year:
            queryset = queryset.filter(entry_date__year=year)
        if search:
            queryset = queryset.filter(
                Q(tenancy__tenant__full_name__icontains=search) |
                Q(tenancy__unit__unit_number__icontains=search) |
                Q(tenancy__unit__parent_property__name__icontains=search)
            )

        report_rows = queryset.values(
            'entry_date__year',
            'entry_date__month',
        ).annotate(
            total_rent_collected=Coalesce(Sum('credit'), Value(0, output_field=DecimalField())),
            number_of_payments=Count('id'),
        ).order_by('-entry_date__year', '-entry_date__month')

    rows = []
    for row in report_rows:
        month_index = row.get('payment_date__month') or row.get('entry_date__month')
        year_value = row.get('payment_date__year') or row.get('entry_date__year')
        rows.append({
            'month': datetime(year=year_value, month=month_index, day=1).strftime('%B %Y'),
            'total_rent_collected': row['total_rent_collected'],
            'total_payments': row['total_rent_collected'],
            'number_of_payments': row['number_of_payments'],
            'year': year_value,
            'month_number': month_index,
        })

    return rows


def expense_report(property_obj=None, month=None, year=None, search=None):
    queryset = Expense.objects.select_related('property')
    if property_obj:
        queryset = queryset.filter(property=property_obj)
    if month:
        queryset = queryset.filter(expense_date__month=month)
    if year:
        queryset = queryset.filter(expense_date__year=year)
    if search:
        queryset = queryset.filter(
            Q(property__name__icontains=search) |
            Q(category__icontains=search) |
            Q(description__icontains=search)
        )

    total_expenses = queryset.aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total']
    expenses_by_category = queryset.values('category').annotate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))).order_by('-total')
    expenses_by_property = queryset.values('property__id', 'property__name').annotate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))).order_by('-total')

    return {
        'total_expenses': total_expenses,
        'expenses_by_category': expenses_by_category,
        'expenses_by_property': expenses_by_property,
        'queryset': queryset,
    }


def profit_report(property_obj=None, month=None, year=None):
    income_queryset = Payment.objects.all()
    expense_queryset = Expense.objects.all()

    if property_obj:
        income_queryset = income_queryset.filter(tenancy__unit__parent_property=property_obj)
        expense_queryset = expense_queryset.filter(property=property_obj)
    if month:
        income_queryset = income_queryset.filter(payment_date__month=month)
        expense_queryset = expense_queryset.filter(expense_date__month=month)
    if year:
        income_queryset = income_queryset.filter(payment_date__year=year)
        expense_queryset = expense_queryset.filter(expense_date__year=year)

    income_total = income_queryset.aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total']
    expense_total = expense_queryset.aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total']
    profit = income_total - expense_total

    return {
        'income_total': income_total,
        'expense_total': expense_total,
        'profit': profit,
        'income_queryset': income_queryset,
        'expense_queryset': expense_queryset,
    }


def arrears_report(property_obj=None, tenant=None, search=None):
    queryset = Tenancy.objects.filter(status=Tenancy.ACTIVE).select_related('tenant', 'unit__parent_property')
    if property_obj:
        queryset = queryset.filter(unit__parent_property=property_obj)
    if tenant:
        queryset = queryset.filter(tenant=tenant)
    if search:
        queryset = queryset.filter(
            Q(tenant__full_name__icontains=search) |
            Q(unit__unit_number__icontains=search) |
            Q(unit__parent_property__name__icontains=search)
        )

    queryset = queryset.annotate(
        debit_total=Coalesce(Sum('ledger_entries__debit'), Value(0, output_field=DecimalField())),
        credit_total=Coalesce(Sum('ledger_entries__credit'), Value(0, output_field=DecimalField())),
    ).annotate(
        balance=F('debit_total') - F('credit_total')
    ).filter(balance__gt=0).order_by('-balance')

    rows = []
    for tenancy in queryset:
        rows.append({
            'tenant': tenancy.tenant.full_name,
            'unit': tenancy.unit.unit_number,
            'property': tenancy.unit.parent_property.name,
            'balance': tenancy.balance,
            'tenancy_id': tenancy.id,
        })
    return rows


def occupancy_summary(property_obj=None):
    units = Unit.objects.all()
    if property_obj:
        units = units.filter(parent_property=property_obj)

    total_units = units.count()
    occupied = units.filter(status=Unit.OCCUPIED).count()
    vacant = units.filter(status=Unit.VACANT).count()
    reserved = units.filter(status=Unit.RESERVED).count()
    occupancy_rate = (occupied / total_units) * 100 if total_units else 0

    property_rows = Property.objects.annotate(
        total_units=Count('units'),
        occupied_units=Count('units', filter=Q(units__status=Unit.OCCUPIED)),
        vacant_units=Count('units', filter=Q(units__status=Unit.VACANT)),
        reserved_units=Count('units', filter=Q(units__status=Unit.RESERVED)),
    ).order_by('-occupied_units')

    rows = []
    for prop in property_rows:
        total = prop.total_units
        occupied_count = prop.occupied_units
        rows.append({
            'property': prop.name,
            'total_units': total,
            'occupied_units': occupied_count,
            'vacant_units': prop.vacant_units,
            'reserved_units': prop.reserved_units,
            'occupancy_rate': round((occupied_count / total) * 100, 2) if total else 0,
        })

    return {
        'total_units': total_units,
        'occupied_units': occupied,
        'vacant_units': vacant,
        'reserved_units': reserved,
        'occupancy_rate': round(occupancy_rate, 2),
        'property_rows': rows,
    }


def tenant_reports(search=None):
    active_tenants = Tenancy.objects.filter(status=Tenancy.ACTIVE).select_related('tenant', 'unit__parent_property').order_by('tenant__full_name')
    moved_out = Tenancy.objects.filter(status=Tenancy.MOVED_OUT).select_related('tenant', 'unit__parent_property').order_by('-move_out_date')

    if search:
        active_tenants = active_tenants.filter(
            Q(tenant__full_name__icontains=search) |
            Q(unit__unit_number__icontains=search) |
            Q(unit__parent_property__name__icontains=search)
        )
        moved_out = moved_out.filter(
            Q(tenant__full_name__icontains=search) |
            Q(unit__unit_number__icontains=search) |
            Q(unit__parent_property__name__icontains=search)
        )

    active_rows = [
        {
            'tenant_name': tenancy.tenant.full_name,
            'phone': tenancy.tenant.phone_no,
            'unit': tenancy.unit.unit_number,
            'property': tenancy.unit.parent_property.name,
            'move_in_date': tenancy.move_in_date,
            'tenant_id': tenancy.tenant.id,
            'tenancy_id': tenancy.id,
        }
        for tenancy in active_tenants
    ]

    moved_out_rows = [
        {
            'tenant_name': tenancy.tenant.full_name,
            'unit': tenancy.unit.unit_number,
            'property': tenancy.unit.parent_property.name,
            'move_out_date': tenancy.move_out_date,
        }
        for tenancy in moved_out
    ]

    return {
        'active_tenants': active_rows,
        'moved_out_tenants': moved_out_rows,
    }


def maintenance_report(property_obj=None, month=None, year=None, search=None):
    queryset = Maintenance.objects.select_related('unit__parent_property')
    if property_obj:
        queryset = queryset.filter(unit__parent_property=property_obj)
    if month:
        queryset = queryset.filter(request_date__month=month)
    if year:
        queryset = queryset.filter(request_date__year=year)
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(unit__unit_number__icontains=search) |
            Q(unit__parent_property__name__icontains=search)
        )

    total = queryset.count()
    pending = queryset.filter(status=Maintenance.PENDING).count()
    in_progress = queryset.filter(status=Maintenance.INPROGRESS).count()
    completed = queryset.filter(status=Maintenance.COMPLETE).count()

    cost_by_property = queryset.values('unit__parent_property__id', 'unit__parent_property__name').annotate(
        total_cost=Coalesce(Sum('cost'), Value(0, output_field=DecimalField())),
    ).order_by('-total_cost')

    cost_by_category = queryset.values('category').annotate(
        total_cost=Coalesce(Sum('cost'), Value(0, output_field=DecimalField())),
    ).order_by('-total_cost')

    cost_by_month = queryset.annotate(
        year=F('request_date__year'),
        month=F('request_date__month'),
    ).values('year', 'month').annotate(
        total_cost=Coalesce(Sum('cost'), Value(0, output_field=DecimalField())),
    ).order_by('-year', '-month')

    rows = []
    for row in cost_by_month:
        rows.append({
            'month': date(int(row['year']), int(row['month']), 1).strftime('%B %Y'),
            'total_cost': row['total_cost'],
        })

    return {
        'total_requests': total,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'cost_by_property': cost_by_property,
        'cost_by_category': cost_by_category,
        'cost_by_month': rows,
    }


def tenant_statement(tenant=None, month=None, year=None):
    tenancy = None
    statement_entries = []
    opening_balance = 0
    closing_balance = 0

    if tenant:
        tenancy = Tenancy.objects.filter(tenant=tenant).select_related('unit__parent_property').order_by('-move_in_date').first()

    if tenancy:
        ledger = LedgerEntry.objects.filter(tenancy=tenancy).select_related('rent_cycle').order_by('entry_date', 'id')
        if month and year:
            period_start = date(year, month, 1)
            period_entries = ledger.filter(entry_date__year=year, entry_date__month=month)
            opening_totals = ledger.filter(entry_date__lt=period_start).aggregate(
                debit=Coalesce(Sum('debit'), Value(0, output_field=DecimalField())),
                credit=Coalesce(Sum('credit'), Value(0, output_field=DecimalField())),
            )
            opening_balance = opening_totals['debit'] - opening_totals['credit']
        else:
            period_entries = ledger
            opening_balance = 0

        balance = opening_balance
        for entry in period_entries:
            balance += entry.debit - entry.credit
            statement_entries.append({
                'date': entry.entry_date,
                'description': entry.description,
                'debit': entry.debit,
                'credit': entry.credit,
                'running_balance': balance,
            })
        closing_balance = balance

    return {
        'tenancy': tenancy,
        'ledger_entries': statement_entries,
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
    }
