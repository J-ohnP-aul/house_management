import calendar
from datetime import datetime
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .forms import ReportFilterForm
from .permissions import AnyReportAccessMixin, FinancialAccessMixin, OccupancyAccessMixin, MaintenanceAccessMixin
from .services import (
    arrears_report,
    dashboard_summary,
    expense_report,
    income_report,
    maintenance_report,
    occupancy_summary,
    profit_report,
    tenant_reports,
    tenant_statement,
)
from .export_utils import export_csv, export_pdf, export_xlsx
from tenants.models import Tenant


class ReportBaseView(LoginRequiredMixin, FormView, TemplateView):
    form_class = ReportFilterForm
    template_name = 'reports/dashboard.html'
    paginate_by = 20
    report_rows = []
    report_columns = []
    report_keys = []
    export_filename = 'report'
    report_title = 'Report'
    permission_mixin = AnyReportAccessMixin

    def dispatch(self, request, *args, **kwargs):
        self.view = super()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data'] = self.request.GET or None
        return kwargs

    def get_filters(self):
        form = self.get_form()
        if form.is_valid():
            return form.cleaned_data
        return {}

    def get_report_rows(self, filters):
        return []

    def get_report_context(self, filters):
        return {}

    def get_export_filename(self):
        return self.export_filename

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.get_filters()
        rows = self.get_report_rows(filters)
        paginator = Paginator(rows, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'form': self.get_form(),
            'rows': page_obj.object_list,
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': page_obj.has_other_pages(),
            'export_query': self.request.GET.urlencode(),
            'report_title': self.report_title,
        })
        context.update(self.get_report_context(filters))
        return context

    def render_to_response(self, context, **response_kwargs):
        export_format = self.request.GET.get('export')
        if export_format in ('csv', 'xlsx', 'pdf'):
            return self.export_response(context['rows'], export_format)
        return super().render_to_response(context, **response_kwargs)

    def export_response(self, rows, export_format):
        filename = self.get_export_filename()
        if export_format == 'csv':
            return export_csv(filename, self.report_columns, self.report_keys, rows)
        if export_format == 'xlsx':
            return export_xlsx(filename, self.report_columns, self.report_keys, rows)
        if export_format == 'pdf':
            return export_pdf(self.report_title, filename, self.report_columns, self.report_keys, rows)
        return super().render_to_response(self.get_context_data())


class DashboardReportView(AnyReportAccessMixin, ReportBaseView):
    template_name = 'reports/dashboard.html'
    report_title = 'Report Dashboard'

    def get(self, request, *args, **kwargs):
        # Avoid passing a kwargs dict directly into get_form().
        self.form = self.get_form()
        return super().get(request, *args, **kwargs)

    def get_report_rows(self, filters):
        return []

    def get_report_context(self, filters):
        return {'summary': dashboard_summary()}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rows'] = []
        return context


class IncomeReportView(FinancialAccessMixin, ReportBaseView):
    template_name = 'reports/income_report.html'
    report_title = 'Monthly Income Report'
    report_columns = ['Month', 'Total Rent Collected', 'Total Payments', 'Number of Payments']
    report_keys = ['month', 'total_rent_collected', 'total_payments', 'number_of_payments']
    export_filename = 'income_report'

    def get_report_rows(self, filters):
        return income_report(
            property_obj=filters.get('property'),
            month=filters.get('month'),
            year=filters.get('year'),
            tenant=filters.get('tenant'),
            search=filters.get('search'),
        )

    def get_report_context(self, filters):
        rows = self.get_report_rows(filters)
        total_payments = sum([row['total_payments'] for row in rows])
        total_quantity = sum([row['number_of_payments'] for row in rows])
        return {
            'summary': {
                'total_payments': total_payments,
                'number_of_payments': total_quantity,
            }
        }


class ExpenseReportView(FinancialAccessMixin, ReportBaseView):
    template_name = 'reports/expense_report.html'
    report_title = 'Expense Report'
    report_columns = ['Category / Property / Month', 'Amount']
    report_keys = ['label', 'amount']
    export_filename = 'expense_report'

    def get_report_rows(self, filters):
        data = expense_report(
            property_obj=filters.get('property'),
            month=filters.get('month'),
            year=filters.get('year'),
            search=filters.get('search'),
        )
        rows = []
        for category in data['expenses_by_category']:
            rows.append({'label': category['category'], 'amount': category['total']})
        for prop in data['expenses_by_property']:
            rows.append({'label': prop['property__name'], 'amount': prop['total']})
        return rows

    def get_report_context(self, filters):
        return expense_report(
            property_obj=filters.get('property'),
            month=filters.get('month'),
            year=filters.get('year'),
            search=filters.get('search'),
        )


