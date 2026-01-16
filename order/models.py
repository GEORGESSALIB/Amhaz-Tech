from django.conf import settings
from django.db import models
from products.models import Product


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # 👇 NEW: for guest users
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def total_price(self):
        return sum(
            item.quantity * item.product.price
            for item in self.items.select_related('product')
        )

    def __str__(self):
        owner = self.user.username if self.user else self.session_key
        return f"Cart {self.id} ({owner})"

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # 👇 NEW: customer info (for guests + logged users)
    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30)
    DISTRICT_CHOICES = [
        ("akkar", "Akkar - عكار"),
        ("aley", "Aley - عاليه"),
        ("baabda", "Baabda - بعبدا"),
        ("baalbek", "Baalbek - بعلبك"),
        ("batroun", "Batroun - البترون"),
        ("beirut", "Beirut - بيروت"),
        ("bint_jbeil", "Bint Jbeil - بنت جبيل"),
        ("bsharri", "Bsharri - بشري"),
        ("byblos", "Byblos - جبيل"),
        ("chouf", "Chouf - الشوف"),
        ("danniyeh", "Danniyeh - الضنية"),
        ("hasbaya", "Hasbaya - حاصبيا"),
        ("hermel", "Hermel - الهرمل"),
        ("jezzine", "Jezzine - جزين"),
        ("keserwan", "Keserwan - كسروان"),
        ("koura", "Koura - الكورة"),
        ("marjeyoun", "Marjeyoun - مرجعيون"),
        ("matn", "Matn - المتن"),
        ("nabatieh", "Nabatieh - النبطية"),
        ("rashaya", "Rashaya - راشيا"),
        ("sidon", "Sidon - صيدا"),
        ("tripoli", "Tripoli - طرابلس"),
        ("tyre", "Tyre - صور"),
        ("western_bekaa", "Western Bekaa - البقاع الغربي"),
        ("zahle", "Zahle - زحلة"),
        ("zgharta", "Zgharta - زغرتا"),
    ]

    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, blank=True)
    customer_address = models.TextField(blank=True)


    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('not_confirmed', 'Not Confirmed'),
            ('confirmed', 'Confirmed'),
        ]
    )

    order_type = models.CharField(
        max_length=20,
        choices=[
            ('delivery', 'Delivery'),
            ('take_from_store', 'Take From Store'),
        ],
        default='delivery'
    )

    def __str__(self):
        return f"Order {self.id} - {self.customer_name}"

