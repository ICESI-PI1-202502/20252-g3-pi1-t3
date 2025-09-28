from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from .models import Preferencias, Actividades, Participantes, TiposActividad, PreferenciasActividades

def user_login(request):
    if request.method == "POST":
        cedula_input = request.POST.get("cedula", "").strip()
        password = request.POST.get("password", "")

        if not User.objects.filter(username=cedula_input).exists():
            messages.error(request, "El usuario con esa cédula no existe")
            return redirect("user_login")

        user = authenticate(request, username=cedula_input, password=password)

        if user is not None:
            login(request, user)
            participante = getattr(user, "participante", None)
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
        name = request.POST.get("nombre_completo", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not cedula_input.isdigit():
            messages.error(request, "La cédula debe contener solo números.")
            return redirect("register")

        # Verifica si ya existe un usuario con esa cédula
        if get_user_model().objects.filter(username=cedula_input).exists():
            messages.error(request, "Este número de cédula ya está registrado.")
            return redirect("register")
        
          # Validación del correo electrónico usando `validate_email`
        try:
            validate_email(email)  # Intentamos validar el email
        except ValidationError:
            messages.error(request, "El correo electrónico no es válido.")
            return redirect("register")
        
        # Verifica si el correo electrónico ya está registrado
        if get_user_model().objects.filter(email=email).exists():
            messages.error(request, "Este correo electrónico ya está registrado.")
            return redirect("register")
        
        # Divide el nombre completo en 'first_name' y 'last_name'
        if " " in name:
            first_name, last_name = name.split(" ", 1)  # Dividimos solo en el primer espacio
        else:
            first_name, last_name = name, ""  # Si no hay espacio, todo es 'first_name'
        
        # Crear el usuario
        user = get_user_model().objects.create_user(
            username=cedula_input,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

         # Crear el participante enlazado
        Participantes.objects.create(
            user=user,
            nombre=first_name,
            apellido=last_name,
            correo=email,
            semestre=None,
            facultad="",
            programa=""
        )
        messages.success(request, "Usuario registrado con éxito. Ahora puede iniciar sesión.")
        return redirect("login")

    return render(request, "auth/register.html")

class AdminLoginView(LoginView):
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

