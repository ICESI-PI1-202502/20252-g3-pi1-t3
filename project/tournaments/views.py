from datetime import date
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# ===== Datos MOCK para la demo UI =====
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
@login_required
def inscripcion_individual(request, id: int):
    torneo = _get(id)
    if torneo["tiene_equipos"]:
        raise Http404("Este torneo no es individual.")

    if request.method == "POST":
        correo = (request.POST.get("correo") or "").strip()
        if not correo:
            messages.error(request, "Ingresa tu correo institucional.")
        else:
            messages.success(request, f"Inscripción registrada para {correo} (demo).")
            return redirect("tournaments:detail", id=id)

    return render(request, "join_individual.html", {"tournament": torneo})

# Historia 4: crear equipo (demo)
@login_required
def crear_equipo(request, id: int):
    torneo = _get(id)
    if not torneo["tiene_equipos"]:
        raise Http404("Este torneo no es por equipos.")
    if request.method == "POST":
        messages.success(request, "Equipo creado (demo).")
        return redirect("tournaments:detail", id=id)
    return render(request, "create_team.html", {"tournament": torneo})

# Historia 5: unirse a equipo (demo)
@login_required
def unirse_equipo(request, id: int):
    torneo = _get(id)
    if not torneo["tiene_equipos"]:
        raise Http404("Este torneo no es por equipos.")
    if request.method == "POST":
        messages.success(request, "Solicitud enviada (demo).")
        return redirect("tournaments:detail", id=id)
    return render(request, "join_team.html", {"tournament": torneo, "teams": torneo.get("teams", [])})
