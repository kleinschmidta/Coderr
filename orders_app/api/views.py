from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import (
    DestroyAPIView,
    ListCreateAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import OfferDetail
from orders_app.models import Order
from .permissions import (
    IsBusinessUser,
    IsCustomerUser,
    IsOrderBusinessUser,
    IsStaffUser,
)
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)


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
        detail = get_object_or_404(
            OfferDetail, pk=serializer.validated_data["offer_detail_id"])
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


class OrderDetailView(UpdateAPIView, DestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderUpdateSerializer
    http_method_names = ["patch", "delete", "options"]

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsStaffUser()]
        return [IsAuthenticated(), IsBusinessUser(), IsOrderBusinessUser()]

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)


class BaseOrderCountView(APIView):
    permission_classes = [IsAuthenticated]
    order_status = None
    count_key = None

    def get(self, request, business_user_id):
        business = get_object_or_404(
            get_user_model(), pk=business_user_id, type="business")
        count = Order.objects.filter(
            business_user=business, status=self.order_status).count()
        return Response({self.count_key: count})


class OrderCountView(BaseOrderCountView):
    order_status = Order.Status.IN_PROGRESS
    count_key = "order_count"


class CompletedOrderCountView(BaseOrderCountView):
    order_status = Order.Status.COMPLETED
    count_key = "completed_order_count"
