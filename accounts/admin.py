from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# تخصيص شكل جدول المستخدمين ليعرض الحقول الجديدة
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ('SaaS Custom Fields', {'fields': ('role', 'phone_number', 'shop_name')}),
    )

# تسجيل النموذج في لوحة التحكم
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)