from django.urls import path
from .views import home, products_by_subcategory, dashboard, add_stock, remove_stock, product_add, product_edit

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('subcategory/<int:sub_id>/', products_by_subcategory, name='products_by_subcategory'),
    path('subcategory/<int:subcategory_id>/product/add/', product_add, name='product_add'),
    path('product/<int:product_id>/add_stock/', add_stock, name='add_stock'),
    path("product/<int:pk>/edit/", product_edit, name="product_edit"),
    path('product/<int:product_id>/remove_stock/', remove_stock, name='remove_stock'),

]
