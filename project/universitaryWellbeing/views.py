from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
# Create your views here.

def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                messages.error(request, "Email o contraseña incorrectos")

    # Si es GET o si falló el login, simplemente renderizamos el login vacío
    return render(request, "login.html")

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
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe")
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)

            # Asignar grupo "Usuarios" automáticamente
            user_group, created = Group.objects.get_or_create(name="Usuarios")
            user.groups.add(user_group)

            login(request, user)
            messages.success(request, "¡Registro exitoso!")
            return redirect("")

    return render(request, "auth/register.html")

def user_logout(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente")
    return redirect("login")

def is_role_admin(user):
    return user.groups.filter(name="admin").exists() or user.is_superuser


def home(request):
  return render(request, 'home.html')
