from django.urls import path
from .views import ProcessPayment, CompensatePayment, HealthView, MetricsView

urlpatterns = [
    path("payments/", ProcessPayment.as_view(), name="process-payment"),
    path("payments/compensate/", CompensatePayment.as_view(), name="compensate-payment"),
    path("health/", HealthView.as_view(), name="health"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
]
