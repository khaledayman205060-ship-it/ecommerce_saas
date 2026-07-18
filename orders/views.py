import os
import stripe
import environ
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Order  # تأكد أن اسم الموديل عندك في التطبيق هو Order

# 👇 استدعاء دالة إرسال الفاتورة الـ PDF من ملف الـ utils المساعد
from .utils import send_invoice_email

# 1. إعداد مكتبة environ لقراءة ملف الـ .env المخفي
env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# 2. قراءة الـ Keys من ملف الـ .env تلقائياً
stripe.api_key = env("STRIPE_SECRET_KEY")
endpoint_secret = env("STRIPE_WEBHOOK_SECRET")


def send_order_confirmation_email(order):
    """
    دالة تقوم بإنشاء فاتورة HTML وإرسالها لإيميل العميل تلقائياً عند نجاح الدفع
    """
    try:
        customer = order.customer
        if not customer or not customer.email:
            print("⚠️ Cannot send email: Customer or email is missing.")
            return

        subject = f"🎉 Order Confirmation - Order #{order.id}"
        
        # تجهيز البيانات التي سيتم عرضها داخل قالب الفاتورة الـ HTML
        context = {
            'customer_name': customer.username,
            'order_id': order.id,
            'total_price': order.total_price,
            'order_items': order.items.all() if hasattr(order, 'items') else order.orderitem_set.all(),
        }

        # 1. رندر لملف الـ HTML
        html_message = render_to_string('emails/order_confirmation.html', context)
        
        # 2. عمل نسخة نصية احتياطية (text version)
        plain_message = strip_tags(html_message)

        # 3. إنشاء الإيميل وإرساله للعميل
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=None,  # سيستخدم الـ DEFAULT_FROM_EMAIL تلقائياً من الـ settings
            to=[customer.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        print(f"📧 Confirmation email sent successfully to {customer.email}!")
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")


def send_payment_failed_email(order, error_message):
    """
    إرسال إيميل تنبيهي للعميل في حال فشل عملية الدفع لتشجيعه على المحاولة مجدداً
    """
    try:
        customer = order.customer
        if not customer or not customer.email:
            print("⚠️ Cannot send failure email: Customer or email is missing.")
            return

        subject = f"⚠️ Payment Failed for Order #{order.id}"
        message = (
            f"Hi {customer.username},\n\n"
            f"We tried to process your payment of ${order.total_price:.2f} for Order #{order.id}, "
            f"but the transaction could not be completed.\n\n"
            f"Reason of failure: {error_message}\n\n"
            f"Please try again or use a different card.\n\n"
            f"Best regards,\nEcommerce SaaS Team"
        )
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=None,
            to=[customer.email]
        )
        email.send()
        print(f"📧 Failure email sent successfully to {customer.email}.")
    except Exception as e:
        print(f"❌ Failed to send failure email: {str(e)}")


