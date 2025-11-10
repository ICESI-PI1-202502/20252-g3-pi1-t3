from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.user_login, name="login"),
    path('logout/', views.user_logout, name='logout'),
    path("cadi/", include("management_CADI.urls", namespace="management_cadi")),
    path("search/", include("searchActivities.urls", namespace="search_cadi")),
    path("home/", views.home_user, name="home"),
    path("profile/", views.profile, name="profile"),
    path("cadi-home/", views.home_admin, name="cadi_admin"),
    path("register/", views.register, name="register"),
    path("preferences/", views.preferences, name="preferences"),
    path("analytics-reports/", include("Analytics_Reports.urls", namespace="Analytics_Reports")),
    path("tournaments/", include("tournaments.urls")),
    path("psu/", include("social_projects.urls")),
    path("horario/", views.schedule, name="horario"),
    path("notificaciones/", include("notificaciones.urls", namespace="notificaciones")),
    path("news/", include("news.urls", namespace="news")),


    path('password_reset/', views.RateLimitedPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
]
