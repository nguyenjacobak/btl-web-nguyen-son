from django.urls import path
from . import views  # Assuming this is where your view functions are defined

urlpatterns = [
    # ...existing URL patterns...
    
    # Add these new URL patterns
    path('captcha-image/', core.views.generate_captcha_image, name='captcha_image'),
    path('verify-captcha/', core.views.verify_captcha, name='verify_captcha'),
    
    path('log-captcha', views.log_captcha, name='log_captcha'),
    path('captcha-log/', views.captcha_log, name='captcha_log'),
]
