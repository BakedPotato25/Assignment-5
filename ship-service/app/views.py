from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Shipment
from .serializers import ShipmentSerializer
from . import metrics


class CreateShipment(APIView):
    def post(self, request):
        metrics.increment("shipment_create_total")
        serializer = ShipmentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            shipment = Shipment.objects.filter(order_id=data["order_id"]).order_by("-created_at").first()
            if shipment:
                shipment.address = data["address"]
                shipment.method = data["method"]
                shipment.status = "Processing"
                shipment.save(update_fields=["address", "method", "status"])
                metrics.increment("shipment_create_success_total")
                return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)

            shipment = Shipment.objects.create(
                order_id=data["order_id"],
                address=data["address"],
                method=data["method"],
                status="Processing",
            )
            metrics.increment("shipment_create_success_total")
            return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)
        metrics.increment("shipment_create_failed_total")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "service": "ship-service"}, status=status.HTTP_200_OK)


class MetricsView(APIView):
    def get(self, request):
        return HttpResponse(metrics.to_prometheus(), content_type="text/plain; version=0.0.4")
