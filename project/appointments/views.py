import datetime as dt
from dataclasses import dataclass
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import Http404
from django.utils.timezone import localtime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import (
    make_aware, get_current_timezone, is_naive, now
)

# AJUSTA este import al módulo real donde están tus modelos
from universitaryWellbeing.models import (
    Participantes, AgendaPsicologos, HorariosParticipante,
    Citas, HistorialCitas, EstadosCita, MotivosCita # EstadosCita/MotivosCita están bloqueados por el OneToOne
)

# ----------------------------
# Utilidades
# ----------------------------
def _parse_dt_local(s: str):
    if not s:
        return None
    s = s.strip()
    tz = get_current_timezone()

    # 1) ISO (lo usual de <input type="datetime-local">)
    try:
        dt_naive = dt.datetime.fromisoformat(s.replace("Z", ""))
        return make_aware(dt_naive, tz) if is_naive(dt_naive) else dt_naive
    except Exception:
        pass

    # 2) Normalizar AM/PM con variantes en español
    s_norm = (
        s.lower()
         .replace("a. m.", "AM").replace("p. m.", "PM")
         .replace("a. m", "AM").replace("p. m", "PM")
         .replace(" a. m.", " AM").replace(" p. m.", " PM")
    )

    # 3) Formatos comunes
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %I:%M %p"):
        try:
            dt_naive = dt.datetime.strptime(s_norm, fmt)
            return make_aware(dt_naive, tz)
        except ValueError:
            continue

    return None


def _get_professionals():
    qs = (
        Participantes.objects
        .select_related("user", "roles_id_rol")
        .filter(user__is_active=True)
        .filter(
            Q(roles_id_rol__id_rol=5) |
            Q(roles_id_rol__nombre_rol__iexact="Psicólogo")
        )
        .order_by("nombre", "apellido")
        .distinct()
    )
    return [
        {"id": p.id_participante, "nombre": f"{p.nombre} {p.apellido}".strip() or p.correo}
        for p in qs
    ]



def _overlap_q(inicio, fin):
    """
    Solape estricto en [inicio, fin):
    existe si fecha_inicio < fin  y  fecha_fin > inicio
    """
    return Q(fecha_inicio__lt=fin) & Q(fecha_fin__gt=inicio)


def _get_participante_from_user(user) -> Participantes:
    return get_object_or_404(Participantes, user_id=user.id)


@dataclass
class SlotDecision:
    inicio: dt.datetime
    fin: dt.datetime
    slot: AgendaPsicologos | None
    lugar: str | None


def _decide_slot_or_duration(*, profesional: Participantes, inicio: dt.datetime) -> SlotDecision:
    """
    - Si existe un slot DISPONIBLE del profesional que cubra el inicio, úsalo.
    - En otro caso, duración por defecto: 45 minutos.
    """
    slot = (
        AgendaPsicologos.objects
        .filter(participantes_id_participante=profesional)
        .filter(fecha_inicio__lte=inicio, fecha_fin__gt=inicio)
        .filter(estado_slot__iexact="DISPONIBLE")
        .order_by("fecha_inicio")
        .first()
    )

    if slot:
        return SlotDecision(inicio=slot.fecha_inicio, fin=slot.fecha_fin, slot=slot, lugar=getattr(slot, "lugar", None))

    # Sin slot: 45 minutos por defecto
    fin = inicio + dt.timedelta(minutes=45)
    return SlotDecision(inicio=inicio, fin=fin, slot=None, lugar="Bienestar (2.º piso)")


def _assert_no_overlap(*, participante: Participantes, inicio: dt.datetime, fin: dt.datetime):
    conflict = HorariosParticipante.objects.filter(
        participantes_id_participante=participante,
    ).filter(_overlap_q(inicio, fin)).exists()
    if conflict:
        raise ValidationError(f"Conflicto de horario para {participante.nombre} {participante.apellido}.")

