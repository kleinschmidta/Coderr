from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from orders_app.models import Order
from .serializers import OrderSerializer


class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))
