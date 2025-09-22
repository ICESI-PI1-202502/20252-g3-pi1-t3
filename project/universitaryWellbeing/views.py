from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, render

# Create your views here.
def user_login(request):
    if request.method == "POST":
        cedula_input = request.POST.get("cedula", "").strip()
        password = request.POST.get("password", "")

        if not User.objects.filter(username=cedula_input).exists():
            messages.error(request, "El usuario con esa cédula no existe")
            return redirect("login")

        user = authenticate(request, username=cedula_input, password=password)

        if user is not None:
            login(request, user)
            if is_role_admin(user):
                return redirect("admin:index")  # admin Django
            return redirect("home")
        else:
            messages.error(request, "Contraseña incorrecta")
            return redirect("login")

    # GET → mostrar formulario vacío
    return render(request, "login.html", {})


def register(request):
    if request.method == "POST":
        cedula_input = request.POST.get("cedula", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if User.objects.filter(username=cedula_input).exists():
            messages.error(request, "Ya existe un usuario con esa cédula")
            return redirect("register")

        user = User.objects.create_user(
            username=cedula_input,
            password=password,
            email=email
        )
        messages.success(request, "Usuario registrado con éxito. Ahora puede iniciar sesión.")
        return redirect("login")

    return render(request, "auth/register.html")



def user_logout(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente")
    return redirect("login")

def is_role_admin(user):
    return user.groups.filter(name="admin").exists() or user.is_superuser

@login_required
def preferences(request):
    return render(request, 'list_prefences_1.html')


def home(request):
  return render(request, 'home.html')





 













