from django.urls import path
from . import views
from django.contrib import admin
#
urlpatterns=[
 
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path(
        '', 
        views.home_view, 
        name="index"),
    path(
        'trade/', 
        views.trade_view, 
        name='trade' 
        ),
    path(
        'journal', 
        views.journal_view, 
        name='journal'
        ),
    path(
        "update/<int:trade_id>/", 
        views.update_trade_view, 
        name="update_trade"
        ),
    path(
        "performance", 
        views.performance_view, 
        name="performance"
        ),
    path(
        "trades", 
        views.trades_view, 
        name="trades_view"
        ),
    path(
        'export-trades/', 
        views.export_trades_to_excel, 
        name='export_trades'
        ),
  
    path(
        'academy/', 
        views.academy_view, 
        name="academy"),
    path(
        "performance/<int:pair_id>/", 
        views.performance_by_pair_view, 
        name="performance_by_pair"
        ),
    path(
        "api/performance/overview/",
        views.performance_overview,
        name="performance_overview",
        ),

    path(
        'p',
        views.p,
        name='p'
    ),
    
    path(
        "delete/<int:trade_id>/confirm/", 
        views.delete_trade_view, 
        name="delete_trade_confirm"
        ),
    path(
        "delete/<int:trade_id>/", 
        views.delete_trade, 
        name="delete_trade"
        ),

    path('save-mood/', views.save_mood, name='save_mood'),
    path('get-mood-stats/', views.get_mood_stats, name='get_mood_stats')
  ]