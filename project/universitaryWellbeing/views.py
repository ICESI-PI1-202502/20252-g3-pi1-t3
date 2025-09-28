from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from .models import Preferencias, Actividades, Participantes, TiposActividad, PreferenciasActividades,Roles
from .forms import UserLoginForm, UserRegisterForm

def user_login(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            if is_role_admin(form.user):
                return redirect("admin:index")
            return redirect("home")
        else:
            for error in form.errors.values():
                messages.error(request, error)
            return redirect("login")
    else:
        form = UserLoginForm()
    return render(request, "login.html", {'form': form})

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            cedula = form.cleaned_data['cedula']
            nombre_completo = form.cleaned_data['nombre_completo']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if " " in nombre_completo:
                first_name, last_name = nombre_completo.split(" ", 1)
            else:
                first_name, last_name = nombre_completo, ""

            user = User.objects.create_user(
                username=cedula,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            rol = Roles.objects.get(nombre_rol='Estudiante')
            Participantes.objects.create(
                user=user,
                nombre=first_name,
                apellido=last_name,
                correo=email,
                semestre=None,
                facultad="",
                programa="",
                genero="",
                estado_activo="S",  # o lo que necesites por defecto
                roles_id_rol=rol
            )

            if rol.grupo_d:
                user.groups.add(rol.grupo_d)

            messages.success(request, "Usuario registrado con éxito. Ahora puede iniciar sesión.")
            return redirect("login")
        else:
            for error in form.errors.values():
                messages.error(request, error)
            return redirect("register")
    else:
        form = UserRegisterForm()

    return render(request, "auth/register.html", {'form': form})
#class AdminLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        user = form.get_user()
        
        if is_role_admin(user):
            return redirect('home_admin')
        else:
            messages.error(self.request, 'No tienes permisos de administrador')
            return redirect('login')

    def form_invalid(self, form):
        messages.error(self.request, 'Credenciales incorrectas')
        return super().form_invalid(form)

def user_logout(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente")
    return redirect("login")

def is_role_admin(user):
    return user.groups.filter(name="admin").exists() or user.is_superuser

#EXPERIMENTAL-
#@login_required 
def preferences(request):
    categorias = TiposActividad.objects.all()  # todas las categorías disponibles

    if request.method == 'POST':
        seleccionadas = request.POST.getlist('categories')  # IDs de categorías elegidas

        # Crear o recuperar la preferencia del usuario
        pref, created = Preferencias.objects.get_or_create(
            participantes_id_participante=request.user.participantes,  # ajusta según tu modelo
            defaults={'fecha_registro': date.today()}
        )

        # Borrar preferencias antiguas
        PreferenciasActividades.objects.filter(preferencias_id_preferencia=pref).delete()

        # Guardar nuevas
        for cat_id in seleccionadas:
            PreferenciasActividades.objects.create(
                preferencias_id_preferencia=pref,
                actividades_id_actividad=TiposActividad.objects.get(pk=cat_id)
            )

        # En lugar de mandar a "recommendations", vamos al home del usuario
        return redirect('home_user')

    return render(request, 'list_preferences.html', {'categorias': categorias})


def home_user(request):
    data = Actividades.objects.values("nombre")  # asumiendo que el campo se llama 'nombre'
    return render(request, 'home_user.html', {'actividades': data})

#def home_user(request):
    data = Actividades.objects.values("nombre")  # asumiendo que el campo se llama 'nombre'
    user_email = request.user.email

    try:
        participante = Participantes.objects.get(correo=user_email)
        preferencia = Preferencias.objects.get(participantes_id_participante=participante)

        recomendaciones_ids = PreferenciasActividades.objects.filter(
            preferencias_id_preferencia=preferencia
        ).values_list('actividades_id_actividad', flat=True)

        recomendaciones = Actividades.objects.filter(id_actividad__in=recomendaciones_ids)

    except (Participantes.DoesNotExist, Preferencias.DoesNotExist):
        recomendaciones = []

    # Actividades generales para mostrar el objeto completo con sus atributos
   # actividades = Actividades.objects.all()

   #calendario idk
   #noticias idk

    return render(request, 'home.html', {
        'actividades': data,
        'recomendaciones': recomendaciones
    })


@login_required
def home_admin(request):
    return render(request, "home_admin.html")

def home(request):
  return render(request, 'home.html')


def profile(request):
    participante = request.user.participante  # acceso directo al modelo relacionado

    context = {
        "user": request.user,
        "participante": participante,
    }
    return render(request, "auth/profile.html", context)

