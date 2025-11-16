import datetime as dt
from django.http import Http404
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError  # Import correction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.urls import reverse
from collections import defaultdict
from django.db.models import Avg
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from universitaryWellbeing.models import (
    ActividadesGrupos, Actividades, TiposActividad, GruposActividad, Grupos,
    HorariosBloque, HorariosActividad, CalificacionesActividad, Participantes, Participaciones, HorariosParticipante,Noticias
)

def _draft_keys(grupo_actividad_id, actividad_id=None):
    suf = f"{grupo_actividad_id}_{actividad_id}" if actividad_id else f"{grupo_actividad_id}_new"
    # base de actividad, lista de bloques, y último bloque en edición (form)
    return (f"cadi_draft_base_{suf}", f"cadi_sched_list_{suf}", f"cadi_sched_last_{suf}")

DIAS_MAP = {
    'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
    'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
}
DIAS_REV = {
    0: "Lunes", 1: "Martes", 2: "Miércoles",
    3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
}

def is_admin(user):
    return user.is_authenticated and user.is_staff

def superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return render(request, "pageNotFound-404.html", status=404)
        return view_func(request, *args, **kwargs)
    return wrapper


DRAFT_KEY_BASE = "cadi_draft_base_{ga}"
DRAFT_KEY_SCHED = "cadi_draft_sched_{ga}"



DUMMY_DATE = dt.datetime(2000, 1, 1)

def hhmm_to_dt(hhmm: str | None):
    """
    '15:00' -> datetime con la hora/minuto indicados (fecha de hoy). None si vacío o inválido.
    """
    s = (hhmm or "").strip()
    if not s:
        return None
    try:
        h, m = map(int, s.split(":"))
        return dt.datetime.combine(dt.date.today(), dt.time(hour=h, minute=m))
    except Exception:
        return None

def date_input_to_dt(s: str | None):
    """
    'YYYY-MM-DD' (input type="date") -> datetime YYYY-MM-DD 00:00:00 (naive). None si vacío.
    """
    s = (s or "").strip()
    if not s:
        return None
    try:
        d = dt.date.fromisoformat(s)  # acepta '2025-10-13'
        return dt.datetime.combine(d, dt.time(0, 0))
    except Exception:
        return None

def cadi_index(request):
    grupo = get_object_or_404(Grupos, pk=1)  # por ejemplo, CADI con id=1
    grupos_actividad = GruposActividad.objects.filter(grupos_id_grupo=grupo)
    return render(request, "listar_grupos_actividades.html", {
        "grupo": grupo,
        "grupos_actividad": grupos_actividad
    })

