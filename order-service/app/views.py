import requests
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from .serializers import OrderSerializer

logger = logging.getLogger(__name__)

PAY_SERVICE_URL  = "http://pay-service:8000/payments/"
SHIP_SERVICE_URL = "http://ship-service:8000/shipments/"


class CreateOrder(APIView):
    """
    POST /orders/
    Body: { customer_id, items: [{book_id, quantity}], total_amount, payment_method, shipping_address }
    """

    def post(self, request):
        customer_id      = request.data.get("customer_id")
        items            = request.data.get("items", [])
        total_amount     = request.data.get("total_amount")
        payment_method   = request.data.get("payment_method", "COD")
        shipping_address = request.data.get("shipping_address", "")

        if not customer_id or not total_amount or not items:
            return Response(
                {"error": "customer_id, total_amount, and items are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Save order
        order = Order.objects.create(customer_id=customer_id, total_amount=total_amount)
        for item in items:
            OrderItem.objects.create(
                order=order,
                book_id=item.get("book_id"),
                quantity=item.get("quantity", 1),
            )

        # 2. Call pay-service
        try:
            pay_resp = requests.post(
                PAY_SERVICE_URL,
                json={"order_id": order.id, "amount": str(total_amount), "method": payment_method},
                timeout=5,
            )
            pay_resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            order.status = "Payment Failed"
            order.save()
            logger.error("pay-service error: %s", e)
            return Response({"error": "Payment service failed.", "order_id": order.id}, status=status.HTTP_502_BAD_GATEWAY)

        # 3. Call ship-service
        try:
            ship_resp = requests.post(
                SHIP_SERVICE_URL,
                json={"order_id": order.id, "address": shipping_address, "method": "Standard"},
                timeout=5,
            )
            ship_resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            order.status = "Shipping Failed"
            order.save()
            logger.error("ship-service error: %s", e)
            return Response({"error": "Shipping service failed.", "order_id": order.id}, status=status.HTTP_502_BAD_GATEWAY)

        # 4. Confirm order
        order.status = "Confirmed"
        order.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
