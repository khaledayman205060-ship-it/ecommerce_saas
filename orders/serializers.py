from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from django.db import transaction

class OrderSerializer(serializers.ModelSerializer):
    # حقول إضافية لاستقبال البيانات من الـ Request لأنها مش موجودة في موديل Order مباشرة
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)
    quantity = serializers.IntegerField(write_only=True)
    
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'product', 'quantity', 'total_price', 'status', 'created_at']

    def validate(self, data):
        product = data['product']
        quantity = data['quantity']
        
        if product.stock < quantity:
            raise serializers.ValidationError(
                f"الكمية المطلوبة غير متوفرة. المتاح حالياً في المخزن هو {product.stock} فقط."
            )
        return data

    def create(self, validated_data):
        product = validated_data.pop('product')
        quantity = validated_data.pop('quantity')
        customer = validated_data['customer'] # مبعوثة من الـ perform_create في الـ View
        
        price_at_purchase = product.price
        total_price = price_at_purchase * quantity
        
        # جلب التاجر (لو موديل المنتج مربوط بـ user أو merchant)
        merchant = getattr(product, 'user', getattr(product, 'merchant', customer))

        with transaction.atomic():
            # 1. إنشاء الأوردر
            order = Order.objects.create(
                customer=customer,
                total_price=total_price,
                status='pending'
            )
            
            # 2. إنشاء عنصر الأوردر
            OrderItem.objects.create(
                order=order,
                product=product,
                merchant=merchant,
                quantity=quantity,
                price=price_at_purchase
            )
            
            # 3. تحديث المخزن
            product.stock -= quantity
            product.save()
            
        return order