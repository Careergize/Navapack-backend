from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_management(user):
    return bool(user.is_authenticated and (
        user.is_staff or user.is_superuser
        or user.groups.filter(name='Management').exists()
    ))


def get_salesperson(user):
    salesperson = getattr(user, 'salesperson', None)
    if salesperson is None or not salesperson.is_active:
        raise PermissionDenied('An active salesperson account must be linked to your user.')
    return salesperson


class SalesRecordPermission(BasePermission):
    """Authorize writes using the stored owner and date, never request data."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method not in SAFE_METHODS and not is_management(request.user):
            get_salesperson(request.user)
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or is_management(request.user):
            return True
        if obj.salesperson_id != get_salesperson(request.user).pk:
            raise PermissionDenied('You cannot modify another salesperson\'s record.')
        date_field = 'date_added' if hasattr(obj, 'date_added') else 'date'
        if getattr(obj, date_field) != timezone.localdate():
            raise PermissionDenied('You can modify only records dated today.')
        return True
