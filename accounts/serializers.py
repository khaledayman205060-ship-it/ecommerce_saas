from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MerchantProfile, Store

# 1. سيرايالايزر تسجيل التاجر وإنشاء المتجر تلقائياً
class MerchantRegisterSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'shop_name']

    def create(self, validated_data):
        shop_name = validated_data.pop('shop_name')
        password = validated_data.pop('password')

        # إنشاء حساب المستخدم
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # إنشاء المتجر (Store) تلقائياً باسم المحل والـ slug بيتحسب لوحده
        store = Store.objects.create(name=shop_name)

        # إنشاء بروفايل التاجر وربطه بالمستخدم والمتجر
        MerchantProfile.objects.create(
            user=user,
            store=store,
            shop_name=shop_name
        )

        return user


# 2. سيرايالايزر عرض بيانات البروفايل (الذي كان يسبب الخطأ)
class MerchantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantProfile
        fields = '__all__'