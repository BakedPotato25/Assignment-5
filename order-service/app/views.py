import requests
import logging

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem, SagaStepLog
from .serializers import OrderSerializer
from .event_bus import publish_event
from . import metrics

logger = logging.getLogger(__name__)

PAY_SERVICE_URL  = "http://pay-service:8000/payments/"
PAY_COMPENSATE_URL = "http://pay-service:8000/payments/compensate/"
SHIP_SERVICE_URL = "http://ship-service:8000/shipments/"


class CreateOrder(APIView):
    """
    POST /orders/
    Body: { customer_id, items: [{book_id, quantity}], total_amount, payment_method, shipping_method, shipping_address }
    """

    def _log_step(self, order, step, from_status, to_status, success=True, detail=""):
        SagaStepLog.objects.create(
            order=order,
            step=step,
            from_status=from_status,
            to_status=to_status,
            success=success,
            detail=detail,
        )

    def _transition(self, order, next_status, step, success=True, detail=""):
        previous_status = order.status
        order.status = next_status
        order.save(update_fields=["status"])
        self._log_step(order, step, previous_status, next_status, success=success, detail=detail)

    def _reserve_payment(self, order_id, total_amount, payment_method):
        return requests.post(
            PAY_SERVICE_URL,
            json={"order_id": order_id, "amount": str(total_amount), "method": payment_method},
            timeout=5,
        )

    def _reserve_shipping(self, order_id, shipping_address, shipping_method):
        return requests.post(
            SHIP_SERVICE_URL,
            json={"order_id": order_id, "address": shipping_address, "method": shipping_method},
            timeout=5,
        )

    def _compensate_payment(self, order_id, total_amount, payment_method):
        try:
            publish_event(
                "payment.compensation.requested",
                {
                    "order_id": order_id,
                    "amount": str(total_amount),
                    "method": payment_method,
                },
            )
            compensate_resp = requests.post(
                PAY_COMPENSATE_URL,
                json={"order_id": order_id, "amount": str(total_amount), "method": payment_method},
                timeout=5,
            )
            compensate_resp.raise_for_status()
            publish_event(
                "payment.compensated",
                {
                    "order_id": order_id,
                    "amount": str(total_amount),
                    "method": payment_method,
                },
            )
            return True, "Payment compensation completed."
        except requests.exceptions.RequestException as e:
            logger.error("payment compensation error: %s", e)
            return False, f"Payment compensation failed: {e}"

    def post(self, request):
        metrics.increment("order_create_total")

        customer_id      = request.data.get("customer_id")
        items            = request.data.get("items", [])
        total_amount     = request.data.get("total_amount")
        payment_method   = request.data.get("payment_method", "COD")
        shipping_method  = request.data.get("shipping_method", "Standard")
        shipping_address = request.data.get("shipping_address", "")

        if not customer_id or not total_amount or not items:
            return Response(
                {"error": "customer_id, total_amount, and items are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Save order in Pending state.
        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=total_amount,
            status=Order.SagaStatus.PENDING,
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                book_id=item.get("book_id"),
                quantity=item.get("quantity", 1),
            )
        self._log_step(
            order,
            step="Create Order",
            from_status="",
            to_status=Order.SagaStatus.PENDING,
            success=True,
            detail="Order and items persisted.",
        )
        publish_event(
            "order.created",
            {
                "order_id": order.id,
                "customer_id": customer_id,
                "total_amount": str(total_amount),
                "items": items,
            },
        )

        # 2. Reserve payment.
        try:
            publish_event(
                "payment.reserve.requested",
                {
                    "order_id": order.id,
                    "amount": str(total_amount),
                    "method": payment_method,
                },
            )
            pay_resp = self._reserve_payment(order.id, total_amount, payment_method)
            pay_resp.raise_for_status()
            self._transition(
                order,
                Order.SagaStatus.PAYMENT_RESERVED,
                step="Reserve Payment",
                success=True,
                detail="Payment reserved successfully.",
            )
            publish_event(
                "payment.reserved",
                {
                    "order_id": order.id,
                    "amount": str(total_amount),
                    "method": payment_method,
                },
            )
        except requests.exceptions.RequestException as e:
            self._transition(
                order,
                Order.SagaStatus.PAYMENT_FAILED,
                step="Reserve Payment",
                success=False,
                detail=str(e),
            )
            metrics.increment("order_payment_failed_total")
            publish_event(
                "payment.failed",
                {
                    "order_id": order.id,
                    "amount": str(total_amount),
                    "method": payment_method,
                    "reason": str(e),
                },
            )
            logger.error("pay-service error: %s", e)
            return Response(
                {
                    "error": "Payment service failed.",
                    "order_id": order.id,
                    "status": order.status,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 3. Reserve shipping.
        try:
            publish_event(
                "shipping.reserve.requested",
                {
                    "order_id": order.id,
                    "address": shipping_address,
                    "method": shipping_method,
                },
            )
            ship_resp = self._reserve_shipping(order.id, shipping_address, shipping_method)
            ship_resp.raise_for_status()
            self._transition(
                order,
                Order.SagaStatus.SHIPPING_RESERVED,
                step="Reserve Shipping",
                success=True,
                detail="Shipping reserved successfully.",
            )
            publish_event(
                "shipping.reserved",
                {
                    "order_id": order.id,
                    "address": shipping_address,
                    "method": shipping_method,
                },
            )
        except requests.exceptions.RequestException as e:
            self._transition(
                order,
                Order.SagaStatus.SHIPPING_FAILED,
                step="Reserve Shipping",
                success=False,
                detail=str(e),
            )
            metrics.increment("order_shipping_failed_total")
            publish_event(
                "shipping.failed",
                {
                    "order_id": order.id,
                    "address": shipping_address,
                    "method": shipping_method,
                    "reason": str(e),
                },
            )

            compensated, compensation_detail = self._compensate_payment(order.id, total_amount, payment_method)
            if compensated:
                self._transition(
                    order,
                    Order.SagaStatus.COMPENSATED,
                    step="Compensate Payment",
                    success=True,
                    detail=compensation_detail,
                )
                metrics.increment("order_compensated_total")
                publish_event(
                    "order.compensated",
                    {
                        "order_id": order.id,
                        "status": Order.SagaStatus.COMPENSATED,
                    },
                )
            else:
                self._log_step(
                    order,
                    step="Compensate Payment",
                    from_status=order.status,
                    to_status=order.status,
                    success=False,
                    detail=compensation_detail,
                )

            logger.error("ship-service error: %s", e)
            return Response(
                {
                    "error": "Shipping service failed.",
                    "order_id": order.id,
                    "status": order.status,
                    "compensation": {
                        "attempted": True,
                        "success": compensated,
                    },
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 4. Confirm order.
        self._transition(
            order,
            Order.SagaStatus.CONFIRMED,
            step="Confirm Order",
            success=True,
            detail="Order confirmed.",
        )
        metrics.increment("order_create_success_total")
        publish_event(
            "order.confirmed",
            {
                "order_id": order.id,
                "status": Order.SagaStatus.CONFIRMED,
            },
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "service": "order-service"}, status=status.HTTP_200_OK)


class MetricsView(APIView):
    def get(self, request):
        return HttpResponse(metrics.to_prometheus(), content_type="text/plain; version=0.0.4")
