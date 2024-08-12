from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user and request.user.is_staff)


class IsAuthor(permissions.BasePermission):
    def has_permission(self, request, view):
        instance = view.get_object()
        return instance.author == request.user