@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])  # دعم التوكن والجلسة النشطة
@permission_classes([IsAuthenticated])  # 🔒 حماية الـ Endpoint: لا بد من تسجيل الدخول
def create_payment_intent(request):
    try:
        order_id = request.data.get('order_id')
        
        if not order_id:
            return JsonResponse({'error': 'order_id is required'}, status=400)
            
        try:
            # تأمين إضافي: التحقق من أن الطلب يخص المستخدم الحالي الذي أرسل الطلب
            order = Order.objects.get(id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found or unauthorized'}, status=404)
            
        total_amount = int(order.total_price * 100)
        
        if total_amount <= 0:
            return JsonResponse({'error': 'Order total amount must be greater than 0'}, status=400)

        # إنشاء طلب الدفع في Stripe مع ربطه بمعلومات العميل الحقيقي
        intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency='usd',
            metadata={
                'order_id': order.id,
                'customer_id': request.user.id,
                'customer_email': request.user.email,
            }
        )
        
        order.stripe_payment_intent_id = intent.id
        order.save()
        
        return JsonResponse({
            'clientSecret': intent.client_secret,
            'amount_to_pay': order.total_price
        }, status=200)
        
    except Exception as e:
        print("Stripe Error:", str(e))
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@api_view(['POST'])             
@authentication_classes([])     
@permission_classes([])  # الـ Webhook يجب أن يظل مفتوحاً لأن Stripe هو من يرسل الطلب
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    # 🛡️ محاولة التحقق من توقيع الطلب بشكل آمن
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print("✅ Webhook Signature Verified Successfully!")
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        # ⚠️ حماية مرنة للبيئة المحلية (Local) فقط:
        from django.conf import settings
        if settings.DEBUG:
            print(f"⚠️ Webhook Signature Verification Failed ({str(e)}), but proceeding because DEBUG=True...")
            try:
                event = json.loads(payload.decode('utf-8'))
            except Exception as json_err:
                print("❌ Webhook JSON Parse Error:", str(json_err))
                return HttpResponse(status=400)
        else:
            # لو على السيرفر الحقيقي (Production) والـ Signature غلط، ارفض فوراً لحمايتك من الاختراق!
            print("❌ Webhook Error: Invalid Signature! Request rejected in Production.")
            return HttpResponse(status=400)

    # جلب نوع الحدث والبيانات الخاصة به ديناميكياً
    event_type = event.get('type') if isinstance(event, dict) else event.type
    event_data = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
    
    # ------------------------------------------------------------
    # 1️⃣ الحالة الأولى: نجاح عملية الدفع بنجاح (Payment Succeeded)
    # ------------------------------------------------------------
    if event_type == 'payment_intent.succeeded':
        intent = event_data
        order_id = intent.get('metadata', {}).get('order_id')
        
        if order_id:
            try:
                # تحديث حالة الـ Order لـ مدفوع[cite: 1]
                order = Order.objects.get(id=order_id)
                order.status = 'paid'
                order.save()
                
                print(f"\n🎉🎉🎉 SUCCESS: Order #{order.id} has been marked as PAID!")

                # تقليل كمية المنتجات في المخزن (Stock/Inventory)[cite: 1]
                order_items = []
                if hasattr(order, 'items'):
                    order_items = order.items.all()
                elif hasattr(order, 'orderitem_set'):
                    order_items = order.orderitem_set.all()

                for item in order_items:
                    product = item.product
                    if hasattr(product, 'stock') and product.stock is not None:
                        product.stock -= item.quantity
                        product.save()
                        print(f"📉 Stock updated for [{product.name}]: Remaining stock ({product.stock})")
                    elif hasattr(product, 'quantity') and product.quantity is not None:
                        product.quantity -= item.quantity
                        product.save()
                        print(f"📉 Quantity updated for [{product.name}]: Remaining ({product.quantity})")

                # تفريغ سلة المشتريات (Clear User Cart)[cite: 1]
                customer = order.customer
                if customer and hasattr(customer, 'cart'):
                    try:
                        customer.cart.items.all().delete()
                        print(f"🛒 Cart cleared successfully for user: {customer.username}")
                    except Exception as cart_err:
                        print(f"⚠️ Could not clear cart: {str(cart_err)}")

                # إرسال إيميل الفاتورة التلقائي للعميل 📧[cite: 1]
                send_order_confirmation_email(order)

                # 👇👇 تشغيل نظام إرسال فاتورة الـ PDF التلقائية (الخطوة الرابعة) 👇👇
                try:
                    # نمرر الطلب والمنتجات للدالة التي تقوم بالتوليد والإرسال
                    send_invoice_email(order, order_items)
                    print(f"📄 Automated PDF Invoice sent successfully for Order #{order.id}!")
                except Exception as pdf_email_err:
                    print(f"⚠️ Webhook caught an error while sending PDF Invoice: {str(pdf_email_err)}")

                print(f"🏁 Order #{order.id} lifecycle completed successfully!\n")
                
            except Order.DoesNotExist:
                print(f"⚠️ Error: Order {order_id} not found in database.")

    # ------------------------------------------------------------
    # 2️⃣ الحالة الثانية: فشل عملية الدفع (Payment Failed)
    # ------------------------------------------------------------
    elif event_type == 'payment_intent.payment_failed':
        intent = event_data
        order_id = intent.get('metadata', {}).get('order_id')
        error_message = intent.get('last_payment_error', {}).get('message', 'Unknown transaction error')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.status = 'failed'  # تحديث حالة الأوردر لـ فاشل[cite: 1]
                order.save()
                
                print(f"\n❌❌❌ PAYMENT FAILED: Order #{order.id} marked as FAILED. Reason: {error_message}")
                
                # إرسال إيميل الفشل التنبيهي للعميل 📧[cite: 1]
                send_payment_failed_email(order, error_message)
                
                print(f"🏁 Order #{order.id} lifecycle stopped due to failure.\n")
            except Order.DoesNotExist:
                print(f"⚠️ Error: Order {order_id} not found in database.")

    # ------------------------------------------------------------
    # 3️⃣ الحالة الثالثة: إلغاء عملية الدفع (Payment Canceled)
    # ------------------------------------------------------------
    elif event_type == 'payment_intent.canceled':
        intent = event_data
        order_id = intent.get('metadata', {}).get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.status = 'canceled'  # تحديث حالة الأوردر لـ ملغي[cite: 1]
                order.save()
                print(f"\n🚫 PAYMENT CANCELED: Order #{order.id} marked as CANCELED.\n")
            except Order.DoesNotExist:
                print(f"⚠️ Error: Order {order_id} not found.")

    return HttpResponse(status=200)


