from .models import Category
from order.utils import get_or_create_cart
from django.db.models import Sum

def navbar_data(request):
    # Only active categories
    categories = Category.objects.filter(is_active=True).prefetch_related(
        'subcategory_set'
    )

    # For each category, only include active subcategories
    for category in categories:
        category.active_subcategories = category.subcategory_set.filter(is_active=True)

    return {
        "nav_categories": categories
    }

def cart_context(request):
    cart = get_or_create_cart(request)

    total_items = 0
    if cart:
        total_items = cart.items.aggregate(total=Sum("quantity"))["total"] or 0

    return {
        "cart": cart,
        "cart_count": total_items
    }
