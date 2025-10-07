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
from django.utils import timezone

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
        "limite_inscripcion": getattr(t, "limite_inscripcion", None),
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
        limite_raw    = (request.POST.get("limite_inscripcion") or "").strip()
        # '2025-10-01T12:30' -> datetime(2025,10,1,12,30)
        limite_inscripcion = None
        if limite_raw:
            try:
                parsed = dt.datetime.fromisoformat(limite_raw)
            except ValueError:
                # No bloqueamos creación; simplemente lo ignoramos por ahora
                pass


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
                limite_inscripcion=limite_inscripcion,
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
    # still reuse your helper
    t, teams = get_torneo_or_404(id)

    # find the team of the logged-in participant in this tournament (if any)
    my_team_id = None
    if t["tiene_equipos"]:
        p = _current_participante(request.user)
        if p:
            my_team_id = (
                EquiposParticipantes.objects
                .filter(
                    participantes_id_participante_id=p.id_participante,
                    equipos_id_equipo__torneosequipos__torneos_id_torneo=id,
                )
                .values_list("equipos_id_equipo_id", flat=True)
                .first()
            )

    template = "detail_team.html" if t["tiene_equipos"] else "detail_individual.html"
    return render(request, template, {"tournament": t, "teams": teams, "my_team_id": my_team_id})


# Historia : crear equipo 
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
                
                print("ORM insert failed:", repr(orm_err))
                print(traceback.format_exc())
               
                with connection.cursor() as cur:
                    cur.execute("""
                        INSERT INTO equipos
                            (nombre, fecha_creacion, cantidad_personas,
                             participantes_id_participante, disciplinas_id_disciplina,
                             capacidad_min, capacidad_max)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_equipo
                    """, [
                        nombre, fecha_creacion.isoformat(), None,
                        int(resp_id), disc_fk,
                        (int(cap_min) if cap_min else None),
                        (int(cap_max) if cap_max else None),
                    ])
                    row = cur.fetchone()
                    if row is None:
                        raise ValueError("La consulta no devolvió ningún ID del equipo.")
                    new_team_id = row[0]

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


def _current_participante(user):
    # With FK we may have multiple; take the first. If you enforced UNIQUE(user), this is exactly one.
    return Participantes.objects.filter(user_id=user.id).order_by("id_participante").first()


# Historia : unirse a equipo
@login_required
def unirse_equipo(request, id: int):
    torneo = get_object_or_404(Torneos.objects.select_related("disciplinas_id_disciplina"), pk=id)
    if not torneo.aforo_equipos:
        messages.error(request, "Este torneo es individual; no permite equipos.")
        return redirect("tournaments:detail", id)

    #  teams that belong to this tournament
    teams = list(
        Equipos.objects
        .filter(torneosequipos__torneos_id_torneo=id)
        .values("id_equipo", "nombre", "capacidad_max", "disciplinas_id_disciplina")
        .order_by("nombre")
    )

    #resolve current participante from logged-in user
    participante = _current_participante(request.user)
    if not participante:
        messages.error(request, "Tu usuario no está vinculado a un participante.")
        return redirect("tournaments:detail", id)

    if request.method == "GET":
        return render(
            request,
            "join_team.html",
            {
                "tournament": {
                    "id": torneo.id_torneo,
                    "nombre": torneo.nombre,
                    "disciplina": getattr(torneo.disciplinas_id_disciplina, "nombre", "") or "",
                },
                "teams": teams,
            },
        )

    # POST
    team_id_raw = (request.POST.get("team_id") or "").strip()
    if not team_id_raw.isdigit():
        messages.error(request, "Selecciona un equipo válido.")
        return redirect("tournaments:join_team", id)
    team_id = int(team_id_raw)

    # 4) Validate the team belongs to the tournament
    if not TorneosEquipos.objects.filter(
        torneos_id_torneo_id=id, equipos_id_equipo_id=team_id
    ).exists():
        messages.error(request, "El equipo seleccionado no pertenece a este torneo.")
        return redirect("tournaments:join_team", id)

    # Optional checks: capacity & discipline
    team = get_object_or_404(Equipos, pk=team_id)

    if team.capacidad_max:
        miembros = EquiposParticipantes.objects.filter(
            equipos_id_equipo_id=team_id
        ).count()
        if miembros >= int(team.capacidad_max):
            messages.error(request, "Este equipo ya alcanzó su capacidad máxima.")
            return redirect("tournaments:join_team", id)

    # 5) Join (idempotent thanks to UNIQUE (equipo, participante))
    try:
        with transaction.atomic():
            _, created = EquiposParticipantes.objects.get_or_create(
                equipos_id_equipo_id=team_id,
                participantes_id_participante_id=int(participante.id_participante),
                defaults={"id_participante1": int(participante.id_participante)},  # legacy column
            )
        if created:
            messages.success(request, "Te uniste al equipo.", extra_tags="tournaments")
        else:
            messages.info(request, "Ya eres miembro de este equipo.", extra_tags="tournaments")
        return redirect("tournaments:detail", id)
    except IntegrityError as e:
        messages.error(request, "No se pudo crear el equipo.", extra_tags="tournaments")
        return redirect("tournaments:join_team", id)


