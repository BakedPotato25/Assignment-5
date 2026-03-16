from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from .serializers import PaymentSerializer
from . import metrics


class ProcessPayment(APIView):
    def post(self, request):
        metrics.increment("payment_process_total")
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            payment = Payment.objects.filter(order_id=data["order_id"]).order_by("-created_at").first()
            if payment:
                payment.amount = data["amount"]
                payment.method = data["method"]
                payment.status = "Success"
                payment.save(update_fields=["amount", "method", "status"])
                metrics.increment("payment_process_success_total")
                return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)

            payment = Payment.objects.create(
                order_id=data["order_id"],
                amount=data["amount"],
                method=data["method"],
                status="Success",
            )
            metrics.increment("payment_process_success_total")
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompensatePayment(APIView):
    def post(self, request):
        metrics.increment("payment_compensate_total")
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"error": "order_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.filter(order_id=order_id).order_by("-created_at").first()
        if not payment:
            payment = Payment.objects.create(
                order_id=order_id,
                amount=request.data.get("amount", "0"),
                method=request.data.get("method", "UNKNOWN"),
                status="Refunded",
            )
            metrics.increment("payment_refunded_total")
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

        payment.status = "Refunded"
        payment.save(update_fields=["status"])
        metrics.increment("payment_refunded_total")
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "service": "pay-service"}, status=status.HTTP_200_OK)


class MetricsView(APIView):
    def get(self, request):
        return HttpResponse(metrics.to_prometheus(), content_type="text/plain; version=0.0.4")
