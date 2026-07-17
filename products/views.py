from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import ProductSerializer
from django.shortcuts import render

def checkout_page(request):
    return render(request, 'checkout.html')

class ProductListCreateView(APIView):
    # تأمين الـ endpoint بحيث ما يدخلش غير تاجر معاه Token
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # جلب منتجات المتجر الخاص بالتاجر الحالي فقط
        user = request.user
        if hasattr(user, 'merchant_profile') and user.merchant_profile.store:
            products = Product.objects.filter(store=user.merchant_profile.store)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        return Response({"error": "لم يتم العثور على متجر لهذا الحساب"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        user = request.user
        if hasattr(user, 'merchant_profile') and user.merchant_profile.store:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                # حفظ المنتج وربطه بمتجر التاجر الحالي تلقائياً
                serializer.save(store=user.merchant_profile.store)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "لا تملك صلاحية إضافة منتجات (يجب أن تكون تاجر ولديك متجر)"}, status=status.HTTP_403_FORBIDDEN)