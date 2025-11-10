from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from .models import Preferencias, Actividades, Participantes, TiposActividad, PreferenciasActividades,Roles,Citas, HorariosParticipante, HorariosActividad, Noticias
from .forms import UserLoginForm, UserRegisterForm
from typing import List
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Notificaciones
from django.contrib.auth import views as auth_views
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.urls import reverse_lazy


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
def schedule(request):
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
    actividades_recomendadas = get_recommendations_for_user(user)
    noticias = Noticias.objects.order_by('-fecha_publicacion')[:5]
    horario = get_user_schedule(user)
    calendario = get_user_calendar(user)

 # Intentamos obtener el rol del participante
    #participante = Participantes.objects.filter(usuario=user).select_related('roles_id_rol').first()
    participante = Participantes.objects.filter(user=user).select_related('roles_id_rol').first()
    user_rol = participante.roles_id_rol.nombre_rol if participante and participante.roles_id_rol else None


    context = {
        "actividades_recomendadas": actividades_recomendadas,
        "horario": horario,
        "calendario": calendario,
        "actividades": actividades,
        "user_rol": user_rol,  #  agregado aquí
        "noticias": noticias,
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

    #  Obtener notificaciones de este participante
    notificaciones = Notificaciones.objects.filter(
        participantes_id_participante=participante
    ).order_by('-fecha')

    notificaciones_no_leidas = notificaciones.filter(leida=False).count()

    # Rol del usuario (por si lo necesita el menú lateral)
    user_rol = participante.roles_id_rol.nombre_rol if participante.roles_id_rol else None

    # Actividades del participante
    try:
        preferencia = Preferencias.objects.get(participantes_id_participante=participante)
        actividades = preferencia.actividades.all()  # type: ignore
    except Preferencias.DoesNotExist:
        actividades = []

    context = {
        "participante": participante,
        "actividades": actividades,
        "notificaciones": notificaciones,
        "notificaciones_no_leidas": notificaciones_no_leidas,
        "user_rol": user_rol,
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


# ============================================
# VISTAS DE PASSWORD RESET PERSONALIZADAS
# ============================================
class RateLimitedPasswordResetView(auth_views.PasswordResetView):
    """Vista de password reset con rate limiting (3 intentos por hora)"""
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/reg/password_reset_email.html'
    subject_template_name = 'auth/reg/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def dispatch(self, request, *args, **kwargs):
        # Rate limiting por IP
        ip = self.get_client_ip(request)
        cache_key = f'password_reset_{ip}'
        
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 3:  # Máximo 3 intentos por hora
            messages.error(
                request,
                'Demasiados intentos de recuperación de contraseña. '
                'Por favor intenta nuevamente en 1 hora.'
            )
            return HttpResponseForbidden(
                'Demasiados intentos. Intenta en 1 hora.'
            )
        
        # Incrementar contador de intentos
        cache.set(cache_key, attempts + 1, 3600)  # 1 hora en segundos
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        """Obtener la IP del cliente (considera proxies)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Vista de confirmación que envía notificación de cambio exitoso"""
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def form_valid(self, form):
        # Llamar al método padre primero para cambiar la contraseña
        response = super().form_valid(form)
        
        # Obtener el usuario
        user = form.user
        
        # Enviar email de notificación de cambio exitoso
        try:
            send_mail(
                subject='Tu contraseña ha sido cambiada - BU App',
                message=(
                    f'Hola {user.first_name or user.username},\n\n'
                    f'Tu contraseña fue cambiada exitosamente el {timezone.now().strftime("%d/%m/%Y a las %H:%M")}.\n\n'
                    f'Si NO fuiste tú quien realizó este cambio, '
                    f'contacta a soporte inmediatamente en jhonjhonshon4@gmail.com.\n\n'
                    f'Saludos,\n'
                    f'El equipo de Bienestar Universitario'
                ),
                from_email='BU App <jhonjhonshon4@gmail.com>',
                recipient_list=[user.email],
                fail_silently=True,  # No interrumpir el flujo si falla el email
            )
        except Exception as e:
            # Log del error pero no interrumpir el proceso
            print(f"Error enviando email de notificación: {e}")
        
        return response
