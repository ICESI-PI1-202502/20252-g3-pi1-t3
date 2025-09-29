from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.user_login, name="login"),
    path('logout/', views.user_logout, name='logout'),
    #path('admin/login/', views.AdminLoginView.as_view(), name='admin_login'),
    path("cadi/", include("management_CADI.urls", namespace="management_cadi")),
    path("home/", views.home_user, name="home"),
    path("profile/", views.profile, name="profile"),
    path("cadi-home/", views.home_admin, name="cadi_admin"),
    path("register/", views.register, name="register"),
    path("preferences/", views.preferences, name="preferences"),
     path("management-cadi/", include("management_CADI.urls", namespace="management_cadi")),
    path("analytics-reports/", include("Analytics_Reports.urls", namespace="analytics_reports")),
]
