#!/bin/bash
#Ejecutar en bash

#activar entorno: source venv/Scripts/activate
#Dar permisos :  chmod +x unit_test.sh
#ejecutar:  ./unit_test.sh

DESTRUCTIVE=false

coverage erase
while (( "$#" )); do
  case "$1" in
    --destructive)
      DESTRUCTIVE=true
      shift
      ;;
    *) # opción desconocida
      echo "Error: Invalid option"
      exit 1
      ;;
  esac
done

# Si hubiera tests destructivos
if [ "$DESTRUCTIVE" = true ]; then
    echo "Ejecutando pruebas destructivas..."
    # coverage run -a manage.py test alguna_app.tests.test_dangerous --timing
fi

echo "Ejecutando pruebas unitarias..."

# Analytics Reports
coverage run -a manage.py test Analytics_Reports.test.test_analytics_reports --timing --keepdb

# Management CADI
coverage run -a manage.py test management_CADI.tests.test_views_management_cadi --timing --keepdb

# Notificaciones
coverage run -a manage.py test notificaciones.test.test_notificaciones --timing --keepdb

# Search Activities
coverage run -a manage.py test searchActivities.tests.test_views_searchActivities --timing --keepdb

# Social Projects
coverage run -a manage.py test social_projects.tests.test_views_psu --timing --keepdb

# Universitary Wellbeing
coverage run -a manage.py test universitaryWellbeing.tests.test_views --timing --keepdb
coverage run -a manage.py test universitaryWellbeing.tests.test_calendario_horario --timing --keepdb


echo " Generando reporte de cobertura..."
coverage report
coverage html

echo " Resultados generados en: htmlcov/index.html"
