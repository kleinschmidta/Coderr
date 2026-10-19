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


class OfferSerializer(serializers.ModelSerializer):
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