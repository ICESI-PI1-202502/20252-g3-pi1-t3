from collections import defaultdict
from functools import reduce
import operator
import datetime as dt
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, F, Value, Avg
from django.db.models.functions import Lower
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from universitaryWellbeing.models import (
    Actividades, TiposActividad, HorariosBloque, HorariosActividad, CalificacionesActividad, Participantes,
    Participaciones, HorariosParticipante
)

try:
    from django.contrib.postgres.search import TrigramSimilarity
    from django.contrib.postgres.functions import Unaccent  # type: ignore
    PG_TRIGRAM_AVAILABLE = True
except Exception:
    PG_TRIGRAM_AVAILABLE = False
    Unaccent = None  # type: ignore

DIAS_REV = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}

@login_required
@require_POST
def add_slot_from_search(request):
    """
    Permite añadir un bloque de horario desde la búsqueda de actividades.
    Aplica la misma lógica de management_cadi:add_slot_to_schedule.
    """
    try:
        participante = Participantes.objects.get(user=request.user)
    except Participantes.DoesNotExist:
        messages.error(request, "No se encontró un perfil de participante asociado a tu usuario.")
        return redirect(request.POST.get("next") or "/buscar/")

    actividad_id = request.POST.get("actividad_id")
    bloque_id = request.POST.get("bloque_id")
    dia_idx_str = request.POST.get("dia_idx")
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/buscar/"

    if not (actividad_id and bloque_id and dia_idx_str):
        messages.error(request, "Solicitud incompleta para agregar el horario.")
        return redirect(next_url)

    try:
        dia_idx = int(dia_idx_str)
    except ValueError:
        messages.error(request, "Día inválido.")
        return redirect(next_url)

    actividad = get_object_or_404(Actividades, pk=actividad_id)
    bloque = get_object_or_404(HorariosBloque, pk=bloque_id, actividades_id_actividad=actividad)

    # calcular próxima fecha
    now = timezone.localtime()
    base = now.date()
    delta = (dia_idx - base.weekday()) % 7
    fecha_obj = base + timedelta(days=delta)
    dt_inicio = timezone.make_aware(datetime.combine(fecha_obj, bloque.hora_inicio))
    dt_fin = timezone.make_aware(datetime.combine(fecha_obj, bloque.hora_fin))
    if delta == 0 and dt_fin <= now:
        fecha_obj = base + timedelta(days=7)
        dt_inicio = timezone.make_aware(datetime.combine(fecha_obj, bloque.hora_inicio))
        dt_fin = timezone.make_aware(datetime.combine(fecha_obj, bloque.hora_fin))

    # evitar duplicados
    if HorariosParticipante.objects.filter(
        participantes_id_participante=participante,
        actividades_id_actividad=actividad,
        fecha_inicio__time=bloque.hora_inicio,
        fecha_fin__time=bloque.hora_fin,
    ).exists():
        messages.info(request, "Este bloque ya está en tu horario.")
        return redirect(next_url)

    # comprobar conflictos
    MARGIN = timedelta(minutes=1)
    wd = dt_inicio.weekday()
    existing_slots = HorariosParticipante.objects.filter(participantes_id_participante=participante)
    for ex in existing_slots:
        ex_s = timezone.localtime(ex.fecha_inicio)
        ex_e = timezone.localtime(ex.fecha_fin)
        if ex_s.weekday() != wd:
            continue
        base_date = dt.date(2000,1,1)
        new_s = datetime.combine(base_date, dt_inicio.timetz().replace(tzinfo=None))
        new_e = datetime.combine(base_date, dt_fin.timetz().replace(tzinfo=None))
        existing_s = datetime.combine(base_date, ex_s.time())
        existing_e = datetime.combine(base_date, ex_e.time())
        if (new_s < (existing_e - MARGIN)) and (existing_s < (new_e - MARGIN)):
            messages.error(request, "No se puede agregar: el horario se cruza con otra actividad.")
            return redirect(next_url)

    # insertar
    try:
        HorariosParticipante.objects.create(
            participantes_id_participante=participante,
            titulo=f"{actividad.nombre}",
            fecha_inicio=dt_inicio,
            fecha_fin=dt_fin,
            fuente_manual="S",
            actividades_id_actividad=actividad,
            notas=f"Bloque {bloque.hora_inicio.strftime('%H:%M')}–{bloque.hora_fin.strftime('%H:%M')}",
        )
        messages.success(request, "Bloque añadido a tu horario.")
    except IntegrityError:
        messages.info(request, "Ya tenías algo igual en ese horario.")
    except Exception:
        messages.error(request, "No se pudo agregar el bloque a tu horario.")
    return redirect(next_url)

