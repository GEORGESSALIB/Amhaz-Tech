from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_view, name='cart_view'),
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("place/", views.checkout, name="place_order"),
    path("cart/update-quantity/", views.cart_update_quantity, name="cart_update_quantity"),
    path("confirmed/", views.confirmed_orders, name="confirmed_orders"),
    path("<int:order_id>/return/", views.return_order, name="return_order"),
    path("success/", views.order_success, name="order_success"),

]
