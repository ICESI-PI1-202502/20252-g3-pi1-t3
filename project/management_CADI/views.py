
from django.db.models import Count
from django.db import transaction, IntegrityError  # Import correction
from  universitaryWellbeing.models import ActividadesGrupos, Actividades, TiposActividad, GruposActividad, Grupos
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import Max

def is_admin(user):
    return user.is_authenticated and user.is_staff

# @user_passes_test(is_admin)  # Uncomment if you want to restrict access

DRAFT_KEY_BASE = "cadi_draft_base_{ga}"
DRAFT_KEY_SCHED = "cadi_draft_sched_{ga}"

import datetime as dt

DUMMY_DATE = dt.datetime(2000, 1, 1)

def hhmm_to_dt(hhmm: str | None):
    """
    '15:00' -> dt.datetime(<hoy>, 15:00)
    ''/None  -> None
    """
    if not hhmm:
        return None
    try:
        h, m = map(int, hhmm.split(":"))
        return dt.datetime.combine(dt.date.today(), dt.time(hour=h, minute=m))
    except ValueError:
        return None


def _draft_keys(grupo_actividad_id, actividad_id=None):
    suf = f"{grupo_actividad_id}_{actividad_id}" if actividad_id else f"{grupo_actividad_id}_new"
    return (
        f"cadi_draft_base_{suf}",
        f"cadi_draft_sched_{suf}",
    )


def cadi_index(request):
    grupo = get_object_or_404(Grupos, pk=1)  # por ejemplo, CADI con id=1
    grupos_actividad = GruposActividad.objects.filter(grupos_id_grupo=grupo)
    return render(request, "listar_grupos_actividades.html", {
        "grupo": grupo,
        "grupos_actividad": grupos_actividad
    })