# ----------------------------
# Vista principal
# ----------------------------
@login_required
def create_appointment(request):
    """
    Agendar cita:
      - Resuelve estudiante/profesional
      - Determina slot o duración por defecto (45m)
      - Verifica solapes (estudiante y profesional)
      - Crea Cita (+ dos HorariosParticipante)
      - Reserva slot (si pudo)
      - Historial
    NOTA: EstadosCita/MotivosCita tienen OneToOne circular con Citas; este código
    crea la cita sin estado si la BD permite NULL en esa columna. Si tu BD no lo
    permite, verás un IntegrityError con una guía para ajustar el modelo/tabla.
    """
    professionals = _get_professionals()

    if request.method == "POST":
        profesional_id = (request.POST.get("profesional_id") or "").strip()
        fecha_raw      = (request.POST.get("fecha") or "").strip()
        motivo         = (request.POST.get("motivo") or "").strip()
        observaciones  = (request.POST.get("observaciones") or "").strip()

        # Validaciones mínimas
        if not profesional_id:
            messages.error(request, "Selecciona un profesional.")
            return render(request, "appointments/create_appointment.html", {"professionals": professionals})

        fecha_inicio = _parse_dt_local(fecha_raw)
        if not fecha_inicio:
            messages.error(request, "Fecha/hora inválida. Usa el selector o formato correcto.")
            return render(request, "appointments/create_appointment.html", {"professionals": professionals})

        if fecha_inicio < now():
            messages.error(request, "La fecha debe ser futura.")
            return render(request, "appointments/create_appointment.html", {"professionals": professionals})

        # Resolver actores
        estudiante = _get_participante_from_user(request.user)
        profesional = get_object_or_404(Participantes, pk=int(profesional_id))

        # Decidir slot o duración por defecto
        decision = _decide_slot_or_duration(profesional=profesional, inicio=fecha_inicio)
        inicio, fin = decision.inicio, decision.fin

        # Validar solapes
        try:
            _assert_no_overlap(participante=estudiante, inicio=inicio, fin=fin)
            _assert_no_overlap(participante=profesional, inicio=inicio, fin=fin)
        except ValidationError as ve:
            messages.error(request, f"No se pudo agendar: {ve}")
            return render(request, "appointments/create_appointment.html", {"professionals": professionals})

        # Persistencia
        try:
            with transaction.atomic():
                # 1) Crear la CITA
                #    OJO: por el OneToOne circular con EstadosCita/MotivosCita dejamos esos campos fuera.
                cita = Citas.objects.create(
                    fecha=inicio,
                    motivo=(motivo or None),
                    observaciones=(observaciones or None),
                    participantes_id_participante=estudiante,
                    participantes_id_participante2=profesional,
                    agenda_psicologos_id_agenda_slot=decision.slot  # puede ser None
                )

                 # Estado por-cita (tu esquema lo modela así: 1 a 1)
                estado = EstadosCita.objects.create(    nombre="Programada",citas_id_cita=cita)
                cita.estados_cita_id_estado_cita = estado
                cita.save(update_fields=["estados_cita_id_estado_cita"])

                # 2) Marcar slot como RESERVADO (si aplica)
                if decision.slot:
                    decision.slot.estado_slot = "RESERVADO"
                    decision.slot.save(update_fields=["estado_slot"])

                # 3) Crear eventos de calendario (HorariosParticipante)
                HorariosParticipante.objects.create(
                    participantes_id_participante=estudiante,
                    titulo="Cita psicológica",
                    fecha_inicio=inicio,
                    fecha_fin=fin,
                    fuente_manual="N",
                    citas_id_cita=cita,
                    notas=None,
                )
                HorariosParticipante.objects.create(
                    participantes_id_participante=profesional,
                    titulo="Cita psicológica (atención)",
                    fecha_inicio=inicio,
                    fecha_fin=fin,
                    fuente_manual="N",
                    citas_id_cita=cita,
                    notas=None,
                )

                # 4) Historial
                HistorialCitas.objects.create(
                    citas_id_cita=cita,
                    participantes_id_participante=estudiante,
                    fecha=now(),
                    nota="Cita programada."
                )

                # 5) (Opcional) Notificaciones — cuando tengas el servicio de notificaciones
                # Notificaciones.objects.create(...)

        except IntegrityError as ie:
            # Suele aparecer si la tabla de Citas NO permite NULL en estados_cita_id_estado_cita
            messages.error(
                request,
                "No se pudo crear la cita por una restricción de base de datos (EstadosCita/MotivosCita "
                "OneToOne). Sugerencia: cambiar esos campos a ForeignKey (catálogo) o permitir NULL en la tabla."
            )
            return render(request, "appointments/create_appointment.html", {"professionals": professionals})
        except Exception as e:
            messages.error(request, f"No se pudo agendar la cita: {e}")
            return render(request, "appointments/create_appointment.html", {"professionals": professionals})

        messages.success(request, "¡Cita programada! Revisa los detalles abajo.")
        return redirect("appointments:detail", cita.id_cita)

    # GET
    return render(request, "appointments/create_appointment.html", {"professionals": professionals})

def _aware(dtobj: dt.datetime | None):
    if not dtobj:
        return None
    return make_aware(dtobj, get_current_timezone()) if is_naive(dtobj) else dtobj


