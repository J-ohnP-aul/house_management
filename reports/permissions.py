from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


def _user_has_group(user, group_name):
    return user.groups.filter(name__iexact=group_name).exists()


def _user_has_role(user, role_name):
    return getattr(user, "role", None) == role_name


class ReportAccessMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        return redirect('dashboard')

    def has_permission(self, user):
        return user.is_authenticated


class AnyReportAccessMixin(ReportAccessMixin):
    pass


class OwnerAccessMixin(ReportAccessMixin):
    def has_permission(self, user):
        if super().has_permission(user) and user.is_superuser:
            return True
        return _user_has_role(user, 'OWNER') or _user_has_group(user, 'Owner')


class AccountantAccessMixin(ReportAccessMixin):
    def has_permission(self, user):
        if super().has_permission(user) and user.is_superuser:
            return True
        return (
            _user_has_role(user, 'ACCOUNTANT')
            or _user_has_group(user, 'Accountant')
            or _user_has_role(user, 'OWNER')
            or _user_has_group(user, 'Owner')
        )


class CaretakerAccessMixin(ReportAccessMixin):
    def has_permission(self, user):
        if super().has_permission(user) and user.is_superuser:
            return True
        return (
            _user_has_role(user, 'CARETAKER')
            or _user_has_group(user, 'Caretaker')
            or _user_has_role(user, 'OWNER')
            or _user_has_group(user, 'Owner')
            or _user_has_role(user, 'MANAGER')
            or _user_has_group(user, 'Manager')
        )


class FinancialAccessMixin(ReportAccessMixin):
    def has_permission(self, user):
        if super().has_permission(user) and user.is_superuser:
            return True
        return (
            _user_has_role(user, 'ACCOUNTANT')
            or _user_has_group(user, 'Accountant')
            or _user_has_role(user, 'OWNER')
            or _user_has_group(user, 'Owner')
        )


class OccupancyAccessMixin(ReportAccessMixin):
    def has_permission(self, user):
        if super().has_permission(user) and user.is_superuser:
            return True
        return (
            _user_has_role(user, 'CARETAKER')
            or _user_has_group(user, 'Caretaker')
            or _user_has_role(user, 'OWNER')
            or _user_has_group(user, 'Owner')
            or _user_has_role(user, 'MANAGER')
            or _user_has_group(user, 'Manager')
        )


class MaintenanceAccessMixin(ReportAccessMixin):
    def has_permission(self, user):
        if super().has_permission(user) and user.is_superuser:
            return True
        return (
            _user_has_role(user, 'CARETAKER')
            or _user_has_group(user, 'Caretaker')
            or _user_has_role(user, 'OWNER')
            or _user_has_group(user, 'Owner')
            or _user_has_role(user, 'MANAGER')
            or _user_has_group(user, 'Manager')
        )


class FinancialAccessMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        return redirect('dashboard')

    def has_permission(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return _user_has_role(user, 'ACCOUNTANT') or _user_has_group(user, 'Accountant') or _user_has_role(user, 'OWNER') or _user_has_group(user, 'Owner')
