from rest_framework import serializers

from offers_app.models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = (
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        )
        read_only_fields = ("id",)


class OfferCreateSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ("id", "title", "image", "description", "details")
        read_only_fields = ("id",)

    def validate_details(self, details):
        if len(details) != 3:
            raise serializers.ValidationError("An offer must contain exactly three details.")
        return details

    def create(self, validated_data):
        details_data = validated_data.pop("details")
        offer = Offer.objects.create(user=self.context["request"].user, **validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer


class OfferListFilterSerializer(serializers.Serializer):
    creator_id = serializers.IntegerField(required=False, min_value=1)
    min_price = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=0)
    max_delivery_time = serializers.IntegerField(required=False, min_value=1)
    ordering = serializers.ChoiceField(
        required=False,
        choices=["min_price", "-min_price", "updated_at", "-updated_at"],
        allow_blank=True,
    )
    search = serializers.CharField(required=False, allow_blank=True)
    page_size = serializers.IntegerField(required=False, min_value=1)


class OfferListSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = (
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
            "user_details",
        )

    def get_details(self, obj):
        return [{"id": detail.id, "url": f"/offerdetails/{detail.id}/"} for detail in obj.details.all()]

    def get_min_price(self, obj):
        return min((detail.price for detail in obj.details.all()), default=None)

    def get_min_delivery_time(self, obj):
        return min((detail.delivery_time_in_days for detail in obj.details.all()), default=None)

    def get_user_details(self, obj):
        return {
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "username": obj.user.username,
        }