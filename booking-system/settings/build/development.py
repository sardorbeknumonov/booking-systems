from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ['*']
# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'booking_systems_db'),
        'USER': os.getenv('DB_USER', 'bookkoob'),
        'PASSWORD': os.getenv('DB_PASSWORD', '$!bookkoob!$'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5232'),
    }
}