def search(request):

    if request.user.is_authenticated:
        try:
            participante = Participantes.objects.get(user=request.user)
        except Participantes.DoesNotExist:
            participante = None
    else:
        participante = None

    q = (request.GET.get("q") or "").strip()
    tipo_id = (request.GET.get("tipo") or "").strip()
    only_available = request.GET.get("only") == "1"

    qs = Actividades.objects.all()

    if q:
        q_lower = q.lower()
        terms = [t for t in q_lower.split() if t]

        if PG_TRIGRAM_AVAILABLE:
            qs = qs.annotate(
                norm_name=Unaccent(Lower(F('nombre')))
            )
            qs = qs.annotate(
                sim=TrigramSimilarity(F('norm_name'), Unaccent(Value(q_lower)))
            )
            tokens_and = reduce(
                operator.and_,
                (Q(norm_name__icontains=t) for t in terms),
                Q()
            ) if terms else Q()
            qs = qs.filter(tokens_and | Q(sim__gte=0.20))
        else:
            qs = qs.annotate(name_lc=Lower(F('nombre')))
            if terms:
                for t in terms:
                    qs = qs.filter(name_lc__icontains=t)
            else:
                qs = qs.filter(name_lc__icontains=q_lower)

    # --- Filtros ---
    if tipo_id:
        try:
            qs = qs.filter(tipos_actividad_id_tipo=int(tipo_id))
        except ValueError:
            pass

    if only_available:
        qs = qs.filter(
            id_actividad__in=HorariosBloque.objects.values('actividades_id_actividad')
        ).distinct()

    if PG_TRIGRAM_AVAILABLE and q:
        qs = qs.order_by(F('sim').desc(nulls_last=True), 'nombre')
    else:
        qs = qs.order_by('nombre')

    # --- Construcción resultados día a día ---
    acts = list(qs.values('id_actividad', 'nombre', 'descripcion'))
    act_ids = [a['id_actividad'] for a in acts]

    bloques = list(
        HorariosBloque.objects
        .filter(actividades_id_actividad__in=act_ids)
        .values('id_horario_bloque', 'actividades_id_actividad', 'profesor', 'lugar', 'hora_inicio', 'hora_fin')
    )
    dias = list(
        HorariosActividad.objects
        .filter(horario_bloque_id__in=[b['id_horario_bloque'] for b in bloques] if bloques else [])
        .values('horario_bloque_id', 'dia_semana')
    )

    dias_por_bloque = defaultdict(list)
    for d in dias:
        dias_por_bloque[d['horario_bloque_id']].append(d['dia_semana'])

    daywise_por_act = defaultdict(list)
    for b in bloques:
        for d in sorted(dias_por_bloque.get(b['id_horario_bloque'], [])):
            daywise_por_act[b['actividades_id_actividad']].append({
                'dia': DIAS_REV[d],
                'dia_idx': d,  # <- necesario para cálculo posterior
                't_ini': b['hora_inicio'],
                't_fin': b['hora_fin'],
                'bloque_id': b['id_horario_bloque'],
                'horario': f"{b['hora_inicio'].strftime('%H:%M')}–{b['hora_fin'].strftime('%H:%M')}",
                'espacio': b['lugar'],
                'profesor': b['profesor'],
            })

    # --- Calificación promedio ---
    for a in acts:
        promedio_calificacion = CalificacionesActividad.objects.filter(
            actividades_id_actividad=a['id_actividad']
        ).aggregate(Avg('estrellas'))['estrellas__avg'] or 0

        a["promedio_calificacion"] = promedio_calificacion

        if promedio_calificacion == 0:
            a["rating_image"] = 'rating_0_0.png'
        elif 0 < promedio_calificacion <= 0.5:
            a["rating_image"] = 'rating_0_5.png'
        elif 0.5 < promedio_calificacion <= 1:
            a["rating_image"] = 'rating_1_0.png'
        elif 1 < promedio_calificacion <= 1.5:
            a["rating_image"] = 'rating_1_5.png'
        elif 1.5 < promedio_calificacion <= 2:
            a["rating_image"] = 'rating_2_0.png'
        elif 2 < promedio_calificacion <= 2.5:
            a["rating_image"] = 'rating_2_5.png'
        elif 2.5 < promedio_calificacion <= 3:
            a["rating_image"] = 'rating_3_0.png'
        elif 3 < promedio_calificacion <= 3.5:
            a["rating_image"] = 'rating_3_5.png'
        elif 3.5 < promedio_calificacion <= 4:
            a["rating_image"] = 'rating_4_0.png'
        elif 4 < promedio_calificacion <= 4.5:
            a["rating_image"] = 'rating_4_5.png'
        else:
            a["rating_image"] = 'rating_5_0.png'

        a["items_dia"] = daywise_por_act.get(a['id_actividad'], [])

    # --- Tipos ---
    tipos = list(
        TiposActividad.objects
        .annotate(nombre=F('nombre_tipo'))
        .values('id_tipo', 'nombre')
        .order_by('nombre')
    )

    selected_tipo_name = None
    if tipo_id:
        t = (TiposActividad.objects
             .filter(id_tipo=tipo_id)
             .annotate(nombre=F('nombre_tipo'))
             .values('nombre')
             .first())
        if t:
            selected_tipo_name = t['nombre']

    ctx = {
        'q': q,
        'tipo_id': tipo_id,
        'only_available': only_available,
        'tipos': tipos,
        'actividades': acts,
        'selected_tipo_name': selected_tipo_name,
        'using_trigram': PG_TRIGRAM_AVAILABLE,
    }

    if participante:
        ids_actividades = [a['id_actividad'] for a in acts]

        calificados_ids = set(
            CalificacionesActividad.objects.filter(
                participantes_id_participante=participante,
                actividades_id_actividad__in=ids_actividades
            ).values_list('actividades_id_actividad', flat=True)
        )

        participados_ids = set(
            Participaciones.objects.filter(
                participantes_id_participante=participante,
                actividades_id_actividad__in=ids_actividades
            ).values_list('actividades_id_actividad', flat=True)
        )
    else:
        calificados_ids = set()
        participados_ids = set()

    for a in acts:
        act_id = a['id_actividad']
        a['user_has_calificado'] = act_id in calificados_ids
        a['user_has_participacion'] = act_id in participados_ids

    # marcar horarios añadidos y detectar conflictos
    if participante:

        MARGIN = timedelta(minutes=1)

        user_slots = list(
            HorariosParticipante.objects.filter(participantes_id_participante=participante)
            .values("fecha_inicio", "fecha_fin", "actividades_id_actividad")
        )

        user_by_weekday = defaultdict(list)
        for s in user_slots:
            fi = timezone.localtime(s["fecha_inicio"])
            ff = timezone.localtime(s["fecha_fin"])
            wd = fi.weekday()
            user_by_weekday[wd].append((fi.time(), ff.time(), s.get("actividades_id_actividad")))

        for a in acts:
            for it in a["items_dia"]:
                item_day = it.get("dia_idx")
                t_ini = it.get("t_ini")
                t_fin = it.get("t_fin")
                added = False
                conflict = False

                for (u_ini, u_fin, u_aid) in user_by_weekday.get(item_day, []):
                    # Si ya tiene ese horario
                    if (u_aid == a["id_actividad"]) and (u_ini == t_ini) and (u_fin == t_fin):
                        added = True

                    # Detección de cruce de horarios con margen de 1 min
                    base_date = dt.date(2000,1,1)
                    new_s = datetime.combine(base_date, t_ini)
                    new_e = datetime.combine(base_date, t_fin)
                    ex_s = datetime.combine(base_date, u_ini)
                    ex_e = datetime.combine(base_date, u_fin)
                    if (new_s < (ex_e - MARGIN)) and (ex_s < (new_e - MARGIN)):
                        conflict = True

                it["already_added"] = added
                it["conflict"] = conflict

    ctx['actividades'] = acts
    return render(request, "search.html", ctx)

