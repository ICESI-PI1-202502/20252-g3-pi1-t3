# Gestionar equipo (demo)
import traceback
from django.views.decorators.csrf import csrf_exempt
import datetime as dt
from django.utils import timezone 
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import make_aware, get_current_timezone
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.db import transaction, IntegrityError, DataError, DatabaseError, ProgrammingError, connection
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Max
from universitaryWellbeing.models import (
 Torneos, Disciplinas, EstadosTorneo, Equipos, TorneosEquipos, EquiposParticipantes, Participantes
)
from django.http import Http404

def get_torneo_or_404(id_: int):
    t = get_object_or_404(
        Torneos.objects.select_related("disciplinas_id_disciplina"),
        pk=id_
    )

    data = {
        "id": t.id_torneo,
        "nombre": t.nombre,
        "fecha_inicio": t.fecha_inicio,
        "fecha_fin": t.fecha_fin,
        "disciplina": getattr(t.disciplinas_id_disciplina, "nombre", "") or "",
        "aforo_equipos": t.aforo_equipos,
        "tiene_equipos": bool(t.aforo_equipos),
    }

    teams = []
    if data["tiene_equipos"]:
        teams = list(
            Equipos.objects
            .filter(torneosequipos__torneos_id_torneo=id_) 
            .values("id_equipo", "nombre")
            .distinct()
        )

    return data, teams

def _parse_date(s: str):
    if not s:
        return None
    try:
        return dt.datetime.strptime(s, "%Y-%m-%d").date()  # input type=date
    except Exception:
        return None

# Historia : Crear Torneo
def crear_torneo(request):
    disciplinas = Disciplinas.objects.all().order_by("id_disciplina")
    print("Disciplinas count:", disciplinas.count())

    if request.method == "POST":
        nombre        = (request.POST.get("nombre") or "").strip()
        disciplina_id = (request.POST.get("disciplina") or "").strip()
        fecha_inicio  = (request.POST.get("fecha_inicio") or "").strip() 
        fecha_fin     = (request.POST.get("fecha_fin") or "").strip()
        aforo         = (request.POST.get("aforo") or "").strip()

        # Validations
        if not nombre or not disciplina_id or not fecha_inicio or not fecha_fin:
            messages.error(request, "Completa nombre, disciplina y fechas.")
            return redirect("tournaments:create")

        try:
            Torneos.objects.create(
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

# Historia : lista
def lista_torneos(request):
    q = (request.GET.get("q") or "").strip().lower()  

    # Fetch tournaments from DB
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
            "tiene_equipos": bool(r["aforo_equipos"]),
        }
        if not q or q in item["nombre"].lower() or q in item["disciplina"].lower():
            items.append(item)
    return render(request,"list_tournament.html",{"tournaments": items, "search": request.GET.get("q", "")},
    )

# Historia : detalle
def detalle_torneo(request, id: int):
    t, teams = get_torneo_or_404(id)
    template = "detail_team.html" if t["tiene_equipos"] else "detail_individual.html"
    return render(request, template, {"tournament": t, "teams": teams})


