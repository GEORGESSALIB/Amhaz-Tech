from django.contrib import admin
from .models import Product, Category, StockMovement, SubCategory

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(StockMovement)
admin.site.register(SubCategory)