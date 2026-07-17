from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import MerchantProfile
from .serializers import MerchantProfileSerializer, MerchantRegisterSerializer

# 1. فيو عرض البروفايل الحالي (القديم)
class MerchantProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.merchant_profile
            serializer = MerchantProfileSerializer(profile)
            return Response(serializer.data)
        except MerchantProfile.DoesNotExist:
            return Response({"error": "هذا المستخدم ليس لديه بروفايل تاجر."}, status=status.HTTP_404_NOT_FOUND)

# 2. فيو تسجيل تاجر جديد (الجديد)
class MerchantRegisterView(APIView):
    permission_classes = [] # عام بدون توكين مسبق

    def post(self, request):
        serializer = MerchantRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # توليد التوكين فوراً
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                "message": "تم تسجيل التاجر وإنشاء المتجر بنجاح! 🎉",
                "username": user.username,
                "token": token.key
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)