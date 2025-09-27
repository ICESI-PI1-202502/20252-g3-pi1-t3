import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.contrib import messages
from django.db.models import Max
from universitaryWellbeing.models import (
 Torneos, Disciplinas, EstadosTorneo, Equipos
)
from django.http import Http404



def _get(id_: int):
    for t in DEMO_TOURNAMENTS:
        if t["id"] == id_:
            return t
    raise Http404("Torneo no encontrado")

# Historia 1: lista
def lista_torneos(request):
    q = (request.GET.get("q") or "").strip().lower()

    # Traemos SOLO columnas válidas y el nombre de la disciplina
    rows = (
        Torneos.objects
        .values(
            "id_torneo", "nombre", "fecha_inicio", "fecha_fin",
            "aforo_equipos", "disciplinas_id_disciplina__nombre"
        )
        .order_by("-fecha_inicio")
    )

    items = []
    for r in rows:
        item = {
            "id": int(r["id_torneo"]),
            "nombre": r["nombre"],
            "fecha_inicio": r["fecha_inicio"],
            "fecha_fin": r["fecha_fin"],
            "disciplina": r["disciplinas_id_disciplina__nombre"] or "",
            # Heurística simple: si tiene aforo_equipos, lo tratamos como torneo por equipos
            "tiene_equipos": bool(r["aforo_equipos"]),
        }
        if not q or q in item["nombre"].lower() or q in item["disciplina"].lower():
            items.append(item)

    return render(
        request,
        "list_tournament.html",
        {"tournaments": items, "search": request.GET.get("q", "")},
    )

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

# Historia 6: Crear Torneo ()
def crear_torneo(request):
    disciplinas = Disciplinas.objects.all().order_by("id_disciplina")
    print("Disciplinas count:", disciplinas.count())

    if request.method == "POST":
        nombre        = (request.POST.get("nombre") or "").strip()
        disciplina_id = (request.POST.get("disciplina") or "").strip()
        fecha_inicio  = (request.POST.get("fecha_inicio") or "").strip()  # input type=date → 'YYYY-MM-DD'
        fecha_fin     = (request.POST.get("fecha_fin") or "").strip()
        aforo         = (request.POST.get("aforo") or "").strip()

        # Validations
        if not nombre or not disciplina_id or not fecha_inicio or not fecha_fin:
            messages.error(request, "Completa nombre, disciplina y fechas.")
            return redirect("tournaments:create")
        
        next_id = (Torneos.objects.aggregate(Max("id_torneo"))["id_torneo__max"] or 0) + 1

        try:
            Torneos.objects.create(
                id_torneo=next_id,
                nombre=nombre,
                disciplinas_id_disciplina_id=disciplina_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estados_torneo_id_estado_torneo_id=1,  
                reglas_elegibilidad=None,
                aforo_equipos=(aforo or None),
            )
        except Exception as e:
            print("Error creating torneo:", e)
            messages.error(request, f"No se pudo crear el torneo: {e}")
            return redirect("tournaments:create")
        
        messages.success(request, "Torneo creado correctamente.")
        return redirect("tournaments:list")
    # GET
    return render(request, "create_tournament.html", {"disciplinas": disciplinas}) 
  