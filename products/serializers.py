from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    # جعل حقل المتجر للقراءة فقط لأننا هنربطه تلقائياً من الـ Token
    store = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'store', 'name', 'description', 'price', 'stock', 'created_at']