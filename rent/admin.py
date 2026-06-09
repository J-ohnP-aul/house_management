from django.contrib import admin
from .models import LedgerEntry, Payment, RentCyle
# Register your models here.
admin.site.register(LedgerEntry)
admin.site.register(Payment)
admin.site.register(RentCyle)