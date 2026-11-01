from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOfferOwnerOrReadOnly(BasePermission):
    """Allow write access to an offer only for the user who created it."""

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.user_id == request.user.id
