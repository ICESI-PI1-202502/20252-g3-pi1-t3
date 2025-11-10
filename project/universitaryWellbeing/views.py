import json
from django.http import JsonResponse
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_email
from .models import Preferencias, Actividades, Participantes, TiposActividad, PreferenciasActividades,Roles,Citas, HorariosParticipante, HorariosActividad, Noticias
from .forms import UserLoginForm, UserRegisterForm
from .models import Notificaciones, HorariosBloque
from django.contrib.auth import views as auth_views
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import datetime, date
from collections import defaultdict

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
        tipo_evento = "otro"
        
        if e.actividades_id_actividad:
            color = "#5454E9"  # Morado para actividades
            tipo_evento = "actividad"
        elif e.citas_id_cita:
            color = "#E4EB60"  # Amarillo para citas
            tipo_evento = "cita"
        elif e.partidos_id_partido:
            color = "#E9683B"  # Naranja para partidos
            tipo_evento = "partido"

        # ⭐ CAMBIO CRÍTICO: Detectar si es recurrente
        # Las actividades añadidas manualmente (fuente_manual='S') deben repetirse semanalmente
        es_recurrente = (e.fuente_manual == 'S' and e.actividades_id_actividad is not None)
        
        if es_recurrente:
            # 🔄 EVENTO RECURRENTE - Se repite cada semana
            dia_semana = e.fecha_inicio.weekday()  # 0=Lunes, 1=Martes, ..., 6=Domingo
            eventos_data.append({
                "id": e.id_horario,
                "title": e.titulo,
                "daysOfWeek": [dia_semana],  # CLAVE: Array con el día de la semana
                "startTime": e.fecha_inicio.strftime("%H:%M:%S"),  # Solo la hora
                "endTime": e.fecha_fin.strftime("%H:%M:%S"),      # Solo la hora
                "color": color,
                "extendedProps": {
                    "notas": e.notas or "",
                    "fuente": "Manual",
                    "tipo": tipo_evento,
                    "puede_eliminar": True,
                    "es_recurrente": True  # Marcador para el frontend
                }
            })
        else:
            # EVENTO ÚNICO - Solo aparece en su fecha específica
            eventos_data.append({
                "id": e.id_horario,
                "title": e.titulo,
                "start": e.fecha_inicio.isoformat(),  # Fecha completa
                "end": e.fecha_fin.isoformat(),        # Fecha completa
                "color": color,
                "extendedProps": {
                    "notas": e.notas or "",
                    "fuente": "Automática" if e.fuente_manual == 'N' else "Manual",
                    "tipo": tipo_evento,
                    "puede_eliminar": e.fuente_manual == 'S',
                    "es_recurrente": False
                }
            })

    context = {
        "participante": participante,
        "eventos_json": json.dumps(eventos_data)
    }
    return render(request, "Horario.html", context)


@login_required
@require_http_methods(["POST"])
def delete_event(request, evento_id):
    """
    Endpoint para eliminar un evento del horario personal
    Solo permite eliminar eventos manuales (fuente_manual = 'S')
    """
    try:
        participante = get_object_or_404(Participantes, user=request.user.id)
        
        # Buscar el evento
        evento = get_object_or_404(
            HorariosParticipante,
            id_horario=evento_id,
            participantes_id_participante=participante.id_participante
        )
        
        # Verificar que sea un evento manual
        if evento.fuente_manual != 'S':
            return JsonResponse({
                'success': False,
                'message': 'Solo puedes eliminar eventos creados manualmente'
            }, status=403)
        
        # Eliminar el evento
        titulo = evento.titulo
        evento.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Evento "{titulo}" eliminado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar el evento: {str(e)}'
        }, status=500)  

# FullCalendar: 0=Dom,1=Lun,...6=Sab
def _django_weekday_to_fc_dow(django_wd: int) -> int:
    # Django: 1=Dom ... 7=Sab  -> FC: 0=Dom ... 6=Sab
    return django_wd % 7

