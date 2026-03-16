from django.contrib import admin
from .models import Order, OrderItem, SagaStepLog


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id", "customer_id", "total_amount", "status", "created_at")
	search_fields = ("id", "customer_id", "status")
	list_filter = ("status", "created_at")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ("id", "order", "book_id", "quantity")
	search_fields = ("order__id", "book_id")


@admin.register(SagaStepLog)
class SagaStepLogAdmin(admin.ModelAdmin):
	list_display = ("id", "order", "step", "from_status", "to_status", "success", "created_at")
	search_fields = ("order__id", "step", "from_status", "to_status")
	list_filter = ("success", "created_at")
