from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime
import logging
from django.core.mail import send_mail
from django.conf import settings


from universitaryWellbeing.models import ProyectosSociales, Participantes, InscripcionesPsu , EstadosParticipacion

logger = logging.getLogger(__name__)

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
    logger.info("inscribirse_psu: INICIO method=%s user=%s", request.method, request.user.id)
    

    p = get_object_or_404(ProyectosSociales, pk=pk)
    participante = _current_participante(request.user)
    if not participante:
        messages.error(request, "No se encontró Participantes asociado al user actual.")
        logger.warning("inscribirse_psu: participante=None user=%s", request.user.id)
        return redirect("social_projects:detalle_proyecto", pk=pk)

   
    if InscripcionesPsu.objects.filter(
        participantes_id_participante=participante,
        proyectos_sociales_id_proyecto=p
    ).exists():
        messages.info(request, "Ya estaba inscrito.")
        logger.info("inscribirse_psu: ya_inscrito user=%s proj=%s", request.user.id, pk)
        return redirect("social_projects:detalle_proyecto", pk=pk)

    
    try:
        with transaction.atomic():
            p = ProyectosSociales.objects.select_for_update().get(pk=pk)
            inscritos = InscripcionesPsu.objects.filter(proyectos_sociales_id_proyecto=p).count()
            logger.info("inscribirse_psu: cupo usados=%s total=%s", inscritos, p.aforo)
            if p.aforo is not None and inscritos >= p.aforo:
                messages.error(request, "Aforo lleno.")
                return redirect("social_projects:detalle_proyecto", pk=pk)

            
            estado = (EstadosParticipacion.objects
                      .filter(nombre__iexact="pendiente")
                      .order_by("id_estado_participacion")
                      .first())
            if not estado:
                estado = EstadosParticipacion.objects.order_by("id_estado_participacion").first()
            if not estado:
                messages.error(request, " No hay estado válido.")
                logger.error("inscribirse_psu: sin estado de participación válido")
                return redirect("social_projects:detalle_proyecto", pk=pk)

            
            InscripcionesPsu.objects.create(
                participantes_id_participante=participante,
                proyectos_sociales_id_proyecto=p,
                fecha_inscripcion=timezone.now(),
                estados_participacion_id_estado_participacion=estado,
            )
    except IntegrityError as e:
        messages.error(request, f"[DEBUG] IntegrityError: {e}")
        logger.exception("inscribirse_psu: IntegrityError")
        return redirect("social_projects:detalle_proyecto", pk=pk)
    except Exception as e:
        messages.error(request, f"[DEBUG] Exception: {e}")
        logger.exception("inscribirse_psu: Exception")
        return redirect("social_projects:detalle_proyecto", pk=pk)

    messages.success(request, "Inscripción realizada con éxito.")
    logger.info("inscribirse_psu: OK user=%s proj=%s", request.user.id, pk)
    return redirect("social_projects:detalle_proyecto", pk=pk)




@login_required
def consultar_duda(request, pk):
    """Permite a un estudiante enviar una duda al coordinador de un proyecto social."""
    proyecto = get_object_or_404(ProyectosSociales, id_proyecto=pk)
    participante = get_object_or_404(Participantes, user_id=request.user.id)
    
    try:
        coordinador = Participantes.objects.get(id_participante=proyecto.coordinador_id)
    except Participantes.DoesNotExist:
        coordinador = None

    if request.method == "POST":
        mensaje = request.POST.get("mensaje")

        if not mensaje.strip():
            messages.error(request, "Por favor, escribe tu duda antes de enviarla.")
        else:
            if coordinador and coordinador.correo:
                try:
                    send_mail(
                        subject=f"Duda sobre el proyecto: {proyecto.nombre}",
                        message=f"Estudiante: {participante.nombre} {participante.apellido}\n"
                                f"Correo: {participante.correo}\n\n"
                                f"Duda:\n{mensaje}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[coordinador.correo],
                        fail_silently=False,
                    )
                    messages.success(request, "Tu duda fue enviada exitosamente al coordinador del proyecto.")
                except Exception as e:
                    messages.error(request, f"Hubo un error al enviar el mensaje. Por favor intenta más tarde.")
            else:
                messages.error(request, "No se pudo enviar el mensaje. El proyecto no tiene coordinador asignado.")
            
            return redirect("social_projects:detalle_proyecto", pk=pk)

    return render(request, "consultar_duda.html", {
        "proyecto": proyecto,
        "coordinador": coordinador
    })


def enviar_email(asunto, mensaje, destinatarios):
    """Envía un email y lo registra en el log"""
    if not destinatarios:
        return
    send_mail(
        asunto,
        mensaje,
        settings.DEFAULT_FROM_EMAIL,
        destinatarios,
        fail_silently=True
    )
 


 