@superuser_required
@login_required
def createActivities(request, grupo_nombre, grupo_id, grupo_actividad_id):
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id)
    slug_real = slugify(grupo_actividad.grupos_id_grupo.nombre)
    tipos = TiposActividad.objects.all().order_by("id_tipo")

    k_base, k_list, k_last = _draft_keys(grupo_actividad_id)

    # Reset borradores
    if request.method == "GET" and request.GET.get("reset") == "1":
        for k in (k_base, k_list, k_last):
            request.session.pop(k, None)
        request.session.modified = True

    if request.method == "POST":
        action = request.POST.get("action")  # "schedule" o "confirm"
        base = {
            "nombre": request.POST.get("nombre") or "",
            "tipo_id": request.POST.get("tipo") or "",
            "aforo": request.POST.get("aforo") or "",
            "descripcion": request.POST.get("descripcion") or "",
            "requiere": request.POST.get("requiere_inscripcion") or "",
            "fecha_apertura_ins": request.POST.get("fecha_apertura_ins") or "",
            "fecha_cierre_ins": request.POST.get("fecha_cierre_ins") or "",
        }
        request.session[k_base] = base
        request.session.modified = True

        if action == "schedule":
            return redirect("management_cadi:schedule_draft",
                            grupo_nombre=slug_real,
                            grupo_id=grupo_actividad.grupos_id_grupo.id_grupo,
                            grupo_actividad_id=grupo_actividad.id_grupo_actividad)

        if action == "confirm":
            
            if not base.get("nombre") or not base.get("tipo_id"):
                sched_list = request.session.get(k_list) or []
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": {"bloques": sched_list},
                    "modo": "create",
                    "error": "Por favor completa Nombre y Tipo. El Espacio se define en cada horario.",
                })

            tipo = TiposActividad.objects.filter(pk=base["tipo_id"]).first()
            requiere_char = "S" if base.get("requiere") == "si" else "N"
            aforo_val = int(base["aforo"]) if base.get("aforo") else None

            sched_list = request.session.get(k_list) or []  # lista de bloques

            try:
                with transaction.atomic():
                    # 1) actividad
                    actividad = Actividades.objects.create(
                        nombre=base["nombre"],
                        descripcion=base["descripcion"] or None,
                        requiere_inscripcion=requiere_char,
                        modalidad=None,
                        aforo=aforo_val,
                        fecha_apertura_ins=date_input_to_dt(base.get("fecha_apertura_ins")),
                        fecha_cierre_ins=date_input_to_dt(base.get("fecha_cierre_ins")),
                        tipos_actividad_id_tipo=tipo,
                    )

                    # 2) relación con grupo
                    ActividadesGrupos.objects.create(
                        grupos_actividad=grupo_actividad,
                        actividad=actividad,
                    )

                    # 3) crear **todos** los bloques + días (cada bloque trae su 'lugar')
                    for b in sched_list:
                        dt_ini = hhmm_to_dt(b.get("hora_inicio"))
                        dt_fin = hhmm_to_dt(b.get("hora_fin"))
                        if not (dt_ini and dt_fin and dt_fin > dt_ini):
                            continue
                        bloque = HorariosBloque.objects.create(
                            actividades_id_actividad=actividad,
                            hora_inicio=dt_ini.time(),
                            hora_fin=dt_fin.time(),
                            profesor=(b.get("profesor") or None),
                            lugar=(b.get("lugar") or None),
                        )
                        for dname in (b.get("dias") or []):
                            dd = DIAS_MAP.get(dname.lower().strip())
                            if dd is not None:
                                HorariosActividad.objects.create(
                                    actividades_id_actividad=actividad,
                                    horario_bloque=bloque,
                                    dia_semana=dd,
                                )

            except IntegrityError:
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": {"bloques": sched_list},
                    "modo": "create",
                    "error": "Ya existe una actividad con ese nombre.",
                })

            # limpiar sesión
            for k in (k_base, k_list, k_last):
                request.session.pop(k, None)
            request.session.modified = True

            return redirect("management_cadi:listar_actividades",
                            grupo_nombre=slug_real,
                            grupo_id=grupo_actividad.grupos_id_grupo.id_grupo,
                            grupo_actividad_id=grupo_actividad.id_grupo_actividad)

    # GET normal: render del form
    base = request.session.get(k_base, {})
    sched_list = request.session.get(k_list, [])
    return render(request, "form_activities.html", {
        "tipos": tipos,
        "grupo_actividad": grupo_actividad,
        "draft": base,
        "sched": {"bloques": sched_list},
        "modo": "create",
    })

