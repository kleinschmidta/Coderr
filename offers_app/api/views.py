from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import CustomUser
from .serializers import OfferSerializer


class OfferCreateView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		if request.user.type != CustomUser.UserType.BUSINESS:
			return Response(status=status.HTTP_403_FORBIDDEN)

		serializer = OfferSerializer(
			data=request.data,
			context={"request": request},
		)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)