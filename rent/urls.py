# rent/urls.py
from django.urls import path
from rent.views import RentGenerateView, RentCycleListView, TenantStatementView

app_name = "rent"

urlpatterns = [
    path("generate/", RentGenerateView.as_view(), name="generate"),
    path("cycles/", RentCycleListView.as_view(), name="cycles"),
    path("statement/<int:tenancy_id>/", TenantStatementView.as_view(), name="tenant_statement"),
]