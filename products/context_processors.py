from .models import Category

def navbar_data(request):
    return {
        "nav_categories": Category.objects.prefetch_related('subcategory_set')
    }
