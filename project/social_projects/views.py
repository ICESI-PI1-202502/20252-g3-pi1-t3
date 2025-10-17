# social_projects/views.py
from time import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime

from universitaryWellbeing.models import ProyectosSociales, Participantes, InscripcionesPsu , EstadosParticipacion

# --- helpers ---
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def _current_participante(user):
    try:
        return Participantes.objects.get(user=user)
    except Participantes.DoesNotExist:
        return None

def _parse_date(datestr):
    if not datestr:
        return None
    try:
        naive = datetime.strptime(datestr, "%Y-%m-%d")
        return make_aware(naive.replace(hour=0, minute=0, second=0), get_current_timezone())
    except ValueError:
        return None

# --- vistas ---
@login_required
def lista_proyectos(request):
    q = (request.GET.get("q") or "").strip()
    projects = ProyectosSociales.objects.all().order_by("-id_proyecto")
    if q:
        projects = projects.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))

    ctx = {
        "projects": projects,
        "search": q,
        "can_create": is_admin(request.user),   
    }
    return render(request, "lista.html", ctx)

@login_required
def crear_proyecto_social(request):
    if not is_admin(request.user):
        messages.error(request, "No tienes permisos para crear proyectos sociales.")
        return redirect("social_projects:lista_proyectos")

    participante = _current_participante(request.user)
    if not participante:
        messages.error(request, "No se encontró tu registro de participante.")
        return redirect("social_projects:lista_proyectos")

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        descripcion = (request.POST.get("descripcion") or "").strip()
        aforo_raw = (request.POST.get("aforo") or "").strip()
        fecha_inicio = _parse_date(request.POST.get("fecha_inicio") or "")
        fecha_fin    = _parse_date(request.POST.get("fecha_fin") or "")

        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
            return render(request, "crear.html", {"prefill": request.POST})

        aforo = None
        if aforo_raw:
            try:
                aforo = int(aforo_raw)
                if aforo < 0:
                    raise ValueError()
            except ValueError:
                messages.error(request, "Aforo debe ser un entero ≥ 0.")
                return render(request, "crear.html", {"prefill": request.POST})

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            messages.error(request, "La fecha de inicio no puede ser posterior a la fecha fin.")
            return render(request, "crear.html", {"prefill": request.POST})

        try:
            with transaction.atomic():
                ProyectosSociales.objects.create(
                    nombre=nombre,
                    descripcion=descripcion or None,
                    coordinador_id=participante.id_participante,  
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    aforo=aforo,
                )
            messages.success(request, "Proyecto social creado correctamente.")
            return redirect("social_projects:lista_proyectos")
        except IntegrityError:
            messages.error(request, "Error de integridad al crear el proyecto.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al crear el proyecto: {e}")

        return render(request, "crear.html", {"prefill": request.POST})

    # GET
    return render(request, "crear.html", {})

@login_required
def detalle_proyecto(request, pk):
    p = get_object_or_404(ProyectosSociales, pk=pk)
    participante = _current_participante(request.user)

    ya_inscrito = False
    cupo_usado = InscripcionesPsu.objects.filter(proyectos_sociales_id_proyecto=p).count()
    cupo_total = p.aforo
    cupo_disponible = (cupo_total is None) or (cupo_usado < cupo_total)

    if participante:
        ya_inscrito = InscripcionesPsu.objects.filter(
            participantes_id_participante=participante,
            proyectos_sociales_id_proyecto=p
        ).exists()

    ctx = {
        "p": p,
        "can_create": (request.user.is_staff or request.user.is_superuser),
        "ya_inscrito": ya_inscrito,
        "cupo_disponible": cupo_disponible,
        "cupo_usado": cupo_usado,
        "cupo_total": cupo_total,
    }
    return render(request, "detalle.html", ctx)

@login_required
def inscribirse_psu(request, pk):
    # Solo POST para inscribirse
    if request.method != "POST":
        return redirect("social_projects:detalle_proyecto", pk=pk)

    p = get_object_or_404(ProyectosSociales, pk=pk)
    participante = _current_participante(request.user)
    if not participante:
        messages.error(request, "No se encontró tu registro de participante.")
        return redirect("social_projects:detalle_proyecto", pk=pk)

    # 1) Ya inscrito
    if InscripcionesPsu.objects.filter(
        participantes_id_participante=participante,
        proyectos_sociales_id_proyecto=p
    ).exists():
        messages.info(request, "Ya estás inscrito en este proyecto.")
        return redirect("social_projects:detalle_proyecto", pk=pk)

    # 2) Cupo
    inscritos = InscripcionesPsu.objects.filter(proyectos_sociales_id_proyecto=p).count()
    if p.aforo is not None and inscritos >= p.aforo:
        messages.error(request, "El proyecto alcanzó el aforo máximo.")
        return redirect("social_projects:detalle_proyecto", pk=pk)
    
    # 3) Estado "pendiente" robusto (evita MultipleObjectsReturned)
    estado = (
        EstadosParticipacion.objects
        .filter(nombre__iexact="pendiente")
        .order_by("id_estado_participacion")
        .first()
    )
    if not estado:
        # Fallback: toma el primer estado disponible (o lanza error si prefieres)
        estado = EstadosParticipacion.objects.order_by("id_estado_participacion").first()
    if not estado:
        messages.error(request, "No hay un estado de participación válido configurado.")
        return redirect("social_projects:detalle_proyecto", pk=pk)

    # 4) Crear inscripción
    try:
        with transaction.atomic():
            InscripcionesPsu.objects.create(
                participantes_id_participante=participante,
                proyectos_sociales_id_proyecto=p,
                fecha_inscripcion=timezone.now(),
                estados_participacion_id_estado_participacion=estado,
            )
        messages.success(request, "Inscripción realizada con éxito.")
    except IntegrityError:
        messages.error(request, "No se pudo registrar la inscripción por un error de integridad.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al inscribirte: {e}")

    return redirect("social_projects:detalle_proyecto", pk=pk)