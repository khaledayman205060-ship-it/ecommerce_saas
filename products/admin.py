from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # عرض الحقول الجديدة في لوحة التحكم (استبدال merchant بـ store)
    list_display = ('name', 'store', 'price', 'stock', 'created_at')
    
    # إضافة فلاتر للبحث والتصفية بحسب المتجر
    list_filter = ('store', 'created_at')
    
    # تمكين البحث باسم المنتج أو اسم المتجر
    search_fields = ('name', 'store__name')