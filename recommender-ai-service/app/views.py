import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

BOOK_POOL = list(range(1, 51))  # Pool of 50 book IDs


class RecommendBooks(APIView):
    def get(self, request, customer_id):
        recommended = random.sample(BOOK_POOL, k=3)
        return Response(
            {"customer_id": customer_id, "recommended_books": recommended},
            status=status.HTTP_200_OK,
        )
