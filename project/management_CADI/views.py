
from django.db.models import Count  # Import correction
from  universitaryWellbeing.models import Participaciones, HorarioActividad, Actividades, TiposActividad, GruposActividad, Grupos
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.db.models import Max

def is_admin(user):
    return user.is_authenticated and user.is_staff

# @user_passes_test(is_admin)  # Uncomment if you want to restrict access

def cadi_index(request):
    grupo = get_object_or_404(Grupos, pk=1)  # por ejemplo, CADI con id=1
    grupos_actividad = GruposActividad.objects.filter(grupos_id_grupo=grupo)
    return render(request, "listar_grupos_actividades.html", {
        "grupo": grupo,
        "grupos_actividad": grupos_actividad
    })

def create_Activities(request, grupo_nombre, grupo_id, grupo_actividad_id):
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id)
    tipos = TiposActividad.objects.all().order_by("id_tipo")

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        lugar = request.POST.get("espacio")
        tipo_id = request.POST.get("tipo")
        tipo = TiposActividad.objects.filter(pk=tipo_id).first()

        actividad = Actividades.objects.create(
            nombre=nombre,
            lugar=lugar,
            tipos_actividad_id_tipo=tipo,
            actividades_grupos=grupo_actividad
        )

        return redirect(
            "management_cadi:listar_actividades",
            grupo_nombre=grupo_nombre,
            grupo_id=grupo_id,
            grupo_actividad_id=grupo_actividad.id_grupo_actividad
        )

    return render(
        request, 
        "form_activities.html", 
        {"tipos": tipos, "grupo_actividad": grupo_actividad}
    )


def listar_actividades(request, grupo_nombre, grupo_id, grupo_actividad_id):
    grupo_actividad = get_object_or_404(GruposActividad, pk=grupo_actividad_id)
    actividades = Actividades.objects.filter(actividades_grupos=grupo_actividad)

    slug_real = slugify(grupo_actividad.nombre)
    if grupo_nombre != slug_real:
        return redirect(
        "management_cadi:listar_actividades",
        grupo_nombre=slug_real,
        grupo_id=grupo_id,
        grupo_actividad_id=grupo_actividad_id
    )

    return render(request, "listar_actividades.html", {
        "grupo_actividad": grupo_actividad,
        "actividades": actividades
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


def add_schedule(request, grupo_nombre, grupo_id, grupo_actividad_id, actividad_id):
    actividad = get_object_or_404(Actividades, pk=actividad_id)

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    horas = [f"{h:02d}:00" for h in range(7, 22)]  # ejemplo: 07:00 - 21:00

    if request.method == "POST":
        profesor = request.POST.get("nombre")
        hora_inicio = request.POST.get("hora_inicio")
        hora_fin = request.POST.get("hora_fin")
        dias = request.POST.getlist("dias")  # lista de días seleccionados

        for dia in dias:
            HorarioActividad.objects.create(
                actividad=actividad,
                dia=dia,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                espacio=actividad.lugar,  # puedes modificar si quieres otro campo
                profesor=profesor
            )

        return redirect(
            "management_cadi:listar_actividades",
            grupo_nombre=grupo_nombre,
            grupo_id=grupo_id,
            grupo_actividad_id=grupo_actividad_id
        )

    return render(request, "schedule.html", {
        "actividad": actividad,
        "dias_semana": dias_semana,
        "horas": horas
    })