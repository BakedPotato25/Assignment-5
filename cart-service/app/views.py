import requests
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

logger = logging.getLogger(__name__)

BOOK_SERVICE_URL = "http://book-service:8000/books/"


class CartCreate(APIView):
    """POST /carts/ — Create or return existing cart for a customer_id."""

    def post(self, request):
        customer_id = request.data.get("customer_id")
        if not customer_id:
            return Response({"error": "customer_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class AddCartItem(APIView):
    """POST /cart-items/ — Add a book to a cart after verifying book exists."""

    def post(self, request):
        customer_id = request.data.get("customer_id")
        book_id     = request.data.get("book_id")
        quantity    = int(request.data.get("quantity", 1))

        if not customer_id or not book_id:
            return Response({"error": "customer_id and book_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Verify book exists in book-service
        try:
            resp = requests.get(BOOK_SERVICE_URL, timeout=5)
            resp.raise_for_status()
            book_ids = [b["id"] for b in resp.json()]
            if int(book_id) not in book_ids:
                return Response({"error": f"Book {book_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.RequestException as e:
            logger.error("book-service unreachable: %s", e)
            return Response({"error": "Book service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        item, created = CartItem.objects.get_or_create(cart=cart, book_id=book_id)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class UpdateCartItem(APIView):
    """PUT /cart-items/<item_id>/ — Update quantity of a cart item."""

    def put(self, request, item_id):
        try:
            item = CartItem.objects.get(pk=item_id)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get("quantity")
        if quantity is None:
            return Response({"error": "quantity is required."}, status=status.HTTP_400_BAD_REQUEST)
        quantity = int(quantity)
        if quantity <= 0:
            item.delete()
            return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)
        item.quantity = quantity
        item.save()
        return Response(CartItemSerializer(item).data)


class ViewCart(APIView):
    """GET /carts/<customer_id>/ — Retrieve full cart for a customer."""

    def get(self, request, customer_id):
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CartSerializer(cart).data)
