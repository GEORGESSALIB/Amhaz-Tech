from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('subcategory/<int:sub_id>/', views.products_by_subcategory, name='products_by_subcategory'),
    path('search/', views.product_search, name='product_search'),
    path('subcategory/<int:subcategory_id>/product/add/', views.product_add, name='product_add'),
    path('product/<int:product_id>/add_stock/', views.add_stock, name='add_stock'),
    path("product/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path('product/<int:product_id>/remove_stock/', views.remove_stock, name='remove_stock'),
    path("ajax/subcategories/", views.ajax_subcategories, name="ajax_subcategories"),
    path("ajax/products/", views.ajax_products, name="ajax_products"),
    path('categories/', views.category_list, name='category_list'),
    path('category/add/', views.category_add, name='category_add'),
    path('category/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('category/<int:category_id>/subcategories/', views.subcategory_list_by_category,
         name='subcategory_list_by_category'),
    path('category/<int:category_id>/subcategory/add/', views.subcategory_add, name='subcategory_add'),
    path('subcategory/<int:subcategory_id>/edit/', views.subcategory_edit, name='subcategory_edit'),


]
