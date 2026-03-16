from django.db import models


class Order(models.Model):
    class SagaStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        PAYMENT_RESERVED = "Payment Reserved", "Payment Reserved"
        SHIPPING_RESERVED = "Shipping Reserved", "Shipping Reserved"
        CONFIRMED = "Confirmed", "Confirmed"
        PAYMENT_FAILED = "Payment Failed", "Payment Failed"
        SHIPPING_FAILED = "Shipping Failed", "Shipping Failed"
        COMPENSATED = "Compensated", "Compensated"

    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=50,
        choices=SagaStatus.choices,
        default=SagaStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order({self.id}, customer={self.customer_id}, status={self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book_id = models.IntegerField()
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"OrderItem(order={self.order_id}, book={self.book_id})"


class SagaStepLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="saga_logs")
    step = models.CharField(max_length=100)
    from_status = models.CharField(max_length=50, blank=True, default="")
    to_status = models.CharField(max_length=50)
    success = models.BooleanField(default=True)
    detail = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"SagaStepLog(order={self.order_id}, step={self.step}, "
            f"to={self.to_status}, success={self.success})"
        )
