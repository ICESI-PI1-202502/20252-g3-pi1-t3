from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from .models import Preferencias, Actividades, Participantes, TiposActividad, PreferenciasActividades,Roles,Citas, HorariosParticipante, HorariosActividad
from .forms import UserLoginForm, UserRegisterForm
from typing import List
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Notificaciones

def user_login(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)

            # Si es admin -> redirige al home_admin
            if is_role_admin(form.user):
                return redirect("cadi_admin") 

            # Obtener el participante relacionado con el usuario
            try:
                participante = Participantes.objects.get(user=form.user)
            except Participantes.DoesNotExist:
                participante = None

            # Si el participante no tiene preferencias, redirigir a la función 'preferences'
            if participante:
                tiene_preferencias = Preferencias.objects.filter(
                    participantes_id_participante=participante
                ).exists()
                if not tiene_preferencias:
                    return redirect("preferences")

            # Si tiene preferencias o no es admin -> home normal
            return redirect("home")

        else:
            for error in form.errors.values():
                messages.error(request, str(error))
            return redirect("login")
    else:
        form = UserLoginForm()
    return render(request, "login.html", {"form": form})


def is_role_admin(user):
    return user.groups.filter(name="admin").exists() or user.is_superuser


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
                id_participante=cedula,
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
                messages.error(request, str(error))
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


@login_required 
def preferences(request):
    participante = Participantes.objects.get(user=request.user)
    # Verificar si ya existen preferencias
    if hasattr(participante, 'preferencias'):
        return redirect('home')  # Ya las completó

    categorias = TiposActividad.objects.all()

    if request.method == 'POST':
        seleccionadas = request.POST.getlist('categories')

        # Crear la preferencia solo si no existe
        pref = Preferencias.objects.create(
            participantes_id_participante=participante,
            fecha_registro=date.today()
        )

        for cat_id in seleccionadas:
            PreferenciasActividades.objects.create(
                preferencia=pref,
                tipo_actividad=TiposActividad.objects.get(pk=cat_id)
        )


        return redirect('home')

    return render(request, 'list_preferences.html', {'categorias': categorias})


import json
@login_required
def horario(request):
    # Obtener el participante asociado al usuario autenticado
    participante = get_object_or_404(Participantes, user=request.user.id)

    # Consultar todos los horarios del participante
    eventos = HorariosParticipante.objects.filter(participantes_id_participante=participante.id_participante)

    # Construir los eventos en formato compatible con FullCalendar
    eventos_data = []
    for e in eventos:
        color = "#007bff"  # Azul por defecto
        if e.actividades_id_actividad:
            color = "#28a745"  # Verde
        elif e.citas_id_cita:
            color = "#ffc107"  # Amarillo
        elif e.partidos_id_partido:
            color = "#dc3545"  # Rojo

        eventos_data.append({
            "title": e.titulo,
            "start": e.fecha_inicio.isoformat(),
            "end": e.fecha_fin.isoformat(),
            "color": color,
            "extendedProps": {
                "notas": e.notas or "",
                "fuente": "Automática" if e.fuente_manual == 'N' else "Manual"
            }
        })

    context = {
        "participante": participante,
        "eventos_json": json.dumps(eventos_data)
    }
    return render(request, "Horario.html", context)

@login_required
def home_user(request):
     
    if request.user.is_superuser:
        return render(request, "pageNotFound-404.html", status=404)
    
    user = request.user
    actividades = Actividades.objects.values("nombre") 
   # actividades_recomendadas = get_recommendations_for_user(user)
    horario = get_user_schedule(user)
    calendario = get_user_calendar(user)

 # Intentamos obtener el rol del participante
    #participante = Participantes.objects.filter(usuario=user).select_related('roles_id_rol').first()
    participante = Participantes.objects.filter(user=user).select_related('roles_id_rol').first()
    user_rol = participante.roles_id_rol.nombre_rol if participante and participante.roles_id_rol else None


    context = {
       # "actividades_recomendadas": actividades_recomendadas,
        "horario": horario,
        "calendario": calendario,
        "actividades": actividades,
        "user_rol": user_rol,  #  agregado aquí
    }

    return render(request, "home_user.html", context)

@login_required
def home_admin(request):
        
    return render(request, "home_admin.html")

def get_recommendations_for_user(user):
    try:
        participante = Participantes.objects.get(user=user)
        preferencias = Preferencias.objects.get(participantes_id_participante=participante)
        tipos_preferidos = PreferenciasActividades.objects.filter(
            preferencia=preferencias
        ).values_list('tipo_actividad', flat=True)

        return Actividades.objects.filter(tipos_actividad_id_tipo__in=tipos_preferidos)
    except (Participantes.DoesNotExist, Preferencias.DoesNotExist):
        return []
    
def get_user_schedule(user):
    try:
        participante = Participantes.objects.get(user=user)
        return HorariosParticipante.objects.filter(participantes_id_participante=participante)
    except Participantes.DoesNotExist:
        return []
    
def get_user_calendar(user):
    try:
        participante = Participantes.objects.get(user=user)
        return Citas.objects.filter(participantes_id_participante=participante)
    except Participantes.DoesNotExist:
        return []


@login_required
def profile(request):
    participante = Participantes.objects.get(user=request.user)
    try:
        preferencia = Preferencias.objects.get(participantes_id_participante=participante)
        actividades: List[PreferenciasActividades] = preferencia.actividades.all()  # type: ignore # Esto funciona en Django pero Pylance lo marca falso positivo
    except Preferencias.DoesNotExist:
        actividades = []

    context = {
        "participante": participante,
        "actividades": actividades,
    }
    return render(request, "profile.html", context)


@login_required
def ver_notificaciones(request):
    notificaciones = Notificaciones.objects.filter(
        participantes_id_participante__user=request.user
    ).order_by('-fecha')

    return render(request, "notificaciones/notificaciones.html", {
        "notificaciones": notificaciones
    })


