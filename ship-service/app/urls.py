from django.urls import path
from .views import CreateShipment, HealthView, MetricsView

urlpatterns = [
    path("shipments/", CreateShipment.as_view(), name="create-shipment"),
    path("health/", HealthView.as_view(), name="health"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
]
