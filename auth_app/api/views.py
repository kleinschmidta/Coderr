from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegistrationSerializer


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