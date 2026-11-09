from rest_framework import serializers

from orders_app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Order
        fields = (
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
