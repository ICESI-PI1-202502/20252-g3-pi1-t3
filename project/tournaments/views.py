from datetime import date
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

DEMO_TOURNAMENTS = [
    {
        "id": 1,
        "nombre": "Torneo de Ajedrez",
        "disciplina": "Ajedrez",
        "fecha_inicio": date(2025, 10, 1),
        "fecha_fin": date(2025, 10, 10),
        "tiene_equipos": False,
        "descripcion": "Competencia individual, rondas suizas y final a 2 partidas.",
        "coordinador": "María Pérez · mperez@uni.edu.co",
    },
    {
        "id": 2,
        "nombre": "Futsala Interfacultades",
        "disciplina": "Futsala",
        "fecha_inicio": date(2025, 11, 5),
        "fecha_fin": date(2025, 11, 20),
        "tiene_equipos": True,
        "aforo_equipos": 16,
        "descripcion": "Fase de grupos + playoffs. Cancha techada.",
        "coordinador": "Juan Rojas · jrojas@uni.edu.co",
        "teams": [
            {"id": 501, "nombre": "Los Cracks"},
            {"id": 502, "nombre": "FC Campus"},
        ],
    },
]

def _get(id_: int):
    for t in DEMO_TOURNAMENTS:
        if t["id"] == id_:
            return t
    raise Http404("Torneo no encontrado")

# Historia 1: lista
def lista_torneos(request):
    q = (request.GET.get("q") or "").strip().lower()
    items = DEMO_TOURNAMENTS
    if q:
        items = [t for t in DEMO_TOURNAMENTS if q in t["nombre"].lower() or q in t["disciplina"].lower()]
    return render(request, "list_tournament.html", {"tournaments": items, "search": request.GET.get("q", "")})

# Historia 2: detalle -> elige template según tiene_equipos
def detalle_torneo(request, id: int):
    t = _get(id)
    ctx = {"tournament": t, "teams": t.get("teams", []) if t["tiene_equipos"] else []}
    template = "detail_team.html" if t["tiene_equipos"] else "detail_individual.html"
    return render(request, template, ctx)

# Historia 3: inscripción individual (demo)
#@login_required
def inscripcion_individual(request, id: int):
    torneo = _get(id)
    if torneo["tiene_equipos"]:
        raise Http404("Este torneo no es individual.")

    ctx = {"tournament": torneo, "ok": False, "errors": {}}

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        apellido = (request.POST.get("apellido") or "").strip()
        cedula = (request.POST.get("cedula") or "").strip()
        correo = (request.POST.get("correo") or "").strip()
        genero = (request.POST.get("genero") or "").strip()

        # Validations
        if not nombre: ctx["errors"]["nombre"] = "Requerido"
        if not apellido: ctx["errors"]["apellido"] = "Requerido"
        if not (cedula.isdigit() and len(cedula) == 10):
            ctx["errors"]["cedula"] = "La cédula debe tener exactamente 10 dígitos"
        try:
            validate_email(correo)
        except ValidationError:
            ctx["errors"]["correo"] = "Formato de correo inválido"
        if genero not in ("Femenino", "Masculino", "Otro"):
            ctx["errors"]["genero"] = "Selecciona un género"

        if not ctx["errors"]:
            ctx.update(ok=True, nombre=nombre, apellido=apellido, correo=correo)

    return render(request, "join_individual.html", ctx)


# Historia 4: crear equipo (demo)
#@login_required
def crear_equipo(request, id: int):
    torneo = _get(id)
    if not torneo["tiene_equipos"]:
        raise Http404("Este torneo no es por equipos.")

    ctx = {"tournament": torneo, "ok": False, "errors": {}}

    if request.method == "POST":
        nombre_equipo     = (request.POST.get("nombre_equipo") or "").strip()
        fecha_creacion    = (request.POST.get("fecha_creacion") or "").strip()
        cantidad_personas = (request.POST.get("cantidad_personas") or "").strip()
        capacidad_min     = (request.POST.get("capacidad_min") or "").strip()
        capacidad_max     = (request.POST.get("capacidad_max") or "").strip()
        id_responsable    = (request.POST.get("id_responsable") or "").strip()

     
        if not nombre_equipo:
            ctx["errors"]["nombre_equipo"] = "Requerido"

        if not fecha_creacion:
            ctx["errors"]["fecha_creacion"] = "Requerida"

        if not capacidad_min.isdigit() or int(capacidad_min) < 1:
            ctx["errors"]["capacidad_min"] = "Debe ser un entero ≥ 1"

        if not capacidad_max.isdigit() or int(capacidad_max) < 1:
            ctx["errors"]["capacidad_max"] = "Debe ser un entero ≥ 1"

        if capacidad_min.isdigit() and capacidad_max.isdigit():
            if int(capacidad_min) > int(capacidad_max):
                ctx["errors"]["capacidad_max"] = "Máximo debe ser ≥ mínimo"

        if cantidad_personas:
            if not cantidad_personas.isdigit() or int(cantidad_personas) < 0:
                ctx["errors"]["cantidad_personas"] = "Debe ser entero ≥ 0"

        if not id_responsable.isdigit():
            ctx["errors"]["id_responsable"] = "Debe ser numérico (ID del participante)"

        # Si todo ok -> “éxito” (demo, sin persistir todavía)
        if not ctx["errors"]:
            ctx.update(ok=True, nombre_equipo=nombre_equipo)

    return render(request, "create_team.html", ctx)

# Historia 5: unirse a equipo (demo)
#@login_required
def unirse_equipo(request, id: int):
    torneo = _get(id)
    if not torneo["tiene_equipos"]:
        raise Http404("Este torneo no es por equipos.")

    ctx = {"tournament": torneo, "teams": torneo.get("teams", []), "ok": False, "errors": {}}

    if request.method == "POST":
        team_id = (request.POST.get("team_id") or "").strip()
        correo = (request.POST.get("correo") or "").strip()
        cedula = (request.POST.get("cedula") or "").strip()

        if not team_id:
            ctx["errors"]["team_id"] = "Selecciona un equipo"
        try:
            validate_email(correo)
        except ValidationError:
            ctx["errors"]["correo"] = "Formato de correo inválido"
        if not (cedula.isdigit() and len(cedula) == 10):
            ctx["errors"]["cedula"] = "La cédula debe tener exactamente 10 dígitos"

        if not ctx["errors"]:
            # demo ok
            elegido = next((t for t in torneo.get("teams", []) if str(t["id"]) == team_id), None)
            ctx.update(ok=True, team=elegido, correo=correo)

    return render(request, "join_team.html", ctx)