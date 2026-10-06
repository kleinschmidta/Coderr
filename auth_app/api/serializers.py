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


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source="pk", read_only=True)
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            "user",
            "username",
            "first_name", # #
            "last_name", # #
            "file",
            "location", # #
            "tel", # #
            "description", # #
            "working_hours", # #
            "type",
            "email", #
            "created_at",
            "uploaded_at",
        )
        read_only_fields = ("user", "username", "file", "type", "created_at", "uploaded_at")


class BusinessProfileSerializer(ProfileSerializer):
    class Meta(ProfileSerializer.Meta):
        fields = (
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
        )


class CustomerProfileSerializer(ProfileSerializer):
    class Meta(ProfileSerializer.Meta):
        fields = (
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "uploaded_at",
            "type",
        )