def create_Activities(request, grupo_nombre, grupo_id, grupo_actividad_id):
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id)
    slug_real = slugify(grupo_actividad.grupos_id_grupo.nombre)
    tipos = TiposActividad.objects.all().order_by("id_tipo")

    k_base, k_sched = _draft_keys(grupo_actividad_id)

    # (opcional) reset por querystring ?reset=1 para limpiar borradores
    if request.method == "GET" and request.GET.get("reset") == "1":
        request.session.pop(k_base, None)
        request.session.pop(k_sched, None)
        request.session.modified = True

    if request.method == "POST":
        action = request.POST.get("action")  # "schedule" o "confirm"

        # Guardar borrador base en sesión
        base = {
            "nombre": request.POST.get("nombre") or "",
            "espacio": request.POST.get("espacio") or "",
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
            return redirect(
                "management_cadi:schedule_draft",
                grupo_nombre=slug_real,
                grupo_id=grupo_actividad.grupos_id_grupo.id_grupo,
                grupo_actividad_id=grupo_actividad.id_grupo_actividad,
            )

        if action == "confirm":
            if not base.get("nombre") or not base.get("espacio") or not base.get("tipo_id"):
                sched = request.session.get(k_sched) or {}
                return render(
                    request,
                    "form_activities.html",
                    {
                        "tipos": tipos,
                        "grupo_actividad": grupo_actividad,
                        "draft": base,
                        "sched": sched,
                        "error": "Por favor completa Nombre, Espacio y Tipo.",
                    },
                )

            tipo = TiposActividad.objects.filter(pk=base["tipo_id"]).first()
            requiere_char = "S" if base.get("requiere") == "si" else "N"
            aforo_val = int(base["aforo"]) if base.get("aforo") else None

            # Horario desde sesión
            sched = request.session.get(k_sched) or {}
            profesor = (sched.get("profesor") or "").strip()
            dias = sched.get("dias") or []
            dt_ini = hhmm_to_dt((sched.get("hora_inicio") or "").strip())
            dt_fin = hhmm_to_dt((sched.get("hora_fin") or "").strip())

            try:
                with transaction.atomic():
                    # 1) crear actividad (NO asignes id_actividad)
                    actividad = Actividades.objects.create(
                        nombre=base["nombre"],
                        descripcion=base["descripcion"] or None,
                        lugar=base["espacio"],
                        requiere_inscripcion=requiere_char,
                        modalidad=None,
                        aforo=aforo_val,
                        fecha_apertura_ins=base.get("fecha_apertura_ins") or None,
                        fecha_cierre_ins=base.get("fecha_cierre_ins") or None,
                        tipos_actividad_id_tipo=tipo,
                        profesor=profesor or None,
                        dias_semana=", ".join(dias) or None,
                        fecha_inicio=dt_ini,
                        fecha_fin=dt_fin,
                    )

                    # 2) crear fila puente usando NOMBRES DE CAMPO del modelo
                    ActividadesGrupos.objects.create(
                        grupos_actividad=grupo_actividad,
                        actividad=actividad,
                    )

                    # (opcional) si tu modelo de Actividades NO mapea act_grup_id, no intentes setearlo:
                    # actividad.act_grup_id = ...
                    # actividad.save(...)

            except IntegrityError:
                # Por índice único (nombre CI) u otro choque
                return render(
                    request,
                    "form_activities.html",
                    {
                        "tipos": tipos,
                        "grupo_actividad": grupo_actividad,
                        "draft": base,
                        "sched": sched,
                        "error": "Ya existe una actividad con ese nombre.",
                    },
                )

            # limpiar borradores
            request.session.pop(k_base, None)
            request.session.pop(k_sched, None)
            request.session.modified = True

            return redirect(
                "management_cadi:listar_actividades",
                grupo_nombre=slug_real,
                grupo_id=grupo_actividad.grupos_id_grupo.id_grupo,
                grupo_actividad_id=grupo_actividad.id_grupo_actividad,
            )

    # GET: precargar con borradores de sesión (si existen)
    base = request.session.get(k_base, {})
    sched = request.session.get(k_sched, {})
    return render(
        request,
        "form_activities.html",
        {
            "tipos": tipos,
            "grupo_actividad": grupo_actividad,
            "draft": base,
            "sched": sched,
        },
    )



# management_CADI/views.py (listar_actividades)
def listar_actividades(request, grupo_nombre, grupo_id, grupo_actividad_id):
    grupo = get_object_or_404(Grupos, pk=grupo_id)
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id, grupos_id_grupo=grupo)

    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect("management_cadi:listar_actividades", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

    crear_url = reverse("management_cadi:crear_actividad", kwargs={
        "grupo_nombre": slug_real,
        "grupo_id": grupo.id_grupo,
        "grupo_actividad_id": grupo_actividad.id_grupo_actividad,
    })

    actividades_ids = ActividadesGrupos.objects.filter(
        grupos_actividad_id=grupo_actividad_id
    ).values_list("actividad_id", flat=True)

    actividades = list(
        Actividades.objects
        .filter(id_actividad__in=actividades_ids)
        .values("id_actividad", "nombre", "dias_semana", "lugar", "profesor",
                "fecha_inicio", "fecha_fin")  # <- añade estos dos
        .order_by("nombre")
    )


    # adjuntar URL de edición a cada item
    for a in actividades:
        a["editar_url"] = reverse("management_cadi:editar_actividad", kwargs={
            "grupo_nombre": slug_real,
            "grupo_id": grupo.id_grupo,
            "grupo_actividad_id": grupo_actividad.id_grupo_actividad,
            "actividad_id": a["id_actividad"],
        })

    return render(request, "listar_actividades.html", {
        "grupo": grupo,
        "grupo_actividad": grupo_actividad,
        "actividades": actividades,
        "crear_url": crear_url,
    })



def editar_actividad(request, grupo_nombre, grupo_id, grupo_actividad_id, actividad_id):
    grupo = get_object_or_404(Grupos, pk=grupo_id)
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id, grupos_id_grupo=grupo)
    actividad = get_object_or_404(Actividades, pk=actividad_id)

    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect(
            "management_cadi:editar_actividad",
            slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad.id_actividad
        )

    tipos = TiposActividad.objects.all().order_by("id_tipo")
    k_base, k_sched = _draft_keys(grupo_actividad_id)

    if request.method == "POST":
        action = request.POST.get("action")

        base = {
            "nombre": request.POST.get("nombre") or "",
            "espacio": request.POST.get("espacio") or "",
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
            sched = request.session.get(k_sched) or {}
            dias_list_bd = [d.strip() for d in (actividad.dias_semana or "").split(",") if d.strip()]

            merged = {
                "profesor": (sched.get("profesor") or actividad.profesor or "").strip(),
                # MUY IMPORTANTE: si en la sesión no hay horas, no metas '' (déjalo sin clave)
                "dias": sched.get("dias") or dias_list_bd,
            }
            if sched.get("hora_inicio"):
                merged["hora_inicio"] = sched["hora_inicio"]
            if sched.get("hora_fin"):
                merged["hora_fin"] = sched["hora_fin"]

            request.session[k_sched] = merged
            request.session.modified = True

            return redirect(
                "management_cadi:schedule_draft_edit",
                grupo_nombre=slug_real,
                grupo_id=grupo.id_grupo,
                grupo_actividad_id=grupo_actividad.id_grupo_actividad,
                actividad_id=actividad.id_actividad,
            )

        if action == "confirm":
            sched = request.session.get(k_sched) or {}
            profesor = (sched.get("profesor") or "").strip()
            dias = sched.get("dias") or []

            dt_ini = hhmm_to_dt((sched.get("hora_inicio") or "").strip())
            dt_fin = hhmm_to_dt((sched.get("hora_fin") or "").strip())

            if not base["nombre"] or not base["espacio"] or not base["tipo_id"]:
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": {
                        "profesor": profesor,
                        "dias": dias,
                        "hora_inicio": sched.get("hora_inicio",""),
                        "hora_fin": sched.get("hora_fin","")
                    },
                    "modo": "edit",
                    "error": "Por favor completa Nombre, Espacio y Tipo.",
                })

            tipo = TiposActividad.objects.filter(pk=base["tipo_id"]).first()
            requiere_char = "S" if base.get("requiere") == "si" else "N"
            aforo_val = int(base["aforo"]) if base.get("aforo") else None

            try:
                with transaction.atomic():
                    actividad.nombre = base["nombre"]
                    actividad.descripcion = base["descripcion"] or None
                    actividad.lugar = base["espacio"]
                    actividad.requiere_inscripcion = requiere_char
                    actividad.aforo = aforo_val
                    actividad.fecha_apertura_ins = base.get("fecha_apertura_ins") or None
                    actividad.fecha_cierre_ins = base.get("fecha_cierre_ins") or None
                    actividad.tipos_actividad_id_tipo = tipo
                    actividad.profesor = profesor or None
                    actividad.dias_semana = ", ".join(dias) or None
                    actividad.fecha_inicio = dt_ini
                    actividad.fecha_fin = dt_fin
                    actividad.save()
            except IntegrityError:
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": {
                        "profesor": profesor,
                        "dias": dias,
                        "hora_inicio": sched.get("hora_inicio",""),
                        "hora_fin": sched.get("hora_fin","")
                    },
                    "modo": "edit",
                    "error": "Ya existe una actividad con ese nombre.",
                })

            request.session.pop(k_sched, None)
            request.session.modified = True

            return redirect(
                "management_cadi:listar_actividades",
                grupo_nombre=slug_real,
                grupo_id=grupo.id_grupo,
                grupo_actividad_id=grupo_actividad.id_grupo_actividad,
            )

    # GET: precargar
    draft = {
        "nombre": actividad.nombre or "",
        "espacio": actividad.lugar or "",
        "tipo_id": getattr(actividad.tipos_actividad_id_tipo, "id_tipo", "") or "",
        "aforo": actividad.aforo or "",
        "descripcion": actividad.descripcion or "",
        "requiere": "si" if (actividad.requiere_inscripcion or "").strip() == "S" else "no",
        "fecha_apertura_ins": actividad.fecha_apertura_ins or "",
        "fecha_cierre_ins": actividad.fecha_cierre_ins or "",
    }
    dias_list = [d.strip() for d in (actividad.dias_semana or "").split(",") if d.strip()]

    sched = request.session.get(k_sched) or {}
    resumen_sched = {
        "profesor": sched.get("profesor", actividad.profesor or ""),
        "hora_inicio": sched.get("hora_inicio", ""),
        "hora_fin": sched.get("hora_fin", ""),
        "dias": sched.get("dias", dias_list),
    }

    return render(request, "form_activities.html", {
        "tipos": tipos,
        "grupo_actividad": grupo_actividad,
        "draft": draft,
        "sched": resumen_sched,
        "modo": "edit",
    })




