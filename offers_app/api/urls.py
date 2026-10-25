from django.urls import path

from .views import OfferListCreateView


urlpatterns = [
    path("", OfferListCreateView.as_view(), name="offers"),
]