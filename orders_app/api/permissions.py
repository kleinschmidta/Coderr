from rest_framework.permissions import BasePermission


class IsCustomerUser(BasePermission):
    """Allow access only to authenticated users of type 'customer'."""

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.type == "customer"
