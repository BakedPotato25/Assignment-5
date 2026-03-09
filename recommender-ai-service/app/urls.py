from django.urls import path
from .views import RecommendBooks

urlpatterns = [
    path("recommendations/<int:customer_id>/", RecommendBooks.as_view(), name="recommend-books"),
]
