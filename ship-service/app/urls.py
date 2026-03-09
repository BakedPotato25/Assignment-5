from django.urls import path
from .views import CreateShipment

urlpatterns = [
    path("shipments/", CreateShipment.as_view(), name="create-shipment"),
]
