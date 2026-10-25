from django.db.models import Q, Min
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import CustomUser
from offers_app.models import Offer
from .serializers import OfferListFilterSerializer, OfferListSerializer, OfferCreateSerializer


class OfferListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filter_serializer = OfferListFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        validated = filter_serializer.validated_data

        queryset = Offer.objects.select_related("user").prefetch_related("details")

        if validated.get("creator_id"):
            queryset = queryset.filter(user_id=validated["creator_id"]).distinct()

        if validated.get("min_price"):
            queryset = queryset.filter(details__price__gte=validated["min_price"]).distinct()

        if validated.get("max_delivery_time"):
            queryset = queryset.filter(details__delivery_time_in_days__lte=validated["max_delivery_time"]).distinct()

        if validated.get("search"):
            queryset = queryset.filter(Q(title__icontains=validated["search"]) | Q(description__icontains=validated["search"]))

        ordering = validated.get("ordering") or "-updated_at"
        if ordering in {"min_price", "-min_price"}:
            queryset = queryset.annotate(min_price=Min("details__price")).order_by(ordering)
        else:
            queryset = queryset.order_by(ordering)

        paginator = PageNumberPagination()
        page_size = validated.get("page_size")
        if page_size:
            paginator.page_size = page_size

        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer = OfferListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = OfferListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OfferCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.type != CustomUser.UserType.BUSINESS:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = OfferCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OfferListCreateView(OfferListView, OfferCreateView):
    pass