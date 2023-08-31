from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ["PATCH", "DELETE"]:
            return request.user == obj.creator
        return True