@superuser_required
@login_required
def editActivity(request, grupo_nombre, grupo_id, grupo_actividad_id, actividad_id):
    grupo = get_object_or_404(Grupos, pk=grupo_id)
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id, grupos_id_grupo=grupo)
    actividad = get_object_or_404(Actividades, pk=actividad_id)

    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect("management_cadi:editar_actividad", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad.id_actividad)

    tipos = TiposActividad.objects.all().order_by("id_tipo")
    k_base, k_list, k_last = _draft_keys(grupo_actividad_id, actividad_id)

    if request.method == "POST":
        action = request.POST.get("action")

        base = {
            "nombre": request.POST.get("nombre") or "",
            "tipo_id": request.POST.get("tipo") or "",
            "aforo": request.POST.get("aforo") or "",
            "descripcion": request.POST.get("descripcion") or "",
            "requiere": request.POST.get("requiere_inscripcion") or "",
            "fecha_apertura_ins": request.POST.get("fecha_apertura_ins") or "",
            "fecha_cierre_ins": request.POST.get("fecha_cierre_ins") or "",
        }
        request.session[k_base] = base
        request.session.modified = True

        if action == "schedule":
            return redirect("management_cadi:schedule_draft_edit",
                            grupo_nombre=slug_real,
                            grupo_id=grupo.id_grupo,
                            grupo_actividad_id=grupo_actividad.id_grupo_actividad,
                            actividad_id=actividad.id_actividad)

        if action == "confirm":
            # validar
            if not base["nombre"] or not base["tipo_id"]:
                sched_list = request.session.get(k_list) or []
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": {"bloques": sched_list},
                    "modo": "edit",
                    "error": "Por favor completa Nombre y Tipo.",
                })

            try:
                tipo_id_int = int(base["tipo_id"])
            except ValueError:
                sched_list = request.session.get(k_list) or []
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": {"bloques": sched_list},
                    "modo": "edit",
                    "error": "Tipo de actividad inválido.",
                })

            requiere_char = "S" if base.get("requiere") == "si" else "N"
            aforo_val = int(base["aforo"]) if base.get("aforo") else None
            sched_list = request.session.get(k_list) or []

            try:
                with transaction.atomic():
                    # Actualiza actividad
                    actividad.nombre = base["nombre"]
                    actividad.descripcion = base["descripcion"] or None
                    actividad.requiere_inscripcion = requiere_char
                    actividad.aforo = aforo_val
                    actividad.fecha_apertura_ins = date_input_to_dt(base.get("fecha_apertura_ins"))
                    actividad.fecha_cierre_ins = date_input_to_dt(base.get("fecha_cierre_ins"))
                    f = Actividades._meta.get_field("tipos_actividad_id_tipo")
                    setattr(actividad, f.attname, tipo_id_int)
                    actividad.save()

                    # Reemplaza **todos** los bloques y días por lo que hay en la lista
                    HorariosActividad.objects.filter(actividades_id_actividad=actividad).delete()
                    HorariosBloque.objects.filter(actividades_id_actividad=actividad).delete()

                    for b in sched_list:
                        dt_ini = hhmm_to_dt(b.get("hora_inicio"))
                        dt_fin = hhmm_to_dt(b.get("hora_fin"))
                        if not (dt_ini and dt_fin and dt_fin > dt_ini):
                            continue
                        bloque = HorariosBloque.objects.create(
                            actividades_id_actividad=actividad,
                            hora_inicio=dt_ini.time(),
                            hora_fin=dt_fin.time(),
                            profesor=(b.get("profesor") or None),
                            lugar=(b.get("lugar") or None),
                        )
                        for dname in (b.get("dias") or []):
                            dd = DIAS_MAP.get(dname.lower().strip())
                            if dd is not None:
                                HorariosActividad.objects.create(
                                    actividades_id_actividad=actividad,
                                    horario_bloque=bloque,
                                    dia_semana=dd,
                                )

            except IntegrityError:
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": {"bloques": sched_list},
                    "modo": "edit",
                    "error": "Ya existe una actividad con ese nombre.",
                })

            # Limpia solo listas de horarios (puedes limpiar base si quieres)
            for k in (k_list, k_last):
                request.session.pop(k, None)
            request.session.modified = True

            return redirect("management_cadi:listar_actividades",
                            grupo_nombre=slug_real,
                            grupo_id=grupo.id_grupo,
                            grupo_actividad_id=grupo_actividad.id_grupo_actividad)

    # GET: precarga base y **lista de bloques** si aún no existe en sesión
    draft = {
        "nombre": actividad.nombre or "",
        "tipo_id": getattr(actividad.tipos_actividad_id_tipo, "id_tipo", "") or "",
        "aforo": actividad.aforo or "",
        "descripcion": actividad.descripcion or "",
        "requiere": "si" if (actividad.requiere_inscripcion or "").strip() == "S" else "no",
        "fecha_apertura_ins": (actividad.fecha_apertura_ins.date().isoformat() if actividad.fecha_apertura_ins else ""),
        "fecha_cierre_ins": (actividad.fecha_cierre_ins.date().isoformat() if actividad.fecha_cierre_ins else ""),
    }
    request.session[k_base] = draft
    request.session.modified = True

    sched_list = request.session.get(k_list)
    if sched_list is None:
        # construir lista desde BD
        sched_list = []
        bloques = HorariosBloque.objects.filter(actividades_id_actividad=actividad).order_by("hora_inicio","hora_fin")
        for b in bloques:
            dias_nums = list(HorariosActividad.objects.filter(horario_bloque=b).values_list('dia_semana', flat=True))
            sched_list.append({
                "profesor": b.profesor or "",
                "lugar": b.lugar or "",
                "hora_inicio": b.hora_inicio.strftime("%H:%M"),
                "hora_fin": b.hora_fin.strftime("%H:%M"),
                "dias": [DIAS_REV[d] for d in sorted(dias_nums)],
            })
        request.session[k_list] = sched_list
        request.session.modified = True

    return render(request, "form_activities.html", {
        "tipos": tipos,
        "grupo_actividad": grupo_actividad,
        "draft": draft,
        "sched": {"bloques": sched_list},
        "modo": "edit",
    })

