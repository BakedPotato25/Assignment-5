from django.urls import path
from .views import ProcessPayment

urlpatterns = [
    path("payments/", ProcessPayment.as_view(), name="process-payment"),
]
