from django.urls import path

from .views import CompletedOrderCountView, OrderCountView


urlpatterns = [
    path("order-count/<int:business_user_id>/",
         OrderCountView.as_view(), name="order-count"),
    path("completed-order-count/<int:business_user_id>/",
         CompletedOrderCountView.as_view(), name="completed-order-count"),
]
