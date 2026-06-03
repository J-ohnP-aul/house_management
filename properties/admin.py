from django.contrib import admin

from .models import Property, Unit

admin.site.register(Property)
admin.site.register(Unit)


# @admin.register(Property)
# class PropertyAdmin(admin.ModelAdmin):
#     list_display = (
#         'name',
#         'location',
#         'water_included',
#         'electricity_included',
#         'active',
#     )

#     list_filter = (
#         'water_included',
#         'electricity_included',
#         'active',
#     )

#     search_fields = (
#         'name',
#         'location',
#     )


# @admin.register(Unit)
# class UnitAdmin(admin.ModelAdmin):
#     list_display = (
#         'unit_number',
#         'property',
#         'monthly_rent',
#         'status',
#         'active',
#     )

#     list_filter = (
#         'status',
#         'property',
#         'active',
#     )

#     search_fields = (
#         'unit_number',
#         'property__name',
#     )