@login_required
def unified_calendar(request):

    tipo_id = request.GET.get("tipo")  # string or None

    # Catálogo de tipos para el filtro (una sola consulta)
    tipos = list(
        TiposActividad.objects
        .values("id_tipo", "nombre_tipo")
        .order_by("nombre_tipo")
    )

    # ACTIVIDADES base (con filtro opcional por tipo)
    qs_acts = Actividades.objects.all()
    if tipo_id:
        qs_acts = qs_acts.filter(tipos_actividad_id_tipo=tipo_id)

    acts_rows = list(
        qs_acts.select_related("tipos_actividad_id_tipo")
        .values(
            "id_actividad",
            "nombre",
            "descripcion",
            "tipos_actividad_id_tipo",                      # id del tipo
            "tipos_actividad_id_tipo__nombre_tipo",        # nombre del tipo
        )
    )

    # Mapa en memoria: id_actividad -> info (incluye tipo)
    acts_by_id = {
        r["id_actividad"]: {
            "nombre": r["nombre"],
            "descripcion": r["descripcion"] or "",
            "tipo_id": r["tipos_actividad_id_tipo"],
            "tipo_nombre": r["tipos_actividad_id_tipo__nombre_tipo"],
        }
        for r in acts_rows
    }

    act_ids = list(acts_by_id.keys())

    if not act_ids:
        ctx = {
            "tipos": tipos,
            "tipo_id": str(tipo_id) if tipo_id else "",
            "eventos_json": "[]",
        }
        return render(request, "calendario_unificado.html", ctx)

    # Bloques (una consulta)
    bloques = list(
        HorariosBloque.objects
        .filter(actividades_id_actividad__in=act_ids)
        .values(
            "id_horario_bloque",
            "actividades_id_actividad",
            "profesor",
            "lugar",
            "hora_inicio",
            "hora_fin",
        )
    )

    # Días por bloque (una consulta)
    bloque_ids = [b["id_horario_bloque"] for b in bloques] or []
    dias = list(
        HorariosActividad.objects
        .filter(horario_bloque_id__in=bloque_ids)
        .values("horario_bloque_id", "dia_semana")
    )

    dias_por_bloque = defaultdict(list)
    for d in dias:
        dias_por_bloque[d["horario_bloque_id"]].append(d["dia_semana"])

    # Construcción de eventos (todo en memoria, sin más consultas)
    eventos = []
    for b in bloques:
        act_id = b["actividades_id_actividad"]
        act = acts_by_id.get(act_id)
        if not act:
            continue

        start_time = b["hora_inicio"].strftime("%H:%M:%S")
        end_time   = b["hora_fin"].strftime("%H:%M:%S")

        for django_wd in sorted(dias_por_bloque.get(b["id_horario_bloque"], [])):
            fc_dow = _django_weekday_to_fc_dow(django_wd)
            eventos.append({
                "title": act["nombre"],
                "daysOfWeek": [fc_dow],          # 0..6
                "startTime": start_time,
                "endTime": end_time,
                "display": "block",
                "color": "#5454E9",
                "extendedProps": {
                    "tipo": act["tipo_nombre"],
                    "actividad_id": act_id,
                    "bloque_id": b["id_horario_bloque"],
                    "profesor": b["profesor"] or "",
                    "espacio": b["lugar"] or "",
                    "descripcion": act["descripcion"],
                }
            })

    ctx = {
        "tipos": tipos,
        "tipo_id": str(tipo_id) if tipo_id else "",
        "eventos_json": json.dumps(eventos, ensure_ascii=False, separators=(",", ":")),
    }
    return render(request, "calendario_unificado.html", ctx)


