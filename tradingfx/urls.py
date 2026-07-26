"""
URL configuration for tradingfx project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ============================================
# MAIN URL PATTERNS
# ============================================

urlpatterns = [
    path('admin/', admin.site.urls),  # Fixed: added trailing slash
    path('', include('trade.urls')),
]

# ============================================
# STATIC AND MEDIA FILE SERVING (Development only)
# ============================================

if settings.DEBUG:
    # Serve static files - with safety check
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        try:
            urlpatterns += static(
                settings.STATIC_URL,
                document_root=settings.STATICFILES_DIRS[0]
            )
        except (IndexError, TypeError):
            # Fallback to STATIC_ROOT if STATICFILES_DIRS is empty
            urlpatterns += static(
                settings.STATIC_URL,
                document_root=settings.STATIC_ROOT
            )
    elif hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        urlpatterns += static(
            settings.STATIC_URL,
            document_root=settings.STATIC_ROOT
        )
    
    # Serve media files
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        urlpatterns += static(
            settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT
        )

# ============================================
# CUSTOM ERROR HANDLERS (Optional)
# ============================================

# Uncomment if you have custom error views
# handler404 = 'trade.views.custom_404'
# handler500 = 'trade.views.custom_500'