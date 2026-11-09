from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from offers_app.models import OfferDetail
from orders_app.models import Order
from .permissions import IsCustomerUser
from .serializers import OrderCreateSerializer, OrderSerializer


class OrderListCreateView(ListCreateAPIView):
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        detail = get_object_or_404(OfferDetail, pk=serializer.validated_data["offer_detail_id"])
        order = self.create_order(detail, request.user)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def create_order(self, detail, customer):
        return Order.objects.create(
            customer_user=customer,
            business_user=detail.offer.user,
            title=detail.title,
            revisions=detail.revisions,
            delivery_time_in_days=detail.delivery_time_in_days,
            price=detail.price,
            features=detail.features,
            offer_type=detail.offer_type,
        )
