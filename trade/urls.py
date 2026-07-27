from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls, ),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('', views.home_view, name="index"),
    path('trade/', views.trade_view, name='trade'),
    path('journal', views.journal_view, name='journal'),
    path("update/<int:trade_id>/", views.update_trade_view, name="update_trade"),
    path("performance", views.performance_view, name="performance"),
    path("trades", views.trades_view, name="trades_view"),
    path('export-trades/', views.export_trades_to_excel, name='export_trades'),
    path('academy/', views.academy_view, name="academy"),
    path("performance/<int:pair_id>/", views.performance_by_pair_view, name="performance_by_pair"),
    path("api/performance/overview/", views.performance_overview, name="performance_overview"),
    path('p', views.p, name='p'),
    path("delete/<int:trade_id>/confirm/", views.delete_trade_view, name="delete_trade_confirm"),
    path("delete/<int:trade_id>/", views.delete_trade, name="delete_trade"),
    path('save-mood/', views.save_mood, name='save_mood'),
    path('get-mood-stats/', views.get_mood_stats, name='get_mood_stats'),
    path('drafts/', views.drafts_view, name='drafts'),
    path('drafts/complete/<int:draft_id>/', views.complete_draft, name='complete_draft'),
    path('drafts/delete/<int:draft_id>/', views.delete_draft, name='delete_draft'),
    path('drafts/delete/<int:draft_id>/confirm/', views.delete_draft_confirm, name='delete_draft_confirm'),
    path('trade-detail/<int:trade_id>/', views.trade_detail_view, name='trade_detail'),
]

# ✅ Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)