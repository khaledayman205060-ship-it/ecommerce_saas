from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CartItemViewSet

router = DefaultRouter()
router.register(r'items', CartItemViewSet, basename='cart-item')

urlpatterns = [
    path('', CartViewSet.as_view({'get': 'list', 'post': 'create'}), name='cart-detail'),
    path('', include(router.urls)),
]