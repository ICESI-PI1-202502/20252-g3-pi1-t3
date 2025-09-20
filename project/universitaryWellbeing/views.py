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



#Login descartado para 2 pantallas como en la secuencia de figma (NO Practico y poco elegante)
#def user_login_step1(request):
    if request.method == "POST":
        username = request.POST.get("username")

        if User.objects.filter(username=username).exists():
            # Guardar en la sesión
            request.session["partial_username"] = username
            return redirect("login-step2")
        else:
            messages.error(request, "El usuario no existe")

    return render(request, "login_1.html")


#def user_login_step2(request):
    username = request.session.get("partial_username", None)

    if not username:
        # Si alguien entra directo sin pasar por step1
        return redirect("login-step1")

    if request.method == "POST":
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            # Limpio la sesión temporal
            del request.session["partial_username"]
            return redirect("")
        else:
            messages.error(request, "Contraseña incorrecta")

    return render(request, "login_2.html", {"username": username})


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





 













