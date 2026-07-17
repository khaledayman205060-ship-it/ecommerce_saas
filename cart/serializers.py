from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product

class ProductCartSerializer(serializers.ModelSerializer):
    """سيرياليزر مبسط لعرض بيانات المنتج جوه السلة"""
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductCartSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        # حساب السعر الإجمالي للمنتج ده بناءً على الكمية
        return obj.quantity * obj.product.price

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']

    def get_total_price(self, obj):
        # حساب السعر الإجمالي للسلة كلها
        return sum(item.quantity * item.product.price for item in obj.items.all())