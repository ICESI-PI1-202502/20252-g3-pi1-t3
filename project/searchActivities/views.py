from collections import defaultdict
from functools import reduce
import operator
from django.db.models import Q, F, Value, Avg
from django.db.models.functions import Lower
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from universitaryWellbeing.models import (
    Actividades, TiposActividad, HorariosBloque, HorariosActividad, CalificacionesActividad, Participantes,
    Participaciones
)

try:
    from django.contrib.postgres.search import TrigramSimilarity
    from django.contrib.postgres.functions import Unaccent  # type: ignore
    PG_TRIGRAM_AVAILABLE = True
except Exception:
    PG_TRIGRAM_AVAILABLE = False
    Unaccent = None  # type: ignore

DIAS_REV = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}

def search(request):


    ##Esto lo usaremos más adelante para validar que se pueda calificar una actividad
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
                norm_name=Unaccent(Lower(F('nombre')))  # type: ignore
            )
            qs = qs.annotate(
                sim=TrigramSimilarity(F('norm_name'), Unaccent(Value(q_lower)))  # type: ignore
            )
            tokens_and = reduce(
                operator.and_,
                (Q(norm_name__icontains=t) for t in terms),
                Q()  # identidad neutra
            ) if terms else Q()

            qs = qs.filter(tokens_and | Q(sim__gte=0.20))
        else:
            qs = qs.annotate(name_lc=Lower(F('nombre')))
            if terms:
                for t in terms:
                    qs = qs.filter(name_lc__icontains=t)
            else:
                qs = qs.filter(name_lc__icontains=q_lower)

    # ---------- Filtro por TIPO ----------
    if tipo_id:
        try:
            qs = qs.filter(tipos_actividad_id_tipo=int(tipo_id))
        except ValueError:
            pass

    # ---------- Solo con horarios ----------
    if only_available:
        qs = qs.filter(
            id_actividad__in=HorariosBloque.objects.values('actividades_id_actividad')
        ).distinct()

    # ---------- Orden ----------
    if PG_TRIGRAM_AVAILABLE and q:
        qs = qs.order_by(F('sim').desc(nulls_last=True), 'nombre')
    else:
        qs = qs.order_by('nombre')

    # ---------- Construcción resultados día a día ----------
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
                'horario': f"{b['hora_inicio'].strftime('%H:%M')}–{b['hora_fin'].strftime('%H:%M')}",
                'espacio': b['lugar'],
                'profesor': b['profesor'],
            })

    # ---------- Calcular promedio de calificación y asignar imagen de calificación ----------
    for a in acts:
        # Calcular el promedio de calificación
        promedio_calificacion = CalificacionesActividad.objects.filter(actividades_id_actividad=a['id_actividad']).aggregate(Avg('estrellas'))['estrellas__avg']
        promedio_calificacion = promedio_calificacion if promedio_calificacion is not None else 0

        # Asignar el promedio de calificación
        a["promedio_calificacion"] = promedio_calificacion

        # Asignar la imagen de calificación según el promedio
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


        # Asignar los bloques y días de la actividad
        a["items_dia"] = daywise_por_act.get(a['id_actividad'], [])

    # ---------- Tipos ----------
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


    # 2) Si hay participante, traemos de una sola vez las actividades
    #    donde YA calificó y donde TIENE participación (evitamos consultas por cada actividad)
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

    # 3) Marcar cada actividad
    for a in acts:
        act_id = a['id_actividad']
        a['user_has_calificado'] = act_id in calificados_ids
        a['user_has_participacion'] = act_id in participados_ids

    # 4) Render
    ctx['actividades'] = acts  # <- este es el que usa tu template
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

