from rest_framework import serializers

from ..models import CustomUser


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=CustomUser.UserType.choices)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password", "repeated_password", "type")
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        return CustomUser.objects.create_user(**validated_data)
