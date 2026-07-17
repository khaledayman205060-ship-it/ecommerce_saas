from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_or_create_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    # 1️⃣ لعرض السلة الخاصة بالذوزر الحالي (GET /api/cart/)
    def list(self, request):
        cart = self.get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    # 2️⃣ لإضافة منتج للسلة أو زيادة كميته (POST /api/cart/)
    def create(self, request):
        cart = self.get_or_create_cart(request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "المنتج غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        # لو المنتج موجود في السلة أصلاً، زود الكمية
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response({"detail": "تم إضافة المنتج للسلة بنجاح"}, status=status.HTTP_201_CREATED)

class CartItemViewSet(viewsets.ModelViewSet):
    """لتعديل كمية منتج معين أو حذفه من السلة"""
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer
    queryset = CartItem.objects.all()

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)