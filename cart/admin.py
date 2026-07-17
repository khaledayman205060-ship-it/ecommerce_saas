from django.contrib import admin
# استورد الموديلات الخاصة بالسلة (تأكد من كتابة مسار الاستيراد الصحيح حسب مشروعك)
from .models import Cart, CartItem 

admin.site.register(Cart)
admin.site.register(CartItem)