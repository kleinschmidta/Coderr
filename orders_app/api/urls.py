from django.urls import path

from .views import OrderDetailView, OrderListCreateView


urlpatterns = [
    path("", OrderListCreateView.as_view(), name="orders"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
]
