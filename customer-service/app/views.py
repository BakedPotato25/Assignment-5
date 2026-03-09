import requests
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer
from .serializers import CustomerSerializer

logger = logging.getLogger(__name__)

CART_SERVICE_URL = "http://cart-service:8000/carts/"


class CustomerListCreate(APIView):
    def get(self, request):
        customers = Customer.objects.all()
        return Response(CustomerSerializer(customers, many=True).data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            # Automatically create a cart for the new customer
            try:
                requests.post(
                    CART_SERVICE_URL,
                    json={"customer_id": customer.id},
                    timeout=3,
                )
            except requests.exceptions.RequestException as e:
                logger.warning("Could not create cart for customer %s: %s", customer.id, e)
            return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