def listar_grupos_actividad(request, grupo_nombre, grupo_id):
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


def crear_grupo_actividad(request, grupo_nombre, grupo_id):
    grupo = get_object_or_404(Grupos, pk=grupo_id)

    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect("management_cadi:crear_grupo_actividad", slug_real, grupo.id_grupo)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        imagen_file = request.FILES.get("imagenActividad")

        # ❌ eliminar:
        # ultimo_actividad = GruposActividad.objects.aggregate(Max("id_grupo_actividad"))["id_grupo_actividad__max"]
        # nuevo_id = (ultimo_actividad or 0) + 1

        # ✅ dejar que Postgres genere el id
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


def schedule_draft(request, grupo_nombre, grupo_id, grupo_actividad_id, actividad_id=None):
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id)
    grupo = grupo_actividad.grupos_id_grupo
    slug_real = slugify(grupo.nombre)

    if grupo_nombre != slug_real:
        if actividad_id:
            return redirect("management_cadi:schedule_draft_edit", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad_id)
        return redirect("management_cadi:schedule_draft", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

    k_base, k_sched = _draft_keys(grupo_actividad_id)
    horas = [f"{h:02d}:00" for h in range(7, 22)]

    # GET en edición: completa sesión desde BD si faltan datos
    # GET en edición: precarga desde BD SOLO si la sesión no lo tiene aún
    if request.method == "GET" and actividad_id:
        actividad = get_object_or_404(Actividades, pk=actividad_id)
        sched = request.session.get(k_sched) or {}

        if not sched.get("profesor"):
            sched["profesor"] = actividad.profesor or ""

        if not sched.get("dias"):
            sched["dias"] = [d.strip() for d in (actividad.dias_semana or "").split(",") if d.strip()]

        # NUEVO: precargar horas si no están en sesión
        if not sched.get("hora_inicio") and actividad.fecha_inicio:
            sched["hora_inicio"] = actividad.fecha_inicio.strftime("%H:%M")
        if not sched.get("hora_fin") and actividad.fecha_fin:
            sched["hora_fin"] = actividad.fecha_fin.strftime("%H:%M")

        request.session[k_sched] = sched
        request.session.modified = True


    if request.method == "POST":
        profesor = (request.POST.get("profesor") or "").strip()
        h_ini = (request.POST.get("hora_inicio") or "").strip()
        h_fin = (request.POST.get("hora_fin") or "").strip()
        dias = request.POST.getlist("dias") or []

        request.session[k_sched] = {
            "profesor": profesor,
            "hora_inicio": h_ini,
            "hora_fin": h_fin,
            "dias": dias,
        }
        request.session.modified = True

        if actividad_id:
            return redirect("management_cadi:editar_actividad", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad, actividad_id)
        return redirect("management_cadi:crear_actividad", slug_real, grupo.id_grupo, grupo_actividad.id_grupo_actividad)

    sched = request.session.get(k_sched, {})
    return render(request, "schedule.html", {
        "horas": horas,
        "dias_semana": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"],
        "draft": {
            "profesor": sched.get("profesor", ""),
            "hora_inicio": sched.get("hora_inicio", ""),
            "hora_fin": sched.get("hora_fin", ""),
            "dias": sched.get("dias", []),
        },
    })

