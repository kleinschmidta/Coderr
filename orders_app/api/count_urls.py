from django.urls import path

from .views import OrderCountView


urlpatterns = [
    path("order-count/<int:business_user_id>/",
         OrderCountView.as_view(), name="order-count"),
]
