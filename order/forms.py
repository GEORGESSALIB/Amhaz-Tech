from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "customer_name",
            "customer_email",
            "customer_phone",
            "district",
            "customer_address",
            "order_type",
        ]
