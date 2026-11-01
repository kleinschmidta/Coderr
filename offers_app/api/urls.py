from django.urls import path

from .views import OfferListCreateView, OfferRetrieveUpdateDestroyView


urlpatterns = [
    path("", OfferListCreateView.as_view(), name="offers"),
    path("<int:pk>/", OfferRetrieveUpdateDestroyView.as_view(), name="offer-single"),
]