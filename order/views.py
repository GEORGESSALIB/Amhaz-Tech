from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from products.models import Product, Category, SubCategory
from .forms import CheckoutForm
from .models import Cart, CartItem, Order
from products.models import StockMovement
from .utils import build_whatsapp_link, get_or_create_cart


def cart_add_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # ✅ unified cart getter (works for user + guest)
    cart = get_or_create_cart(request)

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

        return redirect("cart_view")

    return render(request, "order/cart_add_detail.html", {
        "product": product,
        "cart": cart,
        "next": next_url,
    })

def cart_view(request):
    cart = get_or_create_cart(request)

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


def checkout(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product")

    if not items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart_view")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user if request.user.is_authenticated else None
            order.status = "confirmed"
            order.save()
            return finalize_order(request, order, cart)

    else:
        form = CheckoutForm()

        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)

            form.fields["customer_name"].widget.attrs["value"] = (
                    request.user.get_full_name() or request.user.username
            )
            form.fields["customer_email"].widget.attrs["value"] = request.user.email
            form.fields["customer_phone"].widget.attrs["value"] = profile.phone if profile else ""

            # ✅ Correct way for select/textarea
            form.initial["district"] = profile.district if profile else ""
            form.initial["customer_address"] = profile.customer_address if profile else ""
            form.fields["order_type"].widget.attrs["value"] = "delivery"

    return render(request, "order/checkout.html", {
        "form": form,
        "cart": cart,
        "items": items,
    })


def finalize_order(request, order, cart):
    items = cart.items.select_related("product")

    customer_name = order.customer_name

    message_lines = [
        f"🧾 New Order #{order.id}",
        f"Type: {order.get_order_type_display()}",
        "",
        "Items:",
    ]

    for item in items:
        product = item.product

        if product.cached_quantity < item.quantity:
            messages.error(request, f"Not enough stock for {product.name}")
            return redirect("cart_view")

        product.cached_quantity -= item.quantity
        product.save()

        StockMovement.objects.create(
            product=product,
            change=-item.quantity,
            reason=f"Order #{order.id} from {customer_name}",
        )

        message_lines.append(f"- {product.name} x{item.quantity}")

    message_lines.append("")
    message_lines.append(f"👤 Customer: {customer_name}")
    message_lines.append(f"📞 Phone: {order.customer_phone}")
    message_lines.append(f"📍 Address: {order.customer_address}")

    whatsapp_message = "\n".join(message_lines)

    # Reset cart
    cart.items.all().delete()
    cart.is_active = False
    cart.save()

    # New cart
    if request.user.is_authenticated:
        Cart.objects.create(user=request.user)
    else:
        new_cart = Cart.objects.create()
        request.session["cart_id"] = new_cart.id

    messages.success(request, "Order placed successfully!")

    wa_link = build_whatsapp_link(
        phone="96103291033",
        message=whatsapp_message
    )

    return redirect(wa_link)



