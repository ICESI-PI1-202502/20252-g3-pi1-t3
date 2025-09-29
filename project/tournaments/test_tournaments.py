# tournaments/test_tournaments.py
import pytest
from django.urls import reverse
from django.db import connection
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, date

# ---------- tiny SQL helpers ----------
def exec_sql(sql, params=None):
    with connection.cursor() as cur:
        cur.execute(sql, params or [])

def fetchone(sql, params=None):
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        return cur.fetchone()

# ---------- bootstrap a minimal schema (test DB only) ----------
BOOTSTRAP_SQL = """
-- roles
CREATE TABLE IF NOT EXISTS roles (
  id_rol BIGINT PRIMARY KEY,
  nombre_rol VARCHAR(50) NOT NULL
);

-- disciplinas
CREATE TABLE IF NOT EXISTS disciplinas (
  id_disciplina BIGINT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL
);

-- estados_torneo
CREATE TABLE IF NOT EXISTS estados_torneo (
  id_estado_torneo BIGINT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL
);

-- participantes (FK -> auth_user(id), roles)
CREATE TABLE IF NOT EXISTS participantes (
  id_participante BIGSERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  apellido VARCHAR(100) NOT NULL,
  correo VARCHAR(150) UNIQUE NOT NULL,
  semestre BIGINT NULL,
  estado_activo CHAR(1) NULL,
  roles_id_rol BIGINT NOT NULL REFERENCES roles(id_rol),
  facultad VARCHAR(80) NULL,
  programa VARCHAR(120) NULL,
  genero VARCHAR(20) NULL,
  "user" INTEGER NOT NULL REFERENCES auth_user(id)
);

-- torneos
CREATE TABLE IF NOT EXISTS torneos (
  id_torneo BIGSERIAL PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  disciplinas_id_disciplina BIGINT NOT NULL REFERENCES disciplinas(id_disciplina),
  fecha_inicio TIMESTAMP NOT NULL,
  fecha_fin TIMESTAMP NOT NULL,
  estados_torneo_id_estado_torneo BIGINT NOT NULL REFERENCES estados_torneo(id_estado_torneo),
  reglas_elegibilidad TEXT NULL,
  aforo_equipos BIGINT NULL
);

-- equipos
CREATE TABLE IF NOT EXISTS equipos (
  id_equipo BIGSERIAL PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  fecha_creacion DATE NOT NULL,
  cantidad_personas BIGINT NULL,
  participantes_id_participante BIGINT NOT NULL REFERENCES participantes(id_participante),
  disciplinas_id_disciplina BIGINT NULL REFERENCES disciplinas(id_disciplina),
  capacidad_min BIGINT NULL,
  capacidad_max BIGINT NULL
);

-- puente torneo <-> equipo
CREATE TABLE IF NOT EXISTS torneos_equipos (
  id BIGSERIAL PRIMARY KEY,
  torneos_id_torneo BIGINT NOT NULL REFERENCES torneos(id_torneo) ON DELETE CASCADE,
  equipos_id_equipo BIGINT NOT NULL REFERENCES equipos(id_equipo) ON DELETE CASCADE,
  UNIQUE (torneos_id_torneo, equipos_id_equipo)
);

-- puente equipo <-> participante
CREATE TABLE IF NOT EXISTS equipos_participantes (
  id BIGSERIAL PRIMARY KEY,
  equipos_id_equipo BIGINT NOT NULL REFERENCES equipos(id_equipo) ON DELETE CASCADE,
  participantes_id_participante BIGINT NOT NULL REFERENCES participantes(id_participante) ON DELETE CASCADE,
  id_participante1 BIGINT NULL,
  UNIQUE (equipos_id_equipo, participantes_id_participante)
);
"""

@pytest.fixture(autouse=True, scope="session")
def bootstrap_schema(django_db_setup, django_db_blocker):
    # Create the minimal tables once for the test session.
    with django_db_blocker.unblock():
        for stmt in BOOTSTRAP_SQL.strip().split(";\n"):
            if stmt.strip():
                exec_sql(stmt)

# ---------- base fixtures (per test) ----------
@pytest.fixture
def role_id():
    rid = 9001
    exec_sql("INSERT INTO roles(id_rol, nombre_rol) VALUES (%s, %s) ON CONFLICT (id_rol) DO NOTHING", [rid, "Estudiante"])
    return rid

@pytest.fixture
def disc_id():
    did = 9101
    exec_sql("INSERT INTO disciplinas(id_disciplina, nombre) VALUES (%s, %s) ON CONFLICT (id_disciplina) DO NOTHING",
             [did, "Valorant"])
    return did

