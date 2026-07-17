import os
from pathlib import Path

# BASE_DIR هو المسار الرئيسي للمشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------- إعدادات الأمان (Security) -----------------
SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = ['*']

# ----------------- التطبيقات (Installed Apps) -----------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # تطبيقات الـ Rest Framework
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # تطبيقات مشروعك الخاصة (تأكد من مطابقتها لمشروعك)
    'accounts',
    'products',
    'cart',
    'orders',
]

# ----------------- الـ Middleware -----------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # لفك حظر الـ CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ----------------- 🎯 تعديل الـ TEMPLATES الرئيسي -----------------
# هنا خلينا دجانغو يقرأ مجلد templates الخارجي ومجلدات التطبيقات معاً
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 👈 السطر ده متعدل عشان يقرأ فولدر الـ templates الرئيسي بالملي بدون أخطاء مسارات:
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ----------------- قاعدة البيانات (Database) -----------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ----------------- التحقق من كلمة المرور -----------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------- اللغة والوقت -----------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------- الملفات الثابتة (Static Files) -----------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------- إعدادات الـ Rest Framework & JWT -----------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

CORS_ALLOW_ALL_ORIGINS = True

# ----------------- 📧 إعدادات إرسال الإيميل التجريبي -----------------
# السطر ده بيخلي الإيميلات تُطبع في التيرمينال فوراً للتجربة المحلية السهلة والآمنة
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'