from django.db import models
from accounts.models import Store  # استيراد موديل المتجر من تطبيق الحسابات

class Product(models.Model):
    # ربط المنتج بالمتجر مباشرة؛ تم إتاحة null=True لتفادي مشاكل الميجريشن
    store = models.ForeignKey(
        Store, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name="المتجر",
        null=True,
        blank=True
    )
    
    name = models.CharField(max_length=255, verbose_name="اسم المنتج")
    description = models.TextField(blank=True, null=True, verbose_name="وصف المنتج")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    stock = models.IntegerField(default=0, verbose_name="الكمية المتاحة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    def __str__(self):
        return f"{self.name} - ({self.store.name if self.store else 'بدون متجر'})"