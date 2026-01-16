from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

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

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=True)
    district = forms.ChoiceField(choices=DISTRICT_CHOICES, required=True)
    village = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "phone", "district", "village")

    def clean_email(self):
        email = self.cleaned_data.get("email").lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        if commit:
            user.save()
            # Save the extra fields to UserProfile
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
                district=self.cleaned_data["district"],
                village=self.cleaned_data["village"]
            )
        return user