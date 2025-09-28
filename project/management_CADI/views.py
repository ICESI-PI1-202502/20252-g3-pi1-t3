
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

def _draft_keys(grupo_actividad_id):
    return (
        DRAFT_KEY_BASE.format(ga=grupo_actividad_id),
        DRAFT_KEY_SCHED.format(ga=grupo_actividad_id),
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

    if request.method == "POST":
        action = request.POST.get("action")  # "schedule" o "confirm"

        # guarda borrador base siempre que venga un POST
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
            # ir a añadir/editar horario en borrador
            return redirect(
                "management_cadi:schedule_draft",
                grupo_nombre=slug_real,
                grupo_id=grupo_actividad.grupos_id_grupo.id_grupo,
                grupo_actividad_id=grupo_actividad.id_grupo_actividad,
            )

        if action == "confirm":
            sched = request.session.get(k_sched) or {}
            if not base.get("nombre") or not base.get("espacio") or not base.get("tipo_id"):
                # faltan campos mínimos
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": sched,
                    "error": "Por favor completa Nombre, Espacio y Tipo.",
                })

            tipo = TiposActividad.objects.filter(pk=base["tipo_id"]).first()
            requiere_char = "S" if base.get("requiere") == "si" else "N"
            aforo_val = float(base["aforo"]) if base.get("aforo") else None

            try:
                # Crear definitivamente dentro de transacción
                with transaction.atomic():
                    ultimo_id = Actividades.objects.aggregate(Max("id_actividad"))["id_actividad__max"]
                    nuevo_id = int((ultimo_id or 0) + 1)

                    actividad = Actividades.objects.create(
                        id_actividad=nuevo_id,
                        nombre=base["nombre"],
                        descripcion=base["descripcion"],
                        lugar=base["espacio"],
                        requiere_inscripcion=requiere_char,
                        modalidad=None,
                        aforo=aforo_val,
                        fecha_apertura_ins=base.get("fecha_apertura_ins") or None,
                        fecha_cierre_ins=base.get("fecha_cierre_ins") or None,
                        tipos_actividad_id_tipo=tipo,
                        profesor=sched.get("profesor") or None,
                        dias_semana=", ".join(sched.get("dias", [])) or None,
                        fecha_inicio=None,
                        fecha_fin=None,
                    )

                    # Verificar si ya existe la relación entre grupo y actividad
                    if not ActividadesGrupos.objects.filter(
                        grupos_actividad=grupo_actividad,
                        actividad=actividad
                    ).exists():
                        # 1) calcular nuevo id de la tabla puente
                        ultimo_puente = ActividadesGrupos.objects.aggregate(
                            Max("id_actividad_grupo")
                        )["id_actividad_grupo__max"] or 0
                        nuevo_id_puente = int(ultimo_puente) + 1

                        # 2) crear la relación
                        puente = ActividadesGrupos.objects.create(
                            grupos_actividad=grupo_actividad,
                            actividad=actividad,
                            id_actividad_grupo=nuevo_id_puente,
                        )
                    else:
                        # Si ya existe la relación, se recupera sin intentar crear una nueva
                        puente = ActividadesGrupos.objects.get(
                            grupos_actividad=grupo_actividad,
                            actividad=actividad
                        )

                    # 3) setear el FK en Actividades y guardar
                    actividad.actividades_grupos_id_actividad_grupo = puente
                    actividad.save(update_fields=["actividades_grupos_id_actividad_grupo"])

            except IntegrityError as e:
                # Si ocurre el error de integridad, muestra un mensaje o maneja el error
                return render(request, "form_activities.html", {
                    "tipos": tipos,
                    "grupo_actividad": grupo_actividad,
                    "draft": base,
                    "sched": sched,
                    "error": f"Se produjo un error al guardar la actividad: {e}. Puede que ya exista una actividad con este grupo.",
                })

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

    # GET: precargar con borradores
    base = request.session.get(k_base, {})
    sched = request.session.get(k_sched, {})
    return render(
        request,
        "form_activities.html",
        {"tipos": tipos, "grupo_actividad": grupo_actividad, "draft": base, "sched": sched},
    )

def listar_actividades(request, grupo_nombre, grupo_id, grupo_actividad_id):
    # Grupo padre (1..4)
    grupo = get_object_or_404(Grupos, pk=grupo_id)

    # Grupo de actividad perteneciente a ese grupo
    grupo_actividad = get_object_or_404(
        GruposActividad,
        pk=grupo_actividad_id,
        grupos_id_grupo=grupo
    )

    # Canonicalizar slug en URL
    slug_real = slugify(grupo.nombre)
    if grupo_nombre != slug_real:
        return redirect(
            "management_cadi:listar_actividades",
            slug_real,
            grupo.id_grupo,
            grupo_actividad.id_grupo_actividad
        )
    
    crear_url = reverse(
        "management_cadi:crear_actividad",
        kwargs={
            "grupo_nombre": slug_real,
            "grupo_id": grupo.id_grupo,
            "grupo_actividad_id": grupo_actividad.id_grupo_actividad,
        },
    )

    # IDs de actividades desde la tabla puente
    # IDs de actividades desde la tabla puente
    actividades_ids = ActividadesGrupos.objects.filter(
        grupos_actividad_id=grupo_actividad_id
    ).values_list("actividad_id", flat=True)

    # Traer solo columnas necesarias para listar (evita el FK largo)
    actividades = list(
        Actividades.objects
        .filter(id_actividad__in=actividades_ids)
        .values("id_actividad", "nombre", "dias_semana", "lugar", "profesor")
        .order_by("nombre")
    )

    return render(request, "listar_actividades.html", {
        "grupo": grupo,
        "grupo_actividad": grupo_actividad,
        "actividades": actividades,  # es una lista de dicts
        "crear_url": crear_url,
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

        ultimo_actividad = GruposActividad.objects.aggregate(Max("id_grupo_actividad"))["id_grupo_actividad__max"]
        nuevo_id = (ultimo_actividad or 0) + 1

        GruposActividad.objects.create(
            id_grupo_actividad=nuevo_id,
            grupos_id_grupo=grupo,
            nombre=nombre,
            descripcion=descripcion,
            imagen=imagen_file
        )

        return redirect("management_cadi:listar_grupos_actividad", grupo_nombre=slug_real, grupo_id=grupo.id_grupo)

    return render(request, "form_gruposActivi.html", {"grupo": grupo})


def schedule_draft(request, grupo_nombre, grupo_id, grupo_actividad_id):
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id)
    slug_real = slugify(grupo_actividad.grupos_id_grupo.nombre)

    k_base, k_sched = _draft_keys(grupo_actividad_id)
    horas = [f"{h:02d}:00" for h in range(7, 22)]

    if request.method == "POST":
        profesor = request.POST.get("nombre") or ""
        h_ini = request.POST.get("hora_inicio") or ""
        h_fin = request.POST.get("hora_fin") or ""
        dias = request.POST.getlist("dias") or []

        request.session[k_sched] = {
            "profesor": profesor,
            "hora_inicio": h_ini,
            "hora_fin": h_fin,
            "dias": dias,
        }
        request.session.modified = True

        # volver a la pantalla de crear actividad (sin crear nada)
        return redirect(
            "management_cadi:crear_actividad",
            grupo_nombre=slug_real,
            grupo_id=grupo_actividad.grupos_id_grupo.id_grupo,
            grupo_actividad_id=grupo_actividad.id_grupo_actividad,
        )

    sched = request.session.get(k_sched, {})
    return render(request, "schedule.html", {
        "horas": horas,
        "dias_semana": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"],
        "draft": sched,
    })
