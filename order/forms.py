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
            "building_name",
            "order_type",
        ]
        labels = {
            "customer_name": "Full Name",
            "customer_email": "Email Address",
            "customer_phone": "Phone Number",
            "district": "District",
            "customer_address": "Delivery Address",
            "building_name": "Building Name",
            "order_type": "Payment Method",
        }