from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:product_id>/', views.cart_add_detail, name='cart_add_detail'),
    path('', views.cart_view, name='cart_view'),
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("api/subcategories/", views.subcategories_api, name="subcategories_api"),
    path("place/", views.checkout, name="place_order"),



]
