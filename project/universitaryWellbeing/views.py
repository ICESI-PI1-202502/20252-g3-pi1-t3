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

# ========== LOGIN ==========
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
                
                # ✅ PASO 1: Verificar si tiene tipo_participante asignado
                if not participante.tipo_participante:
                    messages.info(request, '¡Bienvenido! Por favor completa tu perfil para continuar.')
                    return redirect("completar_perfil")
                
                # ✅ PASO 2: Si tiene tipo_participante, verificar preferencias
                tiene_preferencias = Preferencias.objects.filter(
                    participantes_id_participante=participante
                ).exists()
                
                if not tiene_preferencias:
                    messages.info(request, 'Ahora selecciona tus preferencias de actividades.')
                    return redirect("preferences")
                
                # ✅ PASO 3: Todo está completo, ir al home
                messages.success(request, f'¡Bienvenido de nuevo, {participante.nombre}!')
                return redirect("home")
                
            except Participantes.DoesNotExist:
                messages.error(request, 'No se encontró tu perfil de participante.')
                logout(request)
                return redirect("login")

        else:
            for error in form.errors.values():
                messages.error(request, str(error))
            return redirect("login")
    else:
        form = UserLoginForm()
    return render(request, "login.html", {"form": form})


 

def is_role_admin(user):
    return user.groups.filter(name="admin").exists() or user.is_superuser

# ========== REGISTRO ==========
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

            # ✅ ROL POR DEFECTO: Estudiante (ÚNICO ROL ASIGNADO POR CÓDIGO)
            try:
                rol_estudiante = Roles.objects.get(nombre_rol='Estudiante')
            except Roles.DoesNotExist:
                messages.error(request, 'Error: No se encontró el rol "Estudiante" en la base de datos.')
                return redirect("register")
            
            # ✅ CREAR PARTICIPANTE SIN tipo_participante (se asigna en completar_perfil)
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
                estado_activo="S",
                roles_id_rol=rol_estudiante,  # ✅ Siempre "Estudiante"
                tipo_participante=None  # ✅ NULL - se asigna después
            )

            messages.success(request, "Usuario registrado con éxito. Ahora puedes iniciar sesión.")
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

    #  Obtener notificaciones de este participante
    notificaciones = Notificaciones.objects.filter(
        participantes_id_participante=participante
    ).order_by('-fecha')

    notificaciones_no_leidas = notificaciones.filter(leida=False).count()

    # 👤 Rol del usuario (por si lo necesita el menú lateral)
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



@login_required
def completar_perfil(request):
    """
    Vista para que el usuario complete su perfil la primera vez.
    Solo se muestra si el participante no tiene tipo_participante asignado.
    """
    try:
        participante = Participantes.objects.get(user=request.user)
        
        # ✅ Si ya tiene tipo_participante válido, redirigir a preferencias
        if participante.tipo_participante:
            return redirect('preferences')
            
    except Participantes.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil de participante.')
        logout(request)
        return redirect('login')
    
    if request.method == 'POST':
        tipo_nombre = request.POST.get('tipo_participante', '').strip().lower()  # ✅ CAMBIO AQUÍ
        
        if not tipo_nombre:
            messages.error(request, 'Debes seleccionar tu vínculo con la universidad.')
            return render(request, 'completar_perfil.html', {
                'participante': participante
            })
        
        try:
            # ✅ Mapeo de valores del formulario a nombres en tipos_participante
            mapeo_tipos = {
                'estudiante': 'Estudiante',
                'trabajador': 'Docente',  # O el nombre que tengas en la BD
                'egresado': 'Egresado',
                'invitado': 'Otro'  # O el nombre que tengas en la BD
            }
            
            nombre_tipo_bd = mapeo_tipos.get(tipo_nombre)
            
            if not nombre_tipo_bd:
                messages.error(request, 'Tipo de participante no válido.')
                return render(request, 'completar_perfil.html', {
                    'participante': participante
                })
            
            # ✅ Buscar el tipo_participante en la base de datos
            from .models import TiposParticipante
            tipo_participante = TiposParticipante.objects.get(nombre__iexact=nombre_tipo_bd)
            
            # ✅ Asignar tipo_participante (NO cambiar el rol - roles_id_rol se mantiene como 'Invitado')
            participante.tipo_participante = tipo_participante
            
            # Procesar campos según el tipo
            if tipo_nombre == 'estudiante':
                # CAMPOS REQUERIDOS
                semestre = request.POST.get('semestre', '').strip()
                programa = request.POST.get('programa', '').strip()
                facultad = request.POST.get('facultad', '').strip()
                
                if not semestre:
                    messages.error(request, 'El semestre es obligatorio para estudiantes.')
                    return render(request, 'completar_perfil.html', {'participante': participante})
                
                if not programa:
                    messages.error(request, 'El programa académico es obligatorio para estudiantes.')
                    return render(request, 'completar_perfil.html', {'participante': participante})
                
                if semestre.isdigit():
                    participante.semestre = int(semestre)
                
                participante.programa = programa
                participante.facultad = facultad
                
                # Género opcional
                genero = request.POST.get('genero', '').strip()
                if genero:
                    participante.genero = genero
            
            elif tipo_nombre == 'trabajador':
                # Para trabajador, solo género y facultad son opcionales
                facultad = request.POST.get('facultad', '').strip()
                genero = request.POST.get('genero', '').strip()
                
                if facultad:
                    participante.facultad = facultad
                if genero:
                    participante.genero = genero
            
            elif tipo_nombre == 'egresado':
                # Para egresado, programa y género son opcionales
                programa = request.POST.get('programa', '').strip()
                genero = request.POST.get('genero', '').strip()
                
                if programa:
                    participante.programa = programa
                if genero:
                    participante.genero = genero
            
            elif tipo_nombre == 'invitado':
                # Para invitado, solo género es opcional
                genero = request.POST.get('genero', '').strip()
                if genero:
                    participante.genero = genero
            
            # Guardar cambios
            participante.save()
            
            messages.success(request, f'¡Perfil completado exitosamente como {tipo_participante.nombre}!')
            
            # Redirigir a preferencias
            return redirect('preferences')
            
        except TiposParticipante.DoesNotExist:
            messages.error(request, f'No se encontró el tipo "{nombre_tipo_bd}" en la base de datos.')
        except ValueError as e:
            messages.error(request, 'Error en los datos ingresados. Verifica la información.')
        except Exception as e:
            messages.error(request, f'Error al completar el perfil: {str(e)}')
    
    # GET request
    return render(request, 'completar_perfil.html', {
        'participante': participante
    })