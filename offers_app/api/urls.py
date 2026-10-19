from django.urls import path

from .views import OfferCreateView


urlpatterns = [
    path("", OfferCreateView.as_view(), name="offers"),
]