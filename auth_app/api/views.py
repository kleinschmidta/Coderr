from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import CustomUser
from .serializers import (
	BusinessProfileSerializer,
	CustomerProfileSerializer,
	ProfileSerializer,
	RegistrationSerializer,
)


class RegistrationView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = RegistrationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		token, _ = Token.objects.get_or_create(user=user)

		return Response(
			{
				"token": token.key,
				"username": user.username,
				"email": user.email,
				"user_id": user.id,
			},
			status=status.HTTP_201_CREATED,
		)


class LoginView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		username = request.data.get("username")
		password = request.data.get("password")

		if not username or not password:
			return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

		user = authenticate(request, username=username, password=password)
		if user is None:
			return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

		token, _ = Token.objects.get_or_create(user=user)
		return Response(
			{
				"token": token.key,
				"username": user.username,
				"email": user.email,
				"user_id": user.id,
			},
			status=status.HTTP_200_OK,
		)


class ProfileView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, pk):
		user = get_object_or_404(CustomUser, pk=pk)
		return Response(ProfileSerializer(user).data)

	def patch(self, request, pk):
		if request.user.pk != pk:
			return Response(status=status.HTTP_403_FORBIDDEN)

		user = get_object_or_404(CustomUser, pk=pk)
		serializer = ProfileSerializer(user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data)


class ProfileListView(APIView):
	permission_classes = [IsAuthenticated]
	user_type = None
	serializer_class = ProfileSerializer

	def get(self, request):
		users = CustomUser.objects.filter(type=self.user_type).order_by("id")
		return Response(self.serializer_class(users, many=True).data)


class BusinessProfilesView(ProfileListView):
	user_type = CustomUser.UserType.BUSINESS
	serializer_class = BusinessProfileSerializer


class CustomerProfilesView(ProfileListView):
	user_type = CustomUser.UserType.CUSTOMER
	serializer_class = CustomerProfileSerializer