@pytest.fixture
def state_open_id():
    sid = 1  # your crear_torneo view hardcodes id=1
    exec_sql("INSERT INTO estados_torneo(id_estado_torneo, nombre) VALUES (%s, %s) ON CONFLICT (id_estado_torneo) DO NOTHING",
             [sid, "Abierto"])
    return sid

@pytest.fixture
def user_and_participante(role_id):
    User = get_user_model()
    user = User.objects.create_user(username="puser", email="puser@example.com", password="testpass123")
    # participante linked to auth_user.id via column "user"
    exec_sql("""
        INSERT INTO participantes(nombre, apellido, correo, semestre, estado_activo,
                                  roles_id_rol, facultad, programa, genero, "user")
        VALUES ('Test', 'User', 'puser@example.com', NULL, 'S', %s, 'Ing', 'Sistemas', 'Masculino', %s)
        RETURNING id_participante
    """, [role_id, user.id])
    pid = fetchone("SELECT id_participante FROM participantes WHERE correo=%s", ["puser@example.com"])[0]
    return user, pid

@pytest.fixture
def torneo_equipo(disc_id, state_open_id):
    # team-based tournament (aforo_equipos not null)
    fi = datetime.now()
    ff = fi + timedelta(days=7)
    exec_sql("""
        INSERT INTO torneos(nombre, disciplinas_id_disciplina, fecha_inicio, fecha_fin,
                            estados_torneo_id_estado_torneo, reglas_elegibilidad, aforo_equipos)
        VALUES (%s, %s, %s, %s, %s, NULL, %s)
        RETURNING id_torneo
    """, ["Torneo por equipos", disc_id, fi, ff, state_open_id, 8])
    tid = fetchone("SELECT id_torneo FROM torneos WHERE nombre=%s ORDER BY id_torneo DESC LIMIT 1",
                   ["Torneo por equipos"])[0]
    return tid

# ---------- TESTS ----------
@pytest.mark.django_db(transaction=True)
def test_crear_torneo_ok(client, disc_id, state_open_id):
    """
    POST /tournaments/create/ crea un torneo (por equipos si aforo > 0).
    """
    url = reverse("tournaments:create")
    payload = {
        "nombre": "Copa Campus",
        "disciplina": str(disc_id),
        "fecha_inicio": (datetime.now()).strftime("%Y-%m-%d"),
        "fecha_fin": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "aforo": "6",
    }
    resp = client.post(url, data=payload, follow=True)
    assert resp.status_code == 200

    row = fetchone("SELECT count(*) FROM torneos WHERE nombre=%s", ["Copa Campus"])
    assert row and row[0] >= 1

@pytest.mark.django_db(transaction=True)
def test_crear_equipo_en_torneo_ok(client, torneo_equipo, disc_id, user_and_participante):
    """
    POST /tournaments/<id>/teams/create/ crea:
    - equipos
    - torneos_equipos
    - equipos_participantes (líder)
    """
    _, leader_pid = user_and_participante
    url = reverse("tournaments:create_team", args=[torneo_equipo])
    payload = {
        "nombre_equipo": "Los Pros",
        "responsable_id": str(leader_pid),
        "disciplina_id": str(disc_id),
        "capacidad_min": "1",
        "capacidad_max": "4",
        "fecha_creacion": date.today().strftime("%Y-%m-%d"),
    }
    resp = client.post(url, data=payload, follow=True)
    assert resp.status_code == 200

    # equipo creado
    eq = fetchone("SELECT id_equipo FROM equipos WHERE nombre=%s ORDER BY id_equipo DESC LIMIT 1", ["Los Pros"])
    assert eq is not None
    team_id = eq[0]

    # link torneo<->equipo
    c = fetchone("SELECT count(*) FROM torneos_equipos WHERE torneos_id_torneo=%s AND equipos_id_equipo=%s",
                 [torneo_equipo, team_id])[0]
    assert c == 1

    # líder agregado
    c2 = fetchone("SELECT count(*) FROM equipos_participantes WHERE equipos_id_equipo=%s AND participantes_id_participante=%s",
                  [team_id, leader_pid])[0]
    assert c2 == 1

