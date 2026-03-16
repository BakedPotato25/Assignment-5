from rest_framework import serializers
from .models import Order, OrderItem, SagaStepLog


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "book_id", "quantity"]


class SagaStepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SagaStepLog
        fields = ["id", "step", "from_status", "to_status", "success", "detail", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    saga_logs = SagaStepLogSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer_id", "total_amount", "status", "created_at", "items", "saga_logs"]
        read_only_fields = ["status", "created_at"]
