from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from products.models import Product, Category, SubCategory
from .models import Cart, CartItem



@login_required
def cart_add_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart, _ = Cart.objects.get_or_create(
        user=request.user,
        is_active=True
    )

    # next is ONLY for cancel
    next_url = (
        request.GET.get("next")
        or request.META.get("HTTP_REFERER")
        or "/"
    )

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            item.quantity += quantity
            item.save()

        # ✅ ALWAYS go to cart after add
        return redirect("cart_view")

    return render(request, "order/cart_add_detail.html", {
        "product": product,
        "cart": cart,
        "next": next_url,   # used ONLY by Cancel
    })

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(
        user=request.user,
        is_active=True
    )

    # filters
    category_id = request.GET.get("category")
    subcategory_id = request.GET.get("subcategory")
    query = request.GET.get("q")

    products = Product.objects.all()

    if category_id:
        products = products.filter(category__category_id=category_id)

    if subcategory_id:
        products = products.filter(category_id=subcategory_id)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    categories = Category.objects.all()
    subcategories = (
        SubCategory.objects.filter(category_id=category_id)
        if category_id else SubCategory.objects.none()
    )

    context = {
        "cart": cart,
        "items": cart.items.select_related("product"),
        "products": products[:12],
        "categories": categories,
        "subcategories": subcategories,
        "selected_category": category_id,
        "selected_subcategory": subcategory_id,
        "query": query,
    }
    return render(request, "order/cart_view.html", context)

@login_required
def cart_add(request, product_id):
    cart, _ = Cart.objects.get_or_create(
        user=request.user if request.user.is_authenticated else None,
        is_active=True
    )

    product = get_object_or_404(Product, id=product_id)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if not created:
        item.quantity += 1
    item.save()

    return redirect("cart_view")

@login_required
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect("cart_view")

def subcategories_api(request):
    category_id = request.GET.get("category_id")
    subcategories = []

    if category_id:
        subcategories_qs = SubCategory.objects.filter(category_id=category_id)
        subcategories = [{"id": s.id, "name": s.name} for s in subcategories_qs]

    return JsonResponse({"subcategories": subcategories})


