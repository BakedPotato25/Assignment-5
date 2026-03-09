from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Book
from .serializers import BookSerializer


class BookListCreate(APIView):
    """GET /books/  — list all | POST /books/ — create."""

    def get(self, request):
        books = Book.objects.all()
        return Response(BookSerializer(books, many=True).data)

    def post(self, request):
        s = BookSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetail(APIView):
    """GET /books/<id>/ | PUT /books/<id>/ | DELETE /books/<id>/"""

    def _get_book(self, pk):
        try:
            return Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return None

    def get(self, request, pk):
        book = self._get_book(pk)
        if not book:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(BookSerializer(book).data)

    def put(self, request, pk):
        book = self._get_book(pk)
        if not book:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        s = BookSerializer(book, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        book = self._get_book(pk)
        if not book:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        book.delete()
        return Response({"message": "Book deleted."}, status=status.HTTP_204_NO_CONTENT)
