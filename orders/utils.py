import io
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from xhtml2pdf import pisa

def send_invoice_email(order, items_ordered):
    """
    دالة تأخذ بيانات الطلب والمنتجات، تولد فاتورة PDF وترسلها عبر البريد الإلكتروني.
    """
    # 1. تجميع البيانات داخل قالب الـ HTML
    context = {
        'order': order,
        'items': items_ordered,
    }
    html_string = render_to_string('emails/invoice_pdf.html', context)
    
    # 2. تحويل الـ HTML إلى ملف PDF في الـ Memory
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
    
    if pisa_status.err:
        return False  # لو حدث خطأ أثناء التوليد
        
    pdf_buffer.seek(0)
    pdf_data = pdf_buffer.getvalue()

    # 3. إعداد رسالة الإيميل
    subject = f"Your Invoice for Order #{order.id} - Ecommerce SaaS"
    body = "Thank you for your purchase! Please find your official invoice attached to this email."
    from_email = "no-reply@ecommercesaas.com"  # الإيميل المرسل
    to_email = [order.customer.email]          # إيميل العميل المخزن في الطلب

    email = EmailMessage(subject, body, from_email, to_email)
    
    # 4. إرفاق ملف الـ PDF
    email.attach(f'invoice_{order.id}.pdf', pdf_data, 'application/pdf')
    
    # 5. الإرسال الفعلي
    email.send(fail_silently=False)
    return True