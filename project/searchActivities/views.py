from collections import defaultdict
from functools import reduce
import operator

from django.db.models import Q, F, Value
from django.db.models.functions import Lower
from django.shortcuts import render

from universitaryWellbeing.models import (
    Actividades, TiposActividad, HorariosBloque, HorariosActividad
)

# Postgres helpers (si tienes pg_trgm y unaccent)
try:
    from django.contrib.postgres.search import TrigramSimilarity
    from django.contrib.postgres.functions import Unaccent # type: ignore
    PG_TRIGRAM_AVAILABLE = True
except Exception:
    # En caso extremo de entorno que no tenga psycopg/postgres contrib
    PG_TRIGRAM_AVAILABLE = False
    Unaccent = None  # type: ignore

DIAS_REV = {0:"Lunes",1:"Martes",2:"Miércoles",3:"Jueves",4:"Viernes",5:"Sábado",6:"Domingo"}

def search(request):
    q = (request.GET.get("q") or "").strip()
    tipo_id = (request.GET.get("tipo") or "").strip()
    only_available = request.GET.get("only") == "1"

    qs = Actividades.objects.all()

    # ---------- Filtro por NOMBRE (acentos y typos) ----------
    if q:
        # normalizamos el query
        q_lower = q.lower()
        terms = [t for t in q_lower.split() if t]

        if PG_TRIGRAM_AVAILABLE:
            # Requiere extensiones en Postgres:
            #   CREATE EXTENSION IF NOT EXISTS unaccent;
            #   CREATE EXTENSION IF NOT EXISTS pg_trgm;
            # 1) Normaliza campo nombre: unaccent + lower
            qs = qs.annotate(
                norm_name=Unaccent(Lower(F('nombre'))) # type: ignore
            )
            # 2) Trigram similarity contra el query normalizado
            qs = qs.annotate(
                sim=TrigramSimilarity(F('norm_name'), Unaccent(Value(q_lower))) # type: ignore
            )
            # 3) Filtro por tokens (AND de icontains sin acentos)
            tokens_and = reduce(
                operator.and_,
                (Q(norm_name__icontains=t) for t in terms),
                Q()  # identidad neutra
            ) if terms else Q()

            # 4) Aceptamos si (todos los tokens aparecen) OR (sim ≥ umbral)
            #    Umbral típico 0.2 - 0.3; lo dejamos sensible para typos
            qs = qs.filter(tokens_and | Q(sim__gte=0.20))
        else:
            # Fallback sin trigram: lower() + icontains combinando AND de tokens
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

    for a in acts:
        a['items_dia'] = daywise_por_act.get(a['id_actividad'], [])

    # ---------- Tipos ----------
    # Anotamos 'nombre' desde 'nombre_tipo' para usarlo fácil en el template
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
    return render(request, "search.html", ctx)
