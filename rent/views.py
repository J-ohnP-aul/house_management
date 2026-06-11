# rent/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, DetailView, ListView
from django.contrib import messages
from django.shortcuts import get_object_or_404

from rent.forms import RentCycleForm
from rent.models import RentCycle, LedgerEntry
from rent.services import generate_rent_for_cycle
from tenants.models import Tenancy

class RentGenerateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "rent/generate_rent.html"
    form_class = RentCycleForm
    success_url = reverse_lazy("rent:cycles")

    def test_func(self):
        # Only Owner or Accountant can generate rent
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=["Owner", "Accountant"]).exists()

    def form_valid(self, form):
        cycle = form.save(commit=False)
        cycle.generated_by = self.request.user
        cycle.save()
        try:
            count = generate_rent_for_cycle(cycle, self.request.user)
            messages.success(self.request, f"Rent generated for {cycle.get_month_display()} {cycle.year}. {count} tenancy entries created.")
        except ValueError as e:
            messages.error(self.request, str(e))
        return super().form_valid(form)


class RentCycleListView(LoginRequiredMixin, ListView):
    model = RentCycle
    template_name = "rent/cycle_list.html"
    context_object_name = "cycles"


class TenantStatementView(LoginRequiredMixin, DetailView):
    model = Tenancy
    template_name = "rent/tenant_statement.html"
    context_object_name = "tenancy"
    pk_url_kwarg = "tenancy_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ledger = LedgerEntry.objects.filter(tenancy=self.object).order_by("entry_date")
        context["ledger_entries"] = ledger
        context["balance"] = self.object.current_balance
        return context