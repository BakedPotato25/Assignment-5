from django.urls import path
from .views import CartCreate, AddCartItem, UpdateCartItem, ViewCart

urlpatterns = [
    path("carts/",                   CartCreate.as_view(),      name="cart-create"),
    path("carts/<int:customer_id>/", ViewCart.as_view(),        name="view-cart"),
    path("cart-items/",              AddCartItem.as_view(),     name="add-cart-item"),
    path("cart-items/<int:item_id>/",UpdateCartItem.as_view(),  name="update-cart-item"),
]
