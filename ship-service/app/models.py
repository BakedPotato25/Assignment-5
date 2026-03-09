from django.db import models


class Shipment(models.Model):
    order_id = models.IntegerField()
    address = models.CharField(max_length=500)
    method = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default="Processing")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipment(order={self.order_id}, status={self.status})"
