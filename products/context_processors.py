from .models import Category
from order.utils import get_or_create_cart


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

    return {
        "cart": cart,
        "cart_count": cart.items.count() if cart else 0
    }