class ProfitReportView(FinancialAccessMixin, ReportBaseView):
    template_name = 'reports/profit_report.html'
    report_title = 'Profit Report'
    report_columns = ['Metric', 'Amount']
    report_keys = ['metric', 'amount']
    export_filename = 'profit_report'

    def get_report_rows(self, filters):
        data = profit_report(
            property_obj=filters.get('property'),
            month=filters.get('month'),
            year=filters.get('year'),
        )
        return [
            {'metric': 'Income', 'amount': data['income_total']},
            {'metric': 'Expenses', 'amount': data['expense_total']},
            {'metric': 'Profit', 'amount': data['profit']},
        ]

    def get_report_context(self, filters):
        return profit_report(
            property_obj=filters.get('property'),
            month=filters.get('month'),
            year=filters.get('year'),
        )


class ArrearsReportView(FinancialAccessMixin, ReportBaseView):
    template_name = 'reports/arrears_report.html'
    report_title = 'Arrears Report'
    report_columns = ['Tenant', 'Unit', 'Property', 'Current Balance']
    report_keys = ['tenant', 'unit', 'property', 'balance']
    export_filename = 'arrears_report'

    def get_report_rows(self, filters):
        return arrears_report(
            property_obj=filters.get('property'),
            tenant=filters.get('tenant'),
            search=filters.get('search'),
        )


class OccupancyReportView(OccupancyAccessMixin, ReportBaseView):
    template_name = 'reports/occupancy_report.html'
    report_title = 'Occupancy Report'
    report_columns = ['Property', 'Total Units', 'Occupied', 'Vacant', 'Reserved', 'Occupancy Rate']
    report_keys = ['property', 'total_units', 'occupied_units', 'vacant_units', 'reserved_units', 'occupancy_rate']
    export_filename = 'occupancy_report'

    def get_report_rows(self, filters):
        data = occupancy_summary(property_obj=filters.get('property'))
        return data['property_rows']

    def get_report_context(self, filters):
        data = occupancy_summary(property_obj=filters.get('property'))
        return data


class TenantReportView(FinancialAccessMixin, ReportBaseView):
    template_name = 'reports/tenant_report.html'
    report_title = 'Tenant Report'
    report_columns = ['Tenant Name', 'Phone', 'Unit', 'Property', 'Move In Date']
    report_keys = ['tenant_name', 'phone', 'unit', 'property', 'move_in_date']
    export_filename = 'tenant_report'

    def get_report_rows(self, filters):
        report = tenant_reports(search=filters.get('search'))
        return report['active_tenants']

    def get_report_context(self, filters):
        return tenant_reports(search=filters.get('search'))


class MaintenanceReportView(MaintenanceAccessMixin, ReportBaseView):
    template_name = 'reports/maintenance_report.html'
    report_title = 'Maintenance Report'
    report_columns = ['Category / Property / Month', 'Total Cost']
    report_keys = ['label', 'total_cost']
    export_filename = 'maintenance_report'

    def get_report_rows(self, filters):
        data = maintenance_report(
            property_obj=filters.get('property'),
            month=filters.get('month'),
            year=filters.get('year'),
            search=filters.get('search'),
        )
        rows = []
        for item in data['cost_by_property']:
            rows.append({'label': item['unit__parent_property__name'], 'total_cost': item['total_cost']})
        for item in data['cost_by_category']:
            rows.append({'label': item['category'], 'total_cost': item['total_cost']})
        for item in data['cost_by_month']:
            rows.append({'label': item['month'], 'total_cost': item['total_cost']})
        return rows

    def get_report_context(self, filters):
        return maintenance_report(
            property_obj=filters.get('property'),
            month=filters.get('month'),
            year=filters.get('year'),
            search=filters.get('search'),
        )


class TenantStatementReportView(FinancialAccessMixin, ReportBaseView):
    template_name = 'reports/tenant_statement.html'
    report_title = 'Tenant Statement'
    report_columns = ['Date', 'Description', 'Debit', 'Credit', 'Running Balance']
    report_keys = ['date', 'description', 'debit', 'credit', 'running_balance']
    export_filename = 'tenant_statement'

    def get_report_rows(self, filters):
        statement = tenant_statement(
            tenant=filters.get('tenant'),
            month=filters.get('month'),
            year=filters.get('year'),
        )
        return statement['ledger_entries']

    def get_report_context(self, filters):
        return tenant_statement(
            tenant=filters.get('tenant'),
            month=filters.get('month'),
            year=filters.get('year'),
        )
