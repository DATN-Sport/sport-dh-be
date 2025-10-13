from rest_framework import permissions
from apps.utils.enum_type import RoleSystemEnum


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == RoleSystemEnum.ADMIN)


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and
                    request.user.role in [
                        RoleSystemEnum.ADMIN,
                        RoleSystemEnum.OWNER,
                    ])


class IsUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and
                    request.user.role in [
                        RoleSystemEnum.USER,
                        RoleSystemEnum.OWNER,
                        RoleSystemEnum.ADMIN,
                    ])
