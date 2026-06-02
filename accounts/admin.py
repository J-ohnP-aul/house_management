from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Information",
            {
                "fields": (
                    "phone_number",
                    "role",
                )
            },
        ),
    )

    list_display = (
        "username",
        "first_name",
        "last_name",
        "phone_number",
        "role",
        "is_active",
    )

    list_filter = (
        "role",
        "is_active",
    )