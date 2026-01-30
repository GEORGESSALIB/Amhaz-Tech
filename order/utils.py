from .models import Cart

def get_or_create_cart(request):
    # Logged-in user
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            is_active=True
        )
        return cart

    # Guest user (session-based)
    cart_id = request.session.get("cart_id")
    cart = None

    if cart_id:
        cart = Cart.objects.filter(id=cart_id, is_active=True).first()

    if not cart:
        cart = Cart.objects.create(is_active=True)
        request.session["cart_id"] = cart.id

    return cart
