from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import datetime, timedelta
import pytz

from universitaryWellbeing.models import (
    HorariosParticipante, 
    Participantes, 
    Actividades,
    Roles
)
from universitaryWellbeing.views import obtener_eventos_del_dia


class CalendarioHorarioTestCase(TestCase):
    """Tests para el sistema de calendario y horario"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Usar rol existente o None
        self.rol = Roles.objects.first()
        
        # Crear usuario único
        import random
        cedula = f"test{random.randint(1000000, 9999999)}"
        
        self.user = User.objects.create_user(
            username=cedula,
            password='testpass123',
            email=f'{cedula}@example.com',
            first_name='Test',
            last_name='User'
        )
        
        # Crear participante
        self.participante = Participantes.objects.create(
            user=self.user,
            id_participante=cedula,
            nombre='Test',
            apellido='User',
            correo=f'{cedula}@example.com',
            estado_activo='S',
            roles_id_rol=self.rol
        )
        
        # Usar actividad existente si hay, sino None
        self.actividad = Actividades.objects.first()
        
        # Configurar zona horaria
        self.tz = pytz.timezone('America/Bogota')
        self.ahora = timezone.now().astimezone(self.tz)
        self.hoy = self.ahora.date()
    
    def tearDown(self):
        """Limpieza después de cada test"""
        HorariosParticipante.objects.filter(
            participantes_id_participante=self.participante
        ).delete()
        self.participante.delete()
        self.user.delete()
    
    def test_evento_unico_hoy(self):
        """Verifica que se detecte un evento único para hoy"""
        HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Evento Hoy",
            fecha_inicio=self.ahora.replace(hour=14, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=15, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        eventos = obtener_eventos_del_dia(self.participante, self.hoy)
        
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]['titulo'], "[TEST] Evento Hoy")
        self.assertEqual(eventos[0]['tipo'], 'único')
    
    def test_evento_unico_manana_no_aparece_hoy(self):
        """Verifica que eventos de mañana NO aparezcan hoy"""
        manana = self.ahora + timedelta(days=1)
        
        HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Evento Mañana",
            fecha_inicio=manana.replace(hour=10, minute=0, second=0, microsecond=0),
            fecha_fin=manana.replace(hour=11, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        eventos = obtener_eventos_del_dia(self.participante, self.hoy)
        self.assertEqual(len(eventos), 0)
    
    def test_evento_recurrente_mismo_dia_semana(self):
        """Verifica que eventos recurrentes aparezcan en el día correcto"""
        if not self.actividad:
            self.skipTest("No hay actividad disponible")
        
        HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            actividades_id_actividad=self.actividad,
            titulo=f"[TEST] Recurrente {self.hoy.strftime('%A')}",
            fecha_inicio=self.ahora.replace(hour=16, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=17, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        eventos = obtener_eventos_del_dia(self.participante, self.hoy)
        
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]['tipo'], 'recurrente')
    
    def test_multiples_eventos_ordenados_por_hora(self):
        """Verifica que múltiples eventos se ordenen por hora"""
        HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Tarde",
            fecha_inicio=self.ahora.replace(hour=16, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=17, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Mañana",
            fecha_inicio=self.ahora.replace(hour=9, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=10, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        eventos = obtener_eventos_del_dia(self.participante, self.hoy)
        
        self.assertEqual(len(eventos), 2)
        self.assertEqual(eventos[0]['fecha_inicio'].hour, 9)
        self.assertEqual(eventos[1]['fecha_inicio'].hour, 16)
    
    def test_sin_eventos(self):
        """Verifica que retorne lista vacía cuando no hay eventos"""
        eventos = obtener_eventos_del_dia(self.participante, self.hoy)
        
        self.assertEqual(len(eventos), 0)
        self.assertIsInstance(eventos, list)
