from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.DashboardReportView.as_view(), name='dashboard'),
    path('income/', views.IncomeReportView.as_view(), name='income'),
    path('expenses/', views.ExpenseReportView.as_view(), name='expenses'),
    path('profit/', views.ProfitReportView.as_view(), name='profit'),
    path('arrears/', views.ArrearsReportView.as_view(), name='arrears'),
    path('occupancy/', views.OccupancyReportView.as_view(), name='occupancy'),
    path('tenants/', views.TenantReportView.as_view(), name='tenants'),
    path('maintenance/', views.MaintenanceReportView.as_view(), name='maintenance'),
    path('tenant-statement/', views.TenantStatementReportView.as_view(), name='tenant_statement'),
]
