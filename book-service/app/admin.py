from django.contrib import admin
from app.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "price", "stock")
    search_fields = ("title", "author")
    list_filter = ("author",)
    ordering = ("title",)