@pytest.mark.django_db(transaction=True)
def test_unirse_equipo_ok(client, torneo_equipo, disc_id, user_and_participante, role_id):
    """
    POST /tournaments/<id>/teams/join/ agrega al participante logueado al equipo.
    """
    user, pid = user_and_participante

    # crear equipo con otro líder
    # 1) crear líder alterno
    User = get_user_model()
    alt_user = User.objects.create_user(username="leader_alt", email="leader@example.com", password="x")
    exec_sql("""
        INSERT INTO participantes(nombre, apellido, correo, semestre, estado_activo,
                                  roles_id_rol, facultad, programa, genero, "user")
        VALUES ('Lid', 'Alt', 'leader@example.com', NULL, 'S', %s, 'Ing', 'Sistemas', 'M', %s)
        RETURNING id_participante
    """, [role_id, alt_user.id])
    alt_pid = fetchone("SELECT id_participante FROM participantes WHERE correo=%s", ["leader@example.com"])[0]

    # 2) crear equipo y vincular a torneo
    exec_sql("""
        INSERT INTO equipos(nombre, fecha_creacion, cantidad_personas, participantes_id_participante,
                            disciplinas_id_disciplina, capacidad_min, capacidad_max)
        VALUES ('Equipo X', CURRENT_DATE, NULL, %s, %s, 1, 5)
        RETURNING id_equipo
    """, [alt_pid, disc_id])
    team_id = fetchone("SELECT id_equipo FROM equipos WHERE nombre=%s ORDER BY id_equipo DESC LIMIT 1", ["Equipo X"])[0]
    exec_sql("INSERT INTO torneos_equipos(torneos_id_torneo, equipos_id_equipo) VALUES (%s, %s) ON CONFLICT DO NOTHING",
             [torneo_equipo, team_id])

    # login y unirse
    client.force_login(user)
    url = reverse("tournaments:join_team", args=[torneo_equipo])
    resp = client.post(url, data={"team_id": str(team_id)}, follow=True)
    assert resp.status_code == 200

    c = fetchone("""
        SELECT count(*) FROM equipos_participantes
        WHERE equipos_id_equipo=%s AND participantes_id_participante=%s
    """, [team_id, pid])[0]
    assert c == 1

@pytest.mark.django_db(transaction=True)
def test_gestionar_equipo_removerse(client, torneo_equipo, disc_id, user_and_participante, role_id):
    """
    POST /tournaments/<tid>/teams/<eid>/manage/ con remove_id = yo mismo
    (cuando NO soy líder) elimina mi membresía.
    """
    user, me_pid = user_and_participante

    # crear líder real (otro participante)
    User = get_user_model()
    leader_user = User.objects.create_user(username="real_leader", email="rl@example.com", password="x")
    exec_sql("""
        INSERT INTO participantes(nombre, apellido, correo, semestre, estado_activo,
                                  roles_id_rol, facultad, programa, genero, "user")
        VALUES ('Real', 'Leader', 'rl@example.com', NULL, 'S', %s, 'Ing', 'Sistemas', 'M', %s)
        RETURNING id_participante
    """, [role_id, leader_user.id])
    leader_pid = fetchone("SELECT id_participante FROM participantes WHERE correo=%s", ["rl@example.com"])[0]

    # equipo con ese líder y link al torneo
    exec_sql("""
        INSERT INTO equipos(nombre, fecha_creacion, cantidad_personas, participantes_id_participante,
                            disciplinas_id_disciplina, capacidad_min, capacidad_max)
        VALUES ('Mi Equipo', CURRENT_DATE, NULL, %s, %s, 1, 5)
        RETURNING id_equipo
    """, [leader_pid, disc_id])
    team_id = fetchone("SELECT id_equipo FROM equipos WHERE nombre=%s ORDER BY id_equipo DESC LIMIT 1", ["Mi Equipo"])[0]
    exec_sql("INSERT INTO torneos_equipos(torneos_id_torneo, equipos_id_equipo) VALUES (%s, %s) ON CONFLICT DO NOTHING",
             [torneo_equipo, team_id])

    # agregarme como miembro normal
    exec_sql("""
        INSERT INTO equipos_participantes(equipos_id_equipo, participantes_id_participante, id_participante1)
        VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
    """, [team_id, me_pid, me_pid])

    # login y auto-removerse
    client.force_login(user)
    url = reverse("tournaments:manage_team", args=[torneo_equipo, team_id])
    resp = client.post(url, data={"remove_id": str(me_pid)}, follow=True)
    assert resp.status_code == 200

    c = fetchone("""
        SELECT count(*) FROM equipos_participantes
        WHERE equipos_id_equipo=%s AND participantes_id_participante=%s
    """, [team_id, me_pid])[0]
    assert c == 0
