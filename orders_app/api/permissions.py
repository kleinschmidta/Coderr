from rest_framework.permissions import BasePermission


class IsCustomerUser(BasePermission):
    """Allow access only to authenticated users of type 'customer'."""

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.type == "customer"


class IsBusinessUser(BasePermission):
    """Allow access only to authenticated users of type 'business'."""

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.type == "business"


class IsOrderBusinessUser(BasePermission):
    """Allow access only to the business user of the given order."""

    def has_object_permission(self, request, view, obj):
        return obj.business_user_id == request.user.id
