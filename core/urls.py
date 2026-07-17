from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from orders.views import stripe_webhook  # استيراد الدالة مباشرة هنا

urlpatterns = [
    # 🎯 الرابط المباشر والسريع للـ Webhook (بدون أي وسيط)
    path('api/orders/webhook/', stripe_webhook, name='stripe_webhook'),

    # الروابط الأساسية للمشروع
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # روابط التطبيقات الأخرى
    path('api/accounts/', include('accounts.urls')),   
    path('api/products/', include('products.urls')),   
    path('api/cart/', include('cart.urls')),           
    path('api/orders/', include('orders.urls')), 
]