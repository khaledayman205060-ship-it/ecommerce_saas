from django.urls import path
from . import views

app_name = 'orders'  # تأكد من مطابقة الـ namespace إذا كنت تستخدمه في مشروعك

urlpatterns = [
    # 📊 لوحة تحكم العميل (Dashboard)
    path('dashboard/', views.customer_dashboard, name='customer-dashboard'),
    
    # 💳 صفحة إتمام الدفع (Checkout Page)
    path('checkout-page/', views.checkout_page, name='checkout-page'),
    
    # 🔑 إنشاء طلب الدفع في Stripe (Create Payment Intent)
    path('checkout/create-intent/', views.create_payment_intent, name='create-payment-intent'),
    
    # 🛡️ استقبال إشارات ومناسبات الدفع من Stripe (Webhook)
    path('webhook/', views.stripe_webhook, name='stripe-webhook'),
]