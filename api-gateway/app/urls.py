from django.urls import path
from . import views

urlpatterns = [
    path("health/",                        views.health_view,        name="gateway_health"),
    path("metrics/",                       views.metrics_view,       name="gateway_metrics"),
    path("",                              views.book_list,          name="home"),
    path("books/",                        views.book_list,          name="book_list"),
    # Cart
    path("cart/",                         views.view_cart,          name="view_cart"),
    path("cart/add/",                     views.add_to_cart,        name="add_to_cart"),
    path("cart/update/<int:item_id>/",    views.update_cart_item,   name="update_cart_item"),
    path("cart/checkout/",               views.checkout,           name="checkout"),
    # Auth
    path("login/",                        views.login_view,         name="login"),
    path("logout/",                       views.logout_view,        name="logout"),
    path("register/",                     views.register_view,      name="register"),
    # Staff: book management
    path("staff/books/",                 views.staff_books,        name="staff_books"),
    path("staff/books/add/",             views.staff_add_book,     name="staff_add_book"),
    path("staff/books/<int:book_id>/edit/",   views.staff_edit_book,   name="staff_edit_book"),
    path("staff/books/<int:book_id>/delete/", views.staff_delete_book, name="staff_delete_book"),
    # Reviews
    path("reviews/submit/",              views.submit_review,      name="submit_review"),
]
