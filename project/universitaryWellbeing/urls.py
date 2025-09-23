# universitaryWellbeing/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    
    path("", views.user_login, name="login"),
    path("home/", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("preferences/", views.preferences, name="preferences"),
     
    path("management-cadi/", include("management_CADI.urls", namespace="management_cadi")),
]