@login_required  # 🔒 حماية الصفحة: لو اليوزر مش مسجل دخول، يتم تحويله لصفحة الـ Login تلقائياً[cite: 1]
def checkout_page(request):
    publishable_key = env("STRIPE_PUBLISHABLE_KEY")
    
    # 1️⃣ جلب المستخدم الحالي الفعلي المسجل في المتصفح[cite: 1]
    user = request.user
    
    # 2️⃣ جلب سلة المشتريات الخاصة باليوزر الحالي وحساب الإجمالي الحقيقي ديناميكياً[cite: 1]
    total_price = 0.00
    cart_items = []
    
    if hasattr(user, 'cart') and user.cart:
        for item in user.cart.items.all():
            total_price += float(item.product.price * item.quantity)
            cart_items.append(item)
    
    # منع الدخول إذا كانت السلة فارغة مع توفير زر للعودة للداشبورد بأمان[cite: 1]
    if not cart_items:
        return HttpResponse(
            "<div style='text-align:center; margin-top:50px; font-family:sans-serif;'>"
            "<h2 style='color:#d9534f;'>❌ سلة مشترياتك فارغة!</h2>"
            "<p style='color:#666; margin-bottom: 25px;'>يرجى إضافة منتجات إلى السلة أولاً قبل الانتقال لصفحة إتمام الدفع.</p>"
            "<a href='/api/orders/dashboard/' style='background:#5469d4; color:white; padding:10px 20px; border-radius:5px; text-decoration:none; font-weight:bold;'>Go to Dashboard</a>"
            "</div>"
        )
    
    # 3️⃣ إنشاء الأوردر الحقيقي في قاعدة البيانات مربوط باليوزر الحالي كـ Unpaid[cite: 1]
    new_order = Order.objects.create(
        customer=user,
        total_price=total_price,
        status='unpaid'
    )
    
    # 4️⃣ نقل محتويات السلة إلى الأوردر (OrderItem)[cite: 1]
    for cart_item in cart_items:
        try:
            from .models import OrderItem
            OrderItem.objects.create(
                order=new_order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        except Exception as e:
            print(f"⚠️ Could not copy cart item to order: {str(e)}")

    # 5️⃣ رندر صفحة الـ HTML مع البيانات الحقيقية بالكامل[cite: 1]
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Real Secure Checkout</title>
        <script src="https://js.stripe.com/v3/"></script>
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f4f6f8; margin: 0; }}
            .payment-card {{ background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }}
            #card-element {{ border: 1px solid #ccc; padding: 12px; border-radius: 5px; margin-bottom: 20px; background: #fff; }}
            button {{ width: 100%; padding: 12px; background: #5469d4; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; font-weight: bold; }}
            button:disabled {{ background: #a2a2a2; }}
            #message {{ margin-top: 15px; text-align: center; font-weight: bold; }}
            .price-tag {{ text-align: center; font-size: 24px; color: #333; margin-bottom: 20px; font-weight: bold; }}
            .cart-summary {{ background: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 14px; }}
        </style>
    </head>
    <body>
    <div class="payment-card">
        <h2 style="text-align: center; margin-bottom: 5px;">Secure Checkout</h2>
        <p style="text-align: center; color: #666; margin: 0 0 15px 0;">Logged in as: <strong>{user.username}</strong></p>
        
        <div class="cart-summary">
            <strong>Order Items:</strong>
            <ul style="margin: 5px 0; padding-left: 20px;">
                {"".join([f"<li>{item.product.name} (x{item.quantity})</li>" for item in cart_items])}
            </ul>
        </div>

        <div class="price-tag">Total: ${total_price:.2f}</div>
        
        <form id="payment-form">
            <div id="card-element"></div>
            <button id="submit-btn" type="submit">Pay Now</button>
        </form>
        <div id="message"></div>
    </div>
    <script>
        const stripe = Stripe('{publishable_key}'); 
        const elements = stripe.elements();
        const cardElement = elements.create('card');
        cardElement.mount('#card-element');

        const form = document.getElementById('payment-form');
        const submitBtn = document.getElementById('submit-btn');
        const messageDiv = document.getElementById('message');

        form.addEventListener('submit', async (e) => {{
            e.preventDefault();
            submitBtn.disabled = true;
            messageDiv.innerText = "Processing...";

            try {{
                const response = await fetch('/api/orders/checkout/create-intent/', {{
                    method: 'POST',
                    headers: {{ 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }},
                    body: JSON.stringify({{
                        order_id: {new_order.id}
                    }})
                }});

                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Server Error');

                const result = await stripe.confirmCardPayment(data.clientSecret, {{
                    payment_method: {{ card: cardElement }}
                }});

                if (result.error) {{
                    messageDiv.style.color = "red";
                    messageDiv.innerText = "❌ " + result.error.message;
                    submitBtn.disabled = false;
                }} else if (result.paymentIntent.status === 'succeeded') {{
                    messageDiv.style.color = "green";
                    messageDiv.innerText = "🎉 Success! Redirecting to Dashboard...";
                    
                    setTimeout(() => {{
                        window.location.href = '/api/orders/dashboard/';
                    }}, 2000);
                }}
            }} catch (err) {{
                messageDiv.style.color = "red";
                messageDiv.innerText = "❌ " + err.message;
                submitBtn.disabled = false;
            }}
        }});

        function getCookie(name) {{
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {{
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {{
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }}
                }}
            }}
            return cookieValue;
        }}
    </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)


@login_required  # 🔒 تأمين الصفحة: يجب تسجيل الدخول لرؤية الطلبات الخاصة بك فقط[cite: 1]
def customer_dashboard(request):
    user = request.user
    
    # 1️⃣ جلب جميع طلبات المستخدم الحالي من الأحدث للأقدم[cite: 1]
    orders = Order.objects.filter(customer=user).order_by('-id')
    
    # 2️⃣ حساب الإحصائيات ديناميكياً[cite: 1]
    total_orders_count = orders.count()
    paid_orders_count = orders.filter(status='paid').count()
    failed_orders_count = orders.filter(status='failed').count()
    pending_orders_count = orders.filter(status='unpaid').count()
    
    total_spent = sum(float(order.total_price) for order in orders.filter(status='paid'))

    # 3️⃣ بناء محتوى الصفحة بـ Tailwind CSS مظهر عصري واحترافي[cite: 1]
    orders_rows = ""
    for order in orders:
        if order.status == 'paid':
            status_badge = '<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">✅ Paid</span>'
        elif order.status == 'failed':
            status_badge = '<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">❌ Failed</span>'
        elif order.status == 'canceled':
            status_badge = '<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">🚫 Canceled</span>'
        else:
            status_badge = '<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">⏳ Unpaid</span>'

        items_list = []
        order_items = order.items.all() if hasattr(order, 'items') else order.orderitem_set.all()
        for item in order_items:
            items_list.append(f"{item.product.name} (x{item.quantity})")
        items_str = ", ".join(items_list) if items_list else "No items"

        orders_rows += f"""
        <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 font-medium text-gray-900">#{order.id}</td>
            <td class="px-6 py-4 text-gray-500 text-sm">{order.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(order, 'created_at') and order.created_at else "N/A"}</td>
            <td class="px-6 py-4 text-gray-600 text-sm max-w-xs truncate" title="{items_str}">{items_str}</td>
            <td class="px-6 py-4 text-gray-900 font-semibold">${order.total_price:.2f}</td>
            <td class="px-6 py-4">{status_badge}</td>
            <td class="px-6 py-4">
                {"-" if order.status == 'paid' or order.status == 'failed' else f'<a href="/api/orders/checkout-page/" class="text-indigo-600 hover:text-indigo-900 font-medium text-sm">Complete Pay →</a>'}
            </td>
        </tr>
        """

    if not orders_rows:
        orders_rows = """
        <tr>
            <td colspan="6" class="px-6 py-10 text-center text-gray-500">
                You haven't placed any orders yet. 🛒
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Customer Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen font-sans">

        <nav class="bg-white border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <span class="text-xl font-bold text-indigo-600">🚀 SaaS Shop</span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <span class="text-gray-600 text-sm">Welcome, <strong class="text-gray-900">{user.username}</strong></span>
                        <a href="/admin/logout/" class="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg transition">Logout</a>
                    </div>
                </div>
            </div>
        </nav>

        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-900">My Dashboard</h1>
                <p class="text-gray-500 mt-1">Manage your orders, payments, and account status.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <p class="text-sm font-medium text-gray-500 truncate">Total Spent</p>
                    <p class="mt-2 text-3xl font-semibold text-indigo-600">${total_spent:.2f}</p>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <p class="text-sm font-medium text-gray-500 truncate">Paid Orders</p>
                    <p class="mt-2 text-3xl font-semibold text-green-600">{paid_orders_count}</p>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <p class="text-sm font-medium text-gray-500 truncate">Failed Payments</p>
                    <p class="mt-2 text-3xl font-semibold text-red-600">{failed_orders_count}</p>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <p class="text-sm font-medium text-gray-500 truncate">Pending Orders</p>
                    <p class="mt-2 text-3xl font-semibold text-yellow-600">{pending_orders_count}</p>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div class="px-6 py-5 border-b border-gray-100 flex justify-between items-center">
                    <h2 class="text-lg font-bold text-gray-900">Order History</h2>
                    <a href="/api/orders/checkout-page/" class="text-sm bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2 rounded-lg transition shadow-sm">
                        + New Checkout
                    </a>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider border-b border-gray-100">
                                <th class="px-6 py-4 font-semibold">Order ID</th>
                                <th class="px-6 py-4 font-semibold">Date</th>
                                <th class="px-6 py-4 font-semibold">Items</th>
                                <th class="px-6 py-4 font-semibold">Total</th>
                                <th class="px-6 py-4 font-semibold">Status</th>
                                <th class="px-6 py-4 font-semibold">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            {orders_rows}
                        </tbody>
                    </table>
                </div>
            </div>

        </main>
    </body>
    </html>
    """
    return HttpResponse(html_content)