# NOT TAKING THIS ONE INTO ACCOUNT
#@login_required
def inscripcion_individual(request, id: int):
    torneo, _ = get_torneo_or_404(id)
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
# Historia 4: crear equipo (real)
def crear_equipo_en_torneo(request, torneo_id: int):
    torneo = get_object_or_404(
        Torneos.objects.select_related("disciplinas_id_disciplina"),
        pk=torneo_id
    )

    # Solo equipos si hay aforo_equipos definido (team-based)
    if not torneo.aforo_equipos:
        messages.error(request, "Este torneo es individual; no permite equipos.")
        return redirect("tournaments:detail", torneo_id)

    if request.method == "GET":
        return render(request, "create_team.html", {
            "tournament": torneo,
            "disciplinas": Disciplinas.objects.all().order_by("nombre"),
            "today": dt.date.today().isoformat(),
        })

    # ---- DEBUG: ver payload entrante
    print("POST payload:", dict(request.POST))

    # POST
    nombre  = (request.POST.get("nombre_equipo") or "").strip()
    resp_id = (request.POST.get("responsable_id") or "").strip()
    disc_id = (request.POST.get("disciplina_id") or "").strip()
    cap_min = (request.POST.get("capacidad_min") or "").strip()
    cap_max = (request.POST.get("capacidad_max") or "").strip()
    f_crea  = (request.POST.get("fecha_creacion") or "").strip()

    errors = {}
    if not nombre: errors["nombre_equipo"] = "Nombre requerido."
    if not resp_id.isdigit(): errors["responsable_id"] = "ID responsable inválido."
    if cap_min and not cap_min.isdigit(): errors["capacidad_min"] = "Debe ser entero."
    if cap_max and not cap_max.isdigit(): errors["capacidad_max"] = "Debe ser entero."
    if cap_min and cap_max and int(cap_min) > int(cap_max):
        errors["capacidad_max"] = "Máximo debe ser ≥ mínimo."
    fecha_creacion = _parse_date(f_crea) or dt.date.today()
    disc_fk = int(disc_id) if disc_id.isdigit() else None

    # ---- FK prechecks (errores humanos más claros que un FK violation)
    if resp_id.isdigit() and not Participantes.objects.filter(pk=int(resp_id)).exists():
        errors["responsable_fk"] = f"Participante {resp_id} no existe."
    if disc_fk and not Disciplinas.objects.filter(pk=disc_fk).exists():
        errors["disciplina_fk"] = f"Disciplina {disc_fk} no existe."

    if errors:
        for e in errors.values():
            messages.error(request, e)
        return redirect("tournaments:create_team", torneo_id)

    try:
        with transaction.atomic():
            new_team_id = None

            # 1) Crear equipo con un savepoint interno
            try:
                with transaction.atomic():  # savepoint
                    team = Equipos.objects.create(
                        nombre=nombre,
                        fecha_creacion=fecha_creacion,             # DateField
                        cantidad_personas=None,
                        participantes_id_participante_id=int(resp_id),
                        disciplinas_id_disciplina_id=disc_fk,
                        capacidad_min=(int(cap_min) if cap_min else None),
                        capacidad_max=(int(cap_max) if cap_max else None),
                    )
                    new_team_id = getattr(team, "id_equipo", None) or getattr(team, "id", None)
                    print("ORM team created:", new_team_id)
            except Exception as orm_err:
                # El fallo del bloque interno NO envenena la transacción externa
                print("ORM insert failed:", repr(orm_err))
                print(traceback.format_exc())
                # 1b) Fallback: SQL crudo con RETURNING
                with connection.cursor() as cur:
                    cur.execute("""
                        INSERT INTO equipos
                            (nombre, fecha_creacion, cantidad_personas,
                             participantes_id_participante, disciplinas_id_disciplina,
                             capacidad_min, capacidad_max)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_equipo
                    """, [
                        nombre, fecha_creacion, None,
                        int(resp_id), disc_fk,
                        (int(cap_min) if cap_min else None),
                        (int(cap_max) if cap_max else None),
                    ])
                    new_team_id = cur.fetchone()[0]
                    print("SQL team created:", new_team_id)

            # 2) Vincular torneo ↔ equipo (savepoint opcional)
            with transaction.atomic():
                obj, created = TorneosEquipos.objects.get_or_create(
                    torneos_id_torneo_id=torneo.id_torneo,
                    equipos_id_equipo_id=new_team_id
                )
                print("Linked Torneo-Equipo:", obj.id, "created:", created)

            # 3) Añadir responsable como miembro (idempotente por UNIQUE)
            with transaction.atomic():
                ep_obj, ep_created = EquiposParticipantes.objects.get_or_create(
                    equipos_id_equipo_id=new_team_id,
                    participantes_id_participante_id=int(resp_id),
                    defaults={"id_participante1": int(resp_id)},
                )
                print("Added responsable:", ep_obj.id, "created:", ep_created)

        messages.success(request, "Equipo creado y vinculado al torneo.")
        return redirect("tournaments:detail", torneo.id_torneo)

    except (IntegrityError, DataError, ProgrammingError, DatabaseError, Exception) as e:
        tb = traceback.format_exc()
        print("crear_equipo_en_torneo error:", repr(e))
        print(tb)
        messages.error(request, f"No se pudo crear el equipo: {e}")
        last = tb.strip().splitlines()[-1] if tb.strip().splitlines() else ""
        if last:
            messages.error(request, last)
        return redirect("tournaments:create_team", torneo_id)


# Historia 5: unirse a equipo (demo)
#@login_required
def unirse_equipo(request, id: int):
    torneo, teams = get_torneo_or_404(id)
    if not torneo["tiene_equipos"]:
        raise Http404("Este torneo no es por equipos.")

    ctx = {"tournament": torneo, "teams": teams, "ok": False, "errors": {}}

    if request.method == "POST":
        team_id = (request.POST.get("team_id") or "").strip()
        correo  = (request.POST.get("correo") or "").strip()
        cedula  = (request.POST.get("cedula") or "").strip()

        if not team_id:
            ctx["errors"]["team_id"] = "Selecciona un equipo"
        try:
            validate_email(correo)
        except ValidationError:
            ctx["errors"]["correo"] = "Formato de correo inválido"
        if not (cedula.isdigit() and len(cedula) == 10):
            ctx["errors"]["cedula"] = "La cédula debe tener exactamente 10 dígitos"

        if not ctx["errors"]:
            elegido = next((t for t in teams if str(t["id_equipo"]) == team_id), None)
            ctx.update(ok=True, team=elegido, correo=correo)

    return render(request, "join_team.html", ctx)



  