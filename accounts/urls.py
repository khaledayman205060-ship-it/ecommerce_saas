from django.urls import path
from .views import MerchantProfileView, MerchantRegisterView

urlpatterns = [
    path('profile/', MerchantProfileView.as_view(), name='merchant-profile'),
    path('register/merchant/', MerchantRegisterView.as_view(), name='merchant-register'),
]