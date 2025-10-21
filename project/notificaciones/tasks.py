# notificaciones/tasks.py
from celery import shared_task
from datetime import datetime

@shared_task
def generar_notificaciones_horarios_task():
    from universitaryWellbeing.models import HorarioParticipante
    from django.utils import timezone

    ahora = timezone.now()
    proximos = HorarioParticipante.objects.filter(fecha_inicio__gte=ahora)

    print(f"[{ahora}] Revisando {proximos.count()} horarios próximos")
    for h in proximos:
        print(f"→ Notificación: {h.titulo} para participante {h.participante.id_participante}")