@login_required
def appointment_detail(request, id: int):
    cita = get_object_or_404(
        Citas.objects.select_related(
            "participantes_id_participante",
            "participantes_id_participante2",
            "agenda_psicologos_id_agenda_slot",
            "estados_cita_id_estado_cita",
        ),
        pk=id,
    )

    me = get_object_or_404(Participantes, user_id=request.user.id)
    if not (me.id_participante in (cita.participantes_id_participante_id,
                                   cita.participantes_id_participante2_id)
            or request.user.is_superuser):
        raise Http404()

    # ←—— AQUI el fix
    inicio = localtime(_aware(cita.fecha))
    if cita.agenda_psicologos_id_agenda_slot_id:
        fin = localtime(_aware(cita.agenda_psicologos_id_agenda_slot.fecha_fin))
        lugar = getattr(cita.agenda_psicologos_id_agenda_slot, "lugar", None) or "Bienestar (2.º piso)"
    else:
        fin = inicio + dt.timedelta(minutes=45)
        lugar = "Bienestar (2.º piso)"

    return render(request, "appointments/detail.html", {
        "cita": cita,
        "codigo": cita.id_cita,
        "estudiante": cita.participantes_id_participante,
        "profesional": cita.participantes_id_participante2,
        "inicio": inicio, "fin": fin, "lugar": lugar,
        "estado": getattr(cita.estados_cita_id_estado_cita, "nombre", "Programada"),
        "motivo": cita.motivo or "", "observaciones": cita.observaciones or "",
    })


@login_required
def appointments_home(request):
    return render(request, "appointments/home.html")

@login_required
def my_appointments(request):
    me = get_object_or_404(Participantes, user_id=request.user.id)
    rows = (
        Citas.objects
        .select_related("participantes_id_participante2",
                        "agenda_psicologos_id_agenda_slot",
                        "estados_cita_id_estado_cita")
        .filter(participantes_id_participante=me)
        .order_by("-fecha")
    )
    items = []
    for c in rows:
        inicio = localtime(_aware(c.fecha))
        if c.agenda_psicologos_id_agenda_slot_id:
            fin = localtime(_aware(c.agenda_psicologos_id_agenda_slot.fecha_fin))
            lugar = getattr(c.agenda_psicologos_id_agenda_slot, "lugar", None) or "Bienestar (2.º piso)"
        else:
            fin = inicio + dt.timedelta(minutes=45)
            lugar = "Bienestar (2.º piso)"
        items.append({
            "id": c.id_cita,
            "inicio": inicio,
            "fin": fin,
            "lugar": lugar,
            "profesional": f"{c.participantes_id_participante2.nombre} {c.participantes_id_participante2.apellido}",
            "estado": getattr(c.estados_cita_id_estado_cita, "nombre", "Programada"),
        })
     
    return render(
        request,
        "appointments/list.html",
        {"items": items, "is_pro": False, "allow_student_actions": True}
    )


@login_required
def my_appointments_pro(request):
    """Citas donde el usuario logueado es el profesional asignado."""
    me = get_object_or_404(Participantes, user_id=request.user.id)

    rows = (
        Citas.objects
        .select_related("participantes_id_participante",
                        "participantes_id_participante2",
                        "agenda_psicologos_id_agenda_slot",
                        "estados_cita_id_estado_cita")
        .filter(participantes_id_participante2=me)
        .order_by("-fecha")
    )

    items = []
    for c in rows:
        inicio = localtime(_aware(c.fecha))
        if c.agenda_psicologos_id_agenda_slot_id:
            fin = localtime(_aware(c.agenda_psicologos_id_agenda_slot.fecha_fin))
            lugar = getattr(c.agenda_psicologos_id_agenda_slot, "lugar", None) or "Bienestar (2.º piso)"
        else:
            fin = inicio + dt.timedelta(minutes=45)
            lugar = "Bienestar (2.º piso)"
        items.append({
            "id": c.id_cita,
            "inicio": inicio,
            "fin": fin,
            "lugar": lugar,
            "estudiante": f"{c.participantes_id_participante.nombre} {c.participantes_id_participante.apellido}",
            "estado": getattr(c.estados_cita_id_estado_cita, "nombre", "Programada"),
        })

    # Reutilizaremos el mismo template de lista con una bandera para mostrar acciones
    return render(request, "appointments/list.html", {"items": items, "is_pro": True})

def _ensure_estado_programada(cita):
    # por si no existe el registro OneToOne (bases viejas)
    from universitaryWellbeing.models import EstadosCita
    est = getattr(cita, "estados_cita_id_estado_cita", None)
    if est_id := getattr(cita, "estados_cita_id_estado_cita_id", None):
        return cita.estados_cita_id_estado_cita
    return EstadosCita.objects.create(nombre="Programada", citas_id_cita=cita)

def _set_estado(cita, nombre: str):
    est = _ensure_estado_programada(cita)
    est.nombre = nombre
    est.save(update_fields=["nombre"])

