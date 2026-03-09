from django.db import models


class Cart(models.Model):
    customer_id = models.IntegerField(unique=True)

    def __str__(self):
        return f"Cart(customer={self.customer_id})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    book_id = models.IntegerField()
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ("cart", "book_id")

    def __str__(self):
        return f"CartItem(cart={self.cart_id}, book={self.book_id}, qty={self.quantity})"