# Historia : gestionar equipo 

@login_required
def gestionar_equipo(request, torneo_id: int, team_id: int):
    torneo = get_object_or_404(
        Torneos.objects.select_related("disciplinas_id_disciplina"), pk=torneo_id
    )
    team = get_object_or_404(
        Equipos.objects.select_related("disciplinas_id_disciplina", "participantes_id_participante"),
        pk=team_id
    )

    # The team must belong to the tournament
    if not TorneosEquipos.objects.filter(
        torneos_id_torneo_id=torneo_id, equipos_id_equipo_id=team_id
    ).exists():
        raise Http404("El equipo no pertenece a este torneo.")

    participante = _current_participante(request.user)
    if not participante:
        messages.error(request, "Tu usuario no está vinculado a un participante.", extra_tags="tournaments")
        return redirect("tournaments:detail", torneo_id)

 
    is_member = EquiposParticipantes.objects.filter(
        equipos_id_equipo_id=team_id,
        participantes_id_participante_id=participante.id_participante
    ).exists()
    if not is_member:
        messages.error(request, "No perteneces a este equipo.", extra_tags="tournaments")
        return redirect("tournaments:detail", torneo_id)

    # leader (responsable) is the team.participantes_id_participante
    leader_id = getattr(getattr(team, "participantes_id_participante", None), "id_participante", None)
    i_am_leader = (leader_id and int(leader_id) == int(participante.id_participante))

    # Members list
    miembros = list(
        EquiposParticipantes.objects
        .filter(equipos_id_equipo_id=team_id)
        .select_related("participantes_id_participante")
        .values(
            "id",
            "participantes_id_participante",
            "participantes_id_participante__nombre",
            "participantes_id_participante__apellido",
        )
        .order_by("participantes_id_participante__nombre")
    )
    for m in miembros:
        m["is_leader"] = (leader_id and int(m["participantes_id_participante"]) == int(leader_id))
        m["is_me"] = (int(m["participantes_id_participante"]) == int(participante.id_participante))

    # Actions
    if request.method == "POST":
        remove_id_raw = (request.POST.get("remove_id") or "").strip()
        if not remove_id_raw.isdigit():
            messages.error(request, "ID inválido.", extra_tags="tournaments")
            return redirect("tournaments:manage_team", torneo_id=torneo_id, team_id=team_id)

        remove_id = int(remove_id_raw)

        # rules:
        # - nobody can delete the leader (use another flow to transfer leadership)
        if leader_id and remove_id == int(leader_id):
            messages.error(request, "No puedes quitar al líder del equipo.", extra_tags="tournaments")
            return redirect("tournaments:manage_team", torneo_id=torneo_id, team_id=team_id)

        # - only the leader can remove others; anyone can remove themselves (“Salir del equipo”)
        removing_self = (remove_id == int(participante.id_participante))
        if not removing_self and not i_am_leader:
            messages.error(request, "Solo el líder puede quitar a otros integrantes.", extra_tags="tournaments")
            return redirect("tournaments:manage_team", torneo_id=torneo_id, team_id=team_id)

        with transaction.atomic():
            EquiposParticipantes.objects.filter(
                equipos_id_equipo_id=team_id,
                participantes_id_participante_id=remove_id
            ).delete()

        messages.success(
            request,
            "Saliste del equipo." if removing_self else "Miembro eliminado.",
            extra_tags="tournaments",
        )
        return redirect("tournaments:detail", torneo_id) if removing_self else redirect(
            "tournaments:manage_team", torneo_id=torneo_id, team_id=team_id
        )

    integrantes_count = len(miembros)
    integrantes_max = int(team.capacidad_max) if team.capacidad_max else None

    ctx = {
        "torneo": {
            "id": torneo.id_torneo,
            "nombre": torneo.nombre,
            "disciplina": getattr(torneo.disciplinas_id_disciplina, "nombre", "") or "",
        },
        "team": {
            "id": team.id_equipo,
            "nombre": team.nombre,
            "integrantes_count": integrantes_count,
            "integrantes_max": integrantes_max,
            "invite_link": f"bienestar.edu/join/{team.id_equipo}",
        },
        "miembros": miembros,
        "i_am_leader": i_am_leader,
    }
    return render(request, "manage_team.html", ctx)

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