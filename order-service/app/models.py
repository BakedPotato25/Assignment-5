from django.db import models


class Order(models.Model):
    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order({self.id}, customer={self.customer_id}, status={self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book_id = models.IntegerField()
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"OrderItem(order={self.order_id}, book={self.book_id})"
