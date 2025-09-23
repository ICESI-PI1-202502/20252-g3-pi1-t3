# universitaryWellbeing/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    
    path("", views.user_login, name="login"),
    path("home/", views.home_user, name="home"),
    path("cadi-home/", views.home_admin, name="cadi_admin"),
    path("register/", views.register, name="register"),
    path("preferences/", views.preferences, name="preferences"),
    path("preferences2/", views.preferences2, name="preferences_2"),
    path("analytics-reports/", include("Analytics_Reports.urls", namespace="analytics_reports")),
    path("management-cadi/", include("management_CADI.urls", namespace="management_cadi")),
]