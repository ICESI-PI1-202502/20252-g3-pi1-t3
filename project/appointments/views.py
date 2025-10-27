import datetime as dt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.timezone import make_aware, get_current_timezone, is_naive

# IMPORTA TUS MODELOS desde el app donde viven (ajusta el import si tu módulo es otro)
from universitaryWellbeing.models import Participantes  # y luego Citas/Agenda cuando implementemos servicio


# ----------------------------
# Utilidades
# ----------------------------
def _parse_dt_local(s: str):
    """
    Convierte entradas tipo <input type='datetime-local'> o formatos comunes (DD/MM/YYYY hh:mm, con AM/PM),
    y las vuelve timezone-aware con la zona actual del proyecto.
    """
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
    """
    Profesionales autorizados para atender citas.
    Por ahora: usuarios staff/superuser (admins) + (opcional) rol 'Psicólogo' si existe.
    """
    qs = (
        Participantes.objects
        .select_related("user", "roles_id_rol")
        .filter(user__is_active=True)
        .filter(user__is_staff=True)   # criterio base: admin autorizado
        .order_by("nombre", "apellido")
    )
    # Si tuvieras un rol explícito:
    # qs = qs.filter(roles_id_rol__nombre_rol__in=["Psicólogo", "Psicologa", "Ps."])
    return [
        {
            "id": p.id_participante,
            "nombre": f"{p.nombre} {p.apellido}".strip() or p.correo
        }
        for p in qs
    ]


# ----------------------------
# Vista principal
# ----------------------------
@login_required
def create_appointment(request):

    professionals = _get_professionals()

    if request.method == "POST":
        profesional_id = (request.POST.get("profesional_id") or "").strip()
        fecha_raw      = (request.POST.get("fecha") or "").strip()
        motivo         = (request.POST.get("motivo") or "").strip()
        observaciones  = (request.POST.get("observaciones") or "").strip()

        # Validaciones mínimas de UI
        if not profesional_id:
            messages.error(request, "Selecciona un profesional.")
            return render(request, "appointments/create_appointment.html", {
                "professionals": professionals
            })

        fecha = _parse_dt_local(fecha_raw)
        if not fecha:
            messages.error(request, "Fecha/hora inválida. Usa el selector o formato correcto.")
            return render(request, "appointments/create_appointment.html", {
                "professionals": professionals
            })

        # AQUI IREMOS CON LA LÓGICA REAL (servicio de dominio)
        # from .services.appointments import create_appointment as svc_create_appointment
        # try:
        #     cita = svc_create_appointment(
        #         student_user=request.user,
        #         profesional_id=int(profesional_id),
        #         fecha=fecha,
        #         motivo=motivo,
        #         observaciones=observaciones,
        #     )
        #     messages.success(request, f"Cita programada (código: {cita.id_cita}). Revisa tu correo para la confirmación.")
        #     return redirect("appointments:create")  # o a un 'detail'
        # except Exception as e:
        #     messages.error(request, f"No se pudo agendar la cita: {e}")

        # Por ahora (UI only):
        messages.success(
            request,
            "Formulario recibido. La lógica de agendamiento (slots/solapes/notificaciones) se implementará a continuación."
        )
        return redirect("appointments:create")

    # GET
    return render(request, "appointments/create_appointment.html", {
        "professionals": professionals
    })
