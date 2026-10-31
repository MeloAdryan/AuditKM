from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.models import User


class VehiclePermission(BasePermission):
    message = "Seu perfil não permite realizar esta operação."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        if user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return user.role in {
                User.Role.ADMIN,
                User.Role.MANAGER,
                User.Role.DRIVER,
            }

        return user.role in {
            User.Role.ADMIN,
            User.Role.MANAGER,
        }