from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from products.models import Product, Category, SubCategory
from .forms import CheckoutForm
from .models import Cart, CartItem, Order, OrderItem
from products.models import StockMovement
from .utils import build_whatsapp_link, get_or_create_cart
from amhaz import settings


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
    if request.method != "POST":
        return HttpResponseRedirect(reverse("cart_view"))

    product = get_object_or_404(Product, id=product_id)

    # ❌ Do not add if out of stock
    if product.cached_quantity <= 0:
        return HttpResponseRedirect(reverse("cart_view"))

    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": 1}
    )

    if not created:
        # ❌ Respect stock limit
        if item.quantity < product.cached_quantity:
            item.quantity += 1
            item.save()

    return HttpResponseRedirect(reverse("cart_view"))

def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect("cart_view")

from django.db import transaction

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
            form.fields["customer_phone"].widget.attrs["value"] = (
                profile.phone if profile else ""
            )

            form.initial["district"] = profile.district if profile else ""
            form.initial["customer_address"] = profile.customer_address if profile else ""
            form.fields["order_type"].widget.attrs["value"] = "delivery"

    return render(request, "order/checkout.html", {
        "form": form,
        "cart": cart,
        "items": items,
    })


@transaction.atomic
def finalize_order(request, order, cart):
    items = cart.items.select_related("product")
    customer_name = order.customer_name

    message_lines = [
        f"New Order #{order.id}",
        f"Type: {order.get_order_type_display()}",
        "",
        "Items:",
    ]

    for item in items:
        product = item.product

        if product.cached_quantity < item.quantity:
            messages.error(request, f"Not enough stock for {product.name}")
            return redirect("cart_view")

        # ✅ CREATE ORDER ITEM
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            price=product.price,
        )

        # ✅ UPDATE STOCK
        product.cached_quantity -= item.quantity
        product.save(update_fields=["cached_quantity"])

        # ✅ STOCK MOVEMENT
        StockMovement.objects.create(
            product=product,
            change=-item.quantity,
            reason=f"Order #{order.id} from {customer_name}",
        )

        message_lines.append(f"- {product.name} x{item.quantity}")

    message_lines.extend([
        "",
        f"Customer: {customer_name}",
        f"Phone: {order.customer_phone}",
        f"District: {order.get_district_display()}",
        f"Address: {order.customer_address}",
    ])

    email_body = "\n".join(message_lines)

    # ✅ SEND EMAIL
    send_mail(
        subject=f"New Order #{order.id}",
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[
            settings.DEFAULT_FROM_EMAIL,  # store/admin
            order.customer_email,         # optional: customer copy
        ],
        fail_silently=False,
    )

    # ✅ RESET CART
    cart.items.all().delete()
    cart.is_active = False
    cart.save(update_fields=["is_active"])

    # ✅ CREATE NEW CART
    if request.user.is_authenticated:
        Cart.objects.create(user=request.user)
    else:
        new_cart = Cart.objects.create()
        request.session["cart_id"] = new_cart.id

    messages.success(request, "Order placed successfully! Confirmation email sent.")

    return redirect("order_success")


@require_POST
def cart_update_quantity(request):
    item_id = request.POST.get("item_id")
    action = request.POST.get("action")

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    product = item.product
    max_stock = product.cached_quantity

    if action == "increase":
        # ❌ Do not exceed available stock
        if item.quantity < max_stock:
            item.quantity += 1
        else:
            return JsonResponse({
                "blocked": "max",
                "quantity": item.quantity,
                "max_stock": max_stock,
                "cart_total": item.cart.total_price(),
            })

    elif action == "decrease":
        item.quantity -= 1

        # ✅ Quantity = 0 → remove item
        if item.quantity <= 0:
            item.delete()
            return JsonResponse({
                "removed": True,
                "cart_total": item.cart.total_price(),
            })

    item.save()

    return JsonResponse({
        "blocked": False,
        "quantity": item.quantity,
        "max_stock": max_stock,
        "cart_total": item.cart.total_price(),
    })


# Only staff can access
def staff_required(user):
    return user.is_staff


@login_required
@user_passes_test(staff_required)
def confirmed_orders(request):
    today = timezone.localdate()
    from_date = request.GET.get("from", today.strftime("%Y-%m-%d"))
    to_date = request.GET.get("to", today.strftime("%Y-%m-%d"))
    order_number = request.GET.get("order_number", "")

    orders = Order.objects.filter(status="confirmed")

    if from_date:
        orders = orders.filter(created_at__date__gte=from_date)
    if to_date:
        orders = orders.filter(created_at__date__lte=to_date)
    if order_number:
        orders = orders.filter(id=order_number)

    context = {
        "orders": orders.order_by("-created_at"),
        "from_date": from_date,
        "to_date": to_date,
        "order_number": order_number,
    }
    return render(request, "order/confirmed_orders.html", context)


@login_required
@user_passes_test(staff_required)
def return_order(request, order_id):
    """
    Return/discard an order:
    - Re-add all items to stock
    - Log stock movement
    - Mark order as returned
    """

    order = get_object_or_404(Order, id=order_id, status="confirmed")

    order_items = order.items.select_related("product")

    for item in order_items:
        product = item.product
        quantity = item.quantity

        # ✅ Re-add stock
        product.cached_quantity += quantity
        product.save(update_fields=["cached_quantity"])

        # ✅ Stock movement log
        StockMovement.objects.create(
            product=product,
            change=quantity,
            reason=f"Order #{order.id} returned"
        )

    # ✅ Mark order as returned
    order.status = "returned"
    order.save(update_fields=["status"])

    messages.success(request, f"Order #{order.id} returned successfully.")

    return redirect("confirmed_orders")

def order_success(request):
    return render(request, "order/success.html")



