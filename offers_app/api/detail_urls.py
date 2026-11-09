from django.urls import path

from .views import OfferDetailRetrieveView


urlpatterns = [
    path("<int:pk>/", OfferDetailRetrieveView.as_view(), name="offerdetail-single"),
]