@login_required
def showActivities(request, grupo_nombre, grupo_id, grupo_actividad_id):
    grupo = get_object_or_404(Grupos, pk=grupo_id)
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id, grupos_id_grupo=grupo)

    # Verificar si el nombre del grupo coincide con el slug real
    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect("management_cadi:listar_actividades", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

    # URL para crear actividad
    crear_url = reverse("management_cadi:crear_actividad", kwargs={
        "grupo_nombre": slug_real,
        "grupo_id": grupo.id_grupo,
        "grupo_actividad_id": grupo_actividad.id_grupo_actividad,
    })

    # Obtener las actividades asociadas al grupo
    actividades_ids = ActividadesGrupos.objects.filter(grupos_actividad_id=grupo_actividad_id).values_list("actividad_id", flat=True)
    actividades = list(
        Actividades.objects
        .filter(id_actividad__in=actividades_ids)
        .values("id_actividad", "nombre", "descripcion")
        .order_by("nombre")
    )

    # Traer bloques y días de las actividades
    bloques = list(
        HorariosBloque.objects
        .filter(actividades_id_actividad__in=[a["id_actividad"] for a in actividades])
        .values("id_horario_bloque", "actividades_id_actividad", "profesor", "lugar", "hora_inicio", "hora_fin")
    )
    dias = list(
        HorariosActividad.objects
        .filter(horario_bloque_id__in=[b["id_horario_bloque"] for b in bloques])
        .values("horario_bloque_id", "dia_semana")
    )

    dias_por_bloque = defaultdict(list)
    for d in dias:
        dias_por_bloque[d["horario_bloque_id"]].append(d["dia_semana"])

    # Construir la salida "día a día"
    daywise_por_act = defaultdict(list)
    for b in bloques:
        bdias = sorted(dias_por_bloque.get(b["id_horario_bloque"], []))
        for d in bdias:
            daywise_por_act[b["actividades_id_actividad"]].append({
                "dia": DIAS_REV[d],
                "horario": f'{b["hora_inicio"].strftime("%H:%M")}–{b["hora_fin"].strftime("%H:%M")}',
                "espacio": b["lugar"],
                "profesor": b["profesor"],
            })

    # Calcular y asignar el promedio de calificación y la imagen correspondiente a cada actividad
    for a in actividades:
        # Calcular el promedio de las calificaciones
        promedio_calificacion = CalificacionesActividad.objects.filter(actividades_id_actividad=a["id_actividad"]).aggregate(Avg('estrellas'))['estrellas__avg']
        promedio_calificacion = promedio_calificacion if promedio_calificacion is not None else 0

        # Asignar el promedio de calificación
        a["promedio_calificacion"] = promedio_calificacion

        # Asignar la imagen de la calificación según el promedio
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

        # Asignar URL de edición
        a["editar_url"] = reverse("management_cadi:editar_actividad", kwargs={
            "grupo_nombre": slug_real,
            "grupo_id": grupo.id_grupo,
            "grupo_actividad_id": grupo_actividad.id_grupo_actividad,
            "actividad_id": a["id_actividad"],
        })
        # Asignar los bloques y días de la actividad
        a["items_dia"] = daywise_por_act.get(a["id_actividad"], [])

    for a in actividades:
        ya_califico = CalificacionesActividad.objects.filter(
            actividades_id_actividad=a["id_actividad"],
            participantes_id_participante__user=request.user
        ).exists()
        a["user_has_calificado"] = ya_califico


    return render(request, "listar_actividades.html", {
        "grupo": grupo,
        "grupo_actividad": grupo_actividad,
        "actividades": actividades,
        "crear_url": crear_url,
    })

@login_required
def showGroupActivities(request, grupo_nombre, grupo_id):
    grupo = get_object_or_404(Grupos, pk=grupo_id)
    grupos_actividad = GruposActividad.objects.filter(grupos_id_grupo=grupo)

    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect("management_cadi:listar_grupos_actividad", slug_real, grupo.id_grupo)

    descripciones = {
        1: "En el Centro Artístico y Deportivo (CADI) de la Universidad Icesi, promovemos tu salud y bienestar integral, enfocándonos en desarrollar y mejorar tus capacidades físicas y motrices. Aquí, encontrarás el apoyo y las oportunidades necesarias para mantenerte activo a través de actividades artísticas y deportivas, contribuyendo a tu bienestar general. Estamos comprometidos con acompañarte en cada paso de tu camino universitario.",
        2: "El programa de Desarrollo Humano y Promoción de la Salud busca fomentar hábitos saludables y el crecimiento personal.",
        3: "¡Tienes algo para dar… y el Proyecto Social de Bienestar Universitario (PSU) tiene algo para darte! A través de nuestro programa de voluntariado, no solo te brindamos la oportunidad de servir, sino también de crecer. Contribuimos al progreso de la sociedad mediante el servicio y la formación de los estudiantes de nuestra universidad y las comunidades en las que intervenimos.",
        4: "¿Te imaginas llegar a una ciudad nueva y sentirte como en casa desde el primer día? ¡Eso es precisamente lo que buscamos con nuestro programa! Está pensado especialmente para los estudiantes que vienen de fuera de Cali para iniciar su aventura universitaria en Icesi."
    }

    descripcion = descripciones.get(grupo.id_grupo, "")

    return render(request, "listar_grupos_actividades.html", {
        "grupo": grupo,
        "grupos_actividad": grupos_actividad,
        "descripcion": descripcion,
    })

@login_required
@superuser_required
def createGroupActivity(request, grupo_nombre, grupo_id):
    grupo = get_object_or_404(Grupos, pk=grupo_id)

    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect("management_cadi:crear_grupo_actividad", slug_real, grupo.id_grupo)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        imagen_file = request.FILES.get("imagenActividad")

        # El Postgres genera el id
        ga = GruposActividad.objects.create(
            grupos_id_grupo=grupo,
            nombre=nombre,
            descripcion=descripcion,
            imagen=imagen_file,
        )
        # ga.id_grupo_actividad contiene el id autogenerado

        return redirect(
            "management_cadi:listar_grupos_actividad",
            grupo_nombre=slug_real,
            grupo_id=grupo.id_grupo
        )

    return render(request, "form_gruposActivi.html", {"grupo": grupo})


@login_required
@superuser_required
def create_news(request):
    if request.method == "POST":
        titulo = request.POST.get("titulo")
        enunciado = request.POST.get("enunciado")
        descripcion = request.POST.get("descripcion")
        imagen_file = request.FILES.get("imagen")

        # Creamos la noticia
        noticia = Noticias.objects.create(
            titulo=titulo,
            enunciado=enunciado,
            descripcion=descripcion,
            imagen=imagen_file,
        )

        slug_real = slugify(noticia.titulo)

        # Redirigimos a una página de detalle o listado
        return redirect("management_cadi:detalle_noticia", slug=slug_real, id=noticia.id)

    return render(request, "form_news.html")

@login_required
@superuser_required
def edit_news(request, id):
    noticia = get_object_or_404(Noticias, id=id)

    if request.method == "POST":
        noticia.titulo = request.POST.get("titulo")
        noticia.enunciado = request.POST.get("enunciado")
        noticia.autor = request.POST.get("autor")
        noticia.descripcion = request.POST.get("descripcion")

        imagen_file = request.FILES.get("imagen")
        if imagen_file:
            noticia.imagen = imagen_file

        noticia.save()

        slug_real = slugify(noticia.titulo)

        return redirect("management_cadi:detalle_noticia", slug=slug_real, id=noticia.id)

    return render(request, "edit_news.html", {"noticia": noticia})

@login_required
@superuser_required
def delete_news(request, id):
    noticia = get_object_or_404(Noticias, id=id)

    if request.method == "POST":
        noticia.delete()
        return redirect("management_cadi:listar_noticias")

    return render(request, "delete_confirm.html", {"noticia": noticia})

def news_detail(request, slug, id):
    noticia = get_object_or_404(Noticias, id=id)
    return render(request, "detail_news.html", {"noticia": noticia})


def list_news(request):
    noticias = Noticias.objects.all()  # Puedes agregar filtros si es necesario
    paginator = Paginator(noticias, 10)  # Muestra 10 noticias por página

    page = request.GET.get("page")
    noticias_pag = paginator.get_page(page)

    return render(request, "list_news.html", {
        "noticias": noticias_pag
    })

@login_required
@superuser_required
def manage_news(request):
    if not request.user.is_superuser:
        raise Http404("No tienes permiso para acceder a esta sección.")  # Solo superusuarios pueden gestionar noticias
    
    noticias = Noticias.objects.all()  # Obtener todas las noticias
    paginator = Paginator(noticias, 10)
    page = request.GET.get("page")
    noticias_pag = paginator.get_page(page)

    return render(request, 'manage_news.html', {'noticias': noticias_pag})

@login_required
@superuser_required
def scheduleDraft(request, grupo_nombre, grupo_id, grupo_actividad_id, actividad_id=None):
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id)
    grupo = grupo_actividad.grupos_id_grupo
    slug_real = slugify(grupo.nombre)

    modo = "edit" if actividad_id else "create"
    if grupo_nombre != slug_real:
        if actividad_id:
            return redirect("management_cadi:schedule_draft_edit",
                            slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad_id)
        return redirect("management_cadi:schedule_draft",
                        slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

    k_base, k_list, k_last = _draft_keys(grupo_actividad_id, actividad_id)
    horas = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0,30)]  # cada 30 min
    dias_labels = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    # Inicializa lista de bloques si no existe (en edición, la precarga la hace editar_actividad)
    if request.method == "GET" and request.GET.get("init") == "1":
        if request.session.get(k_list) is None:
            request.session[k_list] = []
            request.session.modified = True

    # Acciones POST: agregar/eliminar/terminar
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_block":
            profesor = (request.POST.get("profesor") or "").strip()
            lugar = (request.POST.get("lugar") or "").strip()
            h_ini = (request.POST.get("hora_inicio") or "").strip()
            h_fin = (request.POST.get("hora_fin") or "").strip()
            dias = request.POST.getlist("dias") or []
            # validación simple
            dt_ini = hhmm_to_dt(h_ini)
            dt_fin = hhmm_to_dt(h_fin)
            if not (dt_ini and dt_fin and dt_fin > dt_ini and dias):
                # guarda inputs en k_last para no perderlos
                request.session[k_last] = {"profesor": profesor, "lugar": lugar, "hora_inicio": h_ini, "hora_fin": h_fin, "dias": dias}
                request.session.modified = True
            else:
                lst = request.session.get(k_list, [])
                lst.append({"profesor": profesor, "lugar": lugar, "hora_inicio": h_ini, "hora_fin": h_fin, "dias": dias})
                request.session[k_list] = lst
                request.session.pop(k_last, None)
                request.session.modified = True
            return redirect("management_cadi:schedule_draft_edit" if actividad_id else "management_cadi:schedule_draft",
                            slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad_id) if actividad_id \
                   else redirect("management_cadi:schedule_draft", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

        if action == "delete_block":
            idx = request.POST.get("idx")
            lst = request.session.get(k_list, [])
            try:
                i = int(idx)
                if 0 <= i < len(lst):
                    lst.pop(i)
                    request.session[k_list] = lst
                    request.session.modified = True
            except Exception:
                pass
            return redirect("management_cadi:schedule_draft_edit" if actividad_id else "management_cadi:schedule_draft",
                            slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad_id) if actividad_id \
                   else redirect("management_cadi:schedule_draft", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

        if action == "done":
            # volver a la pantalla de crear/editar
            if actividad_id:
                return redirect("management_cadi:editar_actividad",
                                slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad_id)
            return redirect("management_cadi:crear_actividad",
                            slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

    # GET: render del form de bloques
    last = request.session.get(k_last, {"profesor":"", "lugar":"", "hora_inicio":"", "hora_fin":"", "dias":[]})
    lst = request.session.get(k_list, [])
    return render(request, "schedule.html", {
        "modo": modo,
        "horas": horas,
        "dias_semana": dias_labels,
        "last": last,       # el formulario del bloque actual
        "bloques": lst,     # la lista acumulada
    })
