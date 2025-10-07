from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.user_login, name="login"),
    path('logout/', views.user_logout, name='logout'),
    path("cadi/", include("management_CADI.urls", namespace="management_cadi")),
    path("home/", views.home_user, name="home"),
    path("profile/", views.profile, name="profile"),
    path("cadi-home/", views.home_admin, name="cadi_admin"),
    path("register/", views.register, name="register"),
    path("preferences/", views.preferences, name="preferences"),
    path("analytics-reports/", include("Analytics_Reports.urls", namespace="analytics_reports")),
    path("tournaments/", include("tournaments.urls")),


    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
]
