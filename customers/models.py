from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(max_length=30, blank=True)
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
    customer_address = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.user.username} profile"

