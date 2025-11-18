#!/bin/bash
# chmod +x unit_test.sh

PGUSER="postgres.xlknciyujekwbhysmamn"
PGPASSWORD="h9TZan8icTf3hjsn"
PGHOST="aws-1-us-east-2.pooler.supabase.com"
PGDATABASE="postgres"

export PGPASSWORD

# Función para eliminar test_postgres usando Python
drop_test_db() {
    echo "🗑️ Terminando conexiones y eliminando test_postgres..."
    python - <<EOF
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="$PGHOST",
        user="$PGUSER",
        password="$PGPASSWORD",
        database="$PGDATABASE",
        sslmode="require"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Terminar conexiones activas
    cursor.execute("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = 'test_postgres' AND pid <> pg_backend_pid();
    """)
    
    # Eliminar la base de datos
    cursor.execute("DROP DATABASE IF EXISTS test_postgres WITH (FORCE);")
    
    cursor.close()
    conn.close()
    print("✅ Base test_postgres eliminada exitosamente")
except Exception as e:
    print(f"⚠️ Error al eliminar test_postgres: {e}")
    sys.exit(0)  # No fallar el script completo
EOF
}

# Ejecutar tests con keepdb
run_test_keepdb() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 Ejecutando (keepdb): $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    coverage run -a manage.py test "$1" --timing --keepdb
}

# Ejecutar tests con fresh DB
run_test_fresh() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🧨 Ejecutando (fresh DB): $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    drop_test_db  # <--- ELIMINA test_postgres ANTES
    coverage run -a manage.py test "$1" --timing --keepdb
}

coverage erase

echo "🧪 Ejecutando suites..."

# Suites sin problemas
run_test_keepdb "Analytics_Reports.tests"
run_test_keepdb "notificaciones.test.test_notificaciones"
run_test_keepdb "social_projects.tests.test_views_psu"
run_test_keepdb "universitaryWellbeing.tests.test_views"
run_test_keepdb "universitaryWellbeing.tests.test_calendario_horario"
run_test_keepdb "searchActivities.tests"
run_test_keepdb "tournaments.tests"

# Suites que necesitan BD limpia
run_test_fresh "appointments.tests"
run_test_fresh "management_CADI.tests"

echo "📊 Generando cobertura..."
coverage report
coverage html

echo "✅ COMPLETADO"
echo "📄 Reporte en htmlcov/index.html"