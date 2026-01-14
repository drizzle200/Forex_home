from django.urls import path
from . import views
#
urlpatterns=[
    path('', views.index_view, name='index' ),
    path('journal', views.journal_view, name='journal'),
    path("update/<int:trade_id>/", views.update_trade_view, name="update_trade"),
    path("performance", views.performance_view, name="performance"),
    path("trades", views.trades_view, name="trades_view"),
    path('export-trades/', views.export_trades_to_excel, name='export_trades'),
    path('home/', views.home_view, name="home"),

#   delete urls

    path("delete/<int:trade_id>/confirm/", views.delete_trade_confirm, name="delete_trade_confirm"),
    path("delete/<int:trade_id>/", views.delete_trade, name="delete_trade"),
#    path('course/course-lesson/<str:id>', views.course_lesson_view, name='course_lesson'),
#    path('signup', views.signup_view, name='signup'),
#    path('signin', views.signin_vew, name='signin'),
#    path('signout', views.logout_view, name='logout'),
#    path('account', views.account_view, name='account'),
#    path('a-courses', views.account_courses, name='account_courses'),
#    path('a-course/<str:id>', views.account_course, name='account_course'),
#    path('a-lesson/<str:id>', views.account_lesson, name='account_lesson'),
#    path('ad-account', views.admin_account_view, name='admin_account'),
#    path('ad-courses', views.admin_courses, name='admin_courses'),
#    path('843s98eadmidfn235a/account/addcourse', views.add_course, name='add_course'),
#    path('843s98eadmidfn235a/account/modify/<str:id>', views.modify_course, name='modify_course'),
#    path('843s98eadmidfn235a/account/modifyl/<str:id>', views.modify_lesson, name='modify_lesson'),
#    path('ad-created-course/<str:id>', views.created_course, name='created_course'),
#    path('843s98eadmidfn235a/account/c/<str:id>', views.create_curriculum, name='create_curriculum'),
#    path('843s98eadmidfn235a/account/addcourse/lesson/<str:id>', views.create_lesson, name='create_lesson'),   
#    path('843s98eadmidfn235a/account/courses/<str:id>', views.admin_course_curriculum, name='admin_course_curriculum'),
#    path('flight', views.flight),
  ]