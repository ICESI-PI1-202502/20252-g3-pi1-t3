
from django.db.models import Count  # Import correction
from  universitaryWellbeing.models import Participaciones, Asistencias, Actividades, TiposActividad, GruposActividad, Grupos
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

def create_Activities(request):
    tipos = TiposActividad.objects.all().order_by("id_tipo")  # ordenados por id

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        espacio = request.POST.get("espacio")
        horario = request.POST.get("horario")
        tipo_id = request.POST.get("tipo")

        # ejemplo de cómo podrías guardarlo (si tu modelo Actividad tiene tipo):
        # tipo = TiposActividad.objects.get(pk=tipo_id)
        # Actividad.objects.create(nombre=nombre, espacio=espacio, horario=horario, tipo=tipo)

    return render(request, "form_activities.html", {"tipos": tipos})

def add_schedule(request):
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    horas = ["07:00","08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00"]
    return render(request, "schedule.html", {"dias_semana": dias_semana, "horas": horas})

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