@login_required
def appointment_cancel(request, id: int):
    me = get_object_or_404(Participantes, user_id=request.user.id)
    cita = get_object_or_404(
        Citas.objects.select_related(
            "participantes_id_participante",
            "participantes_id_participante2",
            "agenda_psicologos_id_agenda_slot",
        ),
        pk=id,
    )

    if not (
        me.id_participante in (
            cita.participantes_id_participante_id,
            cita.participantes_id_participante2_id,
        ) or request.user.is_superuser
    ):
        raise Http404()

    try:
        with transaction.atomic():
            # 1) Estado
            _set_estado(cita, "Cancelada")

            # 2) Liberar slot por PK (escribe directo en DB)
            if cita.agenda_psicologos_id_agenda_slot_id:
                updated = AgendaPsicologos.objects.filter(
                    pk=cita.agenda_psicologos_id_agenda_slot_id
                ).update(estado_slot="DISPONIBLE")
                # opcional: asegurar que sí actualizó
                # if updated != 1:
                #     raise RuntimeError("No se pudo liberar el slot")

            # 3) Borrar eventos calendario
            HorariosParticipante.objects.filter(citas_id_cita=cita).delete()

            # 4) Historial
            HistorialCitas.objects.create(
                citas_id_cita=cita,
                participantes_id_participante=me,
                fecha=now(),
                nota="Cita cancelada.",
            )

        messages.success(request, "Cita cancelada.")
    except Exception as e:
        messages.error(request, f"No se pudo cancelar: {e}")

    go_pro = (me.id_participante == cita.participantes_id_participante2_id)
    return redirect("appointments:pro_list" if go_pro else "appointments:list")



#@require_POST
@login_required
def appointment_reschedule(request, id: int):
    new_raw = (request.POST.get("new_fecha") or "").strip()
    if not new_raw:
        messages.error(request, "Debes seleccionar nueva fecha/hora.")
        return redirect("appointments:detail", id)

    new_inicio = _parse_dt_local(new_raw)
    if not new_inicio or new_inicio < now():
        messages.error(request, "Fecha/hora inválida o pasada.")
        return redirect("appointments:detail", id)

    me = get_object_or_404(Participantes, user_id=request.user.id)
    cita = get_object_or_404(
        Citas.objects.select_related("participantes_id_participante",
                                     "participantes_id_participante2",
                                     "agenda_psicologos_id_agenda_slot"),
        pk=id
    )

    # Permisos
    if not (me.id_participante in (cita.participantes_id_participante_id,
                                   cita.participantes_id_participante2_id)
            or request.user.is_superuser):
        raise Http404()

    estudiante  = cita.participantes_id_participante
    profesional = cita.participantes_id_participante2

    # decidir slot nuevo
    decision = _decide_slot_or_duration(profesional=profesional, inicio=new_inicio)
    new_inicio, new_fin = decision.inicio, decision.fin

    # chequear solapes
    try:
        _assert_no_overlap(participante=estudiante,  inicio=new_inicio, fin=new_fin)
        _assert_no_overlap(participante=profesional, inicio=new_inicio, fin=new_fin)
    except ValidationError as ve:
        messages.error(request, f"No se pudo reprogramar: {ve}")
        return redirect("appointments:detail", id)

    try:
        with transaction.atomic():
            old_slot = cita.agenda_psicologos_id_agenda_slot

            # actualizar cita
            cita.fecha = new_inicio
            cita.agenda_psicologos_id_agenda_slot = decision.slot
            cita.save(update_fields=["fecha", "agenda_psicologos_id_agenda_slot"])

            # liberar slot anterior
            if old_slot and getattr(old_slot, "estado_slot", "").upper() == "RESERVADO":
                old_slot.estado_slot = "DISPONIBLE"
                old_slot.save(update_fields=["estado_slot"])

            # reservar nuevo slot (si hay)
            if decision.slot:
                decision.slot.estado_slot = "RESERVADO"
                decision.slot.save(update_fields=["estado_slot"])

            # mover eventos calendario
            for hp in HorariosParticipante.objects.filter(citas_id_cita=cita):
                hp.fecha_inicio = new_inicio
                hp.fecha_fin    = new_fin
                hp.save(update_fields=["fecha_inicio", "fecha_fin"])

            # estado
            _set_estado(cita, "Reprogramada")

            # historial
            HistorialCitas.objects.create(
                citas_id_cita=cita,
                participantes_id_participante=me,
                fecha=now(),
                nota=f"Cita reprogramada para {localtime(new_inicio).strftime('%d/%m/%Y %H:%M')}."
            )

        messages.success(request, "Cita reprogramada.")
    except Exception as e:
        messages.error(request, f"No se pudo reprogramar: {e}")

    go_pro = (me.id_participante == cita.participantes_id_participante2_id)
    return redirect("appointments:pro_list" if go_pro else "appointments:list")