@login_required
def rateActivity(request, actividad_id):
    actividad = get_object_or_404(Actividades, pk=actividad_id)

    # 1) Resolver participante del usuario
    try:
        participante = Participantes.objects.get(user=request.user)
    except Participantes.DoesNotExist:
        messages.error(request, "No se encontró un perfil de participante asociado a tu usuario.")
        return redirect(request.GET.get("next") or "searchActivities:search")

    # 2) Verificar que tenga participación en esta actividad (CRÍTICO)
    #    Si necesitas limitar por estado (p. ej. 'asistió'), agrega el filtro por estado aquí.
    tiene_participacion = Participaciones.objects.filter(
        participantes_id_participante=participante,
        actividades_id_actividad=actividad.id_actividad,
        # estados_participacion_id_estado_participacion=ESTADO_ASISTIO,  # opcional
    ).exists()

    if not tiene_participacion:
        messages.error(request, "Solo quienes participaron pueden calificar esta actividad.")
        return redirect(request.GET.get("next") or "searchActivities:search")

    # 3) Obtener o crear calificación del participante para esta actividad
    calificacion, _created = CalificacionesActividad.objects.get_or_create(
        actividades_id_actividad=actividad,
        participantes_id_participante=participante,
        defaults={"estrellas": 0, "comentario": ""},
    )

    # 4) Procesar POST
    if request.method == "POST":
        # Sanitizar estrellas (0 a 5)
        try:
            estrellas = int(request.POST.get("estrellas", 0))
        except (TypeError, ValueError):
            estrellas = 0
        estrellas = max(0, min(5, estrellas))

        comentario = (request.POST.get("comentario") or "").strip()

        calificacion.estrellas = estrellas
        calificacion.comentario = comentario
        calificacion.save(update_fields=["estrellas", "comentario"])

        messages.success(request, "Tu calificación fue guardada correctamente.")

        next_url = request.GET.get("next")
        return redirect(next_url or "searchActivities:search")

    # 5) GET → mostrar formulario
    return render(request, "calificar.html", {
        "actividad": actividad,
        "calificacion": calificacion,
        "stars_range": range(6),
    })

