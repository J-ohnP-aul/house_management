from django.contrib import admin
from .models import LedgerEntry, Payment, RentCycle
# Register your models here.
admin.site.register(LedgerEntry)
admin.site.register(Payment)
admin.site.register(RentCycle)