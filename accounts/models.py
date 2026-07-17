from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Store(models.Model):
    name = models.CharField(max_length=255)
    # الـ slug هو الرابط الفرعي للمتجر (مثال: saas.com/stores/my-shop-name)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MerchantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='merchant_profile')
    # ربط التاجر بالمتجر الخاص به
    store = models.OneToOneField(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='merchant')
    shop_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default='merchant')

    def __str__(self):
        return f"{self.user.username} - {self.shop_name}"