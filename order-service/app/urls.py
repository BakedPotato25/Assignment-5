from django.urls import path
from .views import CreateOrder, HealthView, MetricsView

urlpatterns = [
    path("orders/", CreateOrder.as_view(), name="create-order"),
    path("health/", HealthView.as_view(), name="health"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
]