def obtener_eventos_del_dia(participante, fecha):
    """
    Obtiene todos los eventos (únicos y recurrentes) para una fecha específica
    """
    dia_semana = fecha.weekday()
    eventos = []
    
    print(f"Buscando eventos para: {fecha} - {fecha.strftime('%A')} (día {dia_semana})")
    
    # 1. Eventos únicos de la fecha
    eventos_unicos = HorariosParticipante.objects.filter(
        participantes_id_participante=participante,
        fecha_inicio__date=fecha
    )
    
    print(f"Eventos únicos encontrados: {eventos_unicos.count()}")
    
    for ev in eventos_unicos:
        eventos.append({
            'titulo': ev.titulo,
            'fecha_inicio': ev.fecha_inicio,
            'fecha_fin': ev.fecha_fin,
            'notas': ev.notas or '',
            'tipo': 'único',
            'id': ev.id_horario
        })
    
    # 2. Eventos recurrentes que caen en este día de la semana
    eventos_recurrentes = HorariosParticipante.objects.filter(
        participantes_id_participante=participante,
        fuente_manual='S',
        actividades_id_actividad__isnull=False
    )
    
    print(f"Eventos recurrentes totales: {eventos_recurrentes.count()}")
    
    for ev in eventos_recurrentes:
        # Obtener el día de la semana del evento original
        dia_evento = ev.fecha_inicio.weekday()
        print(f"   - {ev.titulo}: día {dia_evento} ({['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][dia_evento]}) | Buscando: {dia_semana} ({['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][dia_semana]})")
        
        if dia_evento == dia_semana:
            # Usar timezone.localtime para asegurar zona horaria correcta
            hora_inicio = ev.fecha_inicio.time()
            hora_fin = ev.fecha_fin.time()
            
            eventos.append({
                'titulo': ev.titulo,
                'fecha_inicio': datetime.combine(fecha, hora_inicio),
                'fecha_fin': datetime.combine(fecha, hora_fin),
                'notas': ev.notas or '',
                'tipo': 'recurrente',
                'id': ev.id_horario
            })
            print(f"      MATCH! Agregado.")
    
    # Ordenar por hora
    eventos.sort(key=lambda x: x['fecha_inicio'].time())
    print(f"Total eventos a mostrar: {len(eventos)}")
    
    return eventos


@login_required
def home_user(request):
    if request.user.is_superuser:
        return render(request, "pageNotFound-404.html", status=404)
    
    user = request.user
    participante = Participantes.objects.filter(user=user).select_related('roles_id_rol').first()
    
    # Datos para el home
    actividades = Actividades.objects.values("nombre")[:10]
    noticias = Noticias.objects.order_by('-fecha_publicacion')[:5]
    actividades_recomendadas = get_recommendations_for_user(user)
    
    ahora = timezone.localtime(timezone.now())
    hoy = ahora.date()
    # Datos para el home
    actividades = Actividades.objects.values("nombre")[:10]
    noticias = Noticias.objects.order_by('-fecha_publicacion')[:5]
    
    # EVENTOS DE HOY para el mini calendario
    eventos_hoy = obtener_eventos_del_dia(participante, hoy)[:5]  # Máximo 5 eventos
    
    # Horario general (próximos 10 eventos)
    horario = HorariosParticipante.objects.filter(
        participantes_id_participante=participante,
        fecha_inicio__gte=timezone.now()
    ).order_by('fecha_inicio')[:10]
    
    # Calendario actividades (próximas 5)
    calendario = Actividades.objects.all()[:5]
    
     # Intentamos obtener el rol del participante
    #participante = Participantes.objects.filter(usuario=user).select_related('roles_id_rol').first()
    participante = Participantes.objects.filter(user=user).select_related('roles_id_rol').first()
    user_rol = participante.roles_id_rol.nombre_rol if participante and participante.roles_id_rol else None

    context = {
        "today": hoy,  # Para mostrar la fecha
        "eventos_hoy": eventos_hoy,  # Eventos del día
        "horario": horario,
        "calendario": calendario,
        "actividades": actividades,
        "user_rol": user_rol,
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
