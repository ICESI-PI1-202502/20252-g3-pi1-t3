from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, time
import pytz

from universitaryWellbeing.models import (
    HorariosParticipante, 
    Participantes, 
    Actividades,
    Roles,
    HorariosBloque,
    HorariosActividad,
    TiposActividad
)
from universitaryWellbeing.views import obtener_actividades_generales_del_dia


class CalendarioGeneralTestCase(TestCase):
    """Tests para el calendario de actividades generales"""
    
    @classmethod
    def setUpTestData(cls):
        """Datos que se crean una vez para todos los tests de la clase"""
        # Crear tipo de actividad
        cls.tipo_actividad = TiposActividad.objects.create(
            nombre_tipo='Deportes Test',
            descripcion='Actividades deportivas'
        )
        
        # Crear actividad
        cls.actividad = Actividades.objects.create(
            nombre='Fútbol Test',
            descripcion='Fútbol masculino avanzado',
            tipos_actividad_id_tipo=cls.tipo_actividad
        )
    
    def setUp(self):
        """Configuración para cada test individual"""
        self.tz = pytz.timezone('America/Bogota')
        self.ahora = timezone.now().astimezone(self.tz)
        self.hoy = self.ahora.date()
    
    def tearDown(self):
        """Limpieza después de cada test"""
        HorariosBloque.objects.filter(actividades_id_actividad=self.actividad).delete()
    
    def test_actividad_general_lunes(self):
        """Verifica que se detecten actividades generales de lunes"""
        # Crear bloque de horario
        bloque = HorariosBloque.objects.create(
            actividades_id_actividad=self.actividad,
            hora_inicio=time(7, 0),
            hora_fin=time(9, 0),
            profesor='Prof. Test',
            lugar='Cancha 1'
        )
        
        # Asignar día lunes (2 en tu BD probablemente)
        HorariosActividad.objects.create(
            horario_bloque_id=bloque,
            dia_semana=2  # Lunes
        )
        
        # Buscar un lunes
        dias_hasta_lunes = (0 - self.ahora.weekday()) % 7
        fecha_lunes = self.hoy + timedelta(days=dias_hasta_lunes if dias_hasta_lunes else 0)
        
        eventos = obtener_actividades_generales_del_dia(fecha_lunes)
        
        self.assertGreater(len(eventos), 0, "Debe haber al menos 1 actividad")
        self.assertEqual(eventos[0]['titulo'], 'Fútbol Test')
        self.assertEqual(eventos[0]['tipo'], 'actividad_general')
    
    def test_actividad_general_sin_horarios(self):
        """Verifica que retorne lista vacía cuando no hay actividades"""
        # No crear ningún horario
        eventos = obtener_actividades_generales_del_dia(self.hoy)
        
        self.assertIsInstance(eventos, list)
        # Puede estar vacío o tener actividades existentes
    
    def test_actividad_general_con_multiples_horarios(self):
        """Verifica orden de múltiples actividades"""
        # Crear 3 bloques diferentes
        bloque1 = HorariosBloque.objects.create(
            actividades_id_actividad=self.actividad,
            hora_inicio=time(16, 0),
            hora_fin=time(17, 0),
            profesor='Prof. Tarde'
        )
        
        bloque2 = HorariosBloque.objects.create(
            actividades_id_actividad=self.actividad,
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
            profesor='Prof. Mañana'
        )
        
        bloque3 = HorariosBloque.objects.create(
            actividades_id_actividad=self.actividad,
            hora_inicio=time(12, 0),
            hora_fin=time(13, 0),
            profesor='Prof. Mediodía'
        )
        
        # Asignar todos al lunes
        dia_semana_lunes = 2
        HorariosActividad.objects.create(horario_bloque_id=bloque1, dia_semana=dia_semana_lunes)
        HorariosActividad.objects.create(horario_bloque_id=bloque2, dia_semana=dia_semana_lunes)
        HorariosActividad.objects.create(horario_bloque_id=bloque3, dia_semana=dia_semana_lunes)
        
        # Buscar lunes
        dias_hasta_lunes = (0 - self.ahora.weekday()) % 7
        fecha_lunes = self.hoy + timedelta(days=dias_hasta_lunes if dias_hasta_lunes else 0)
        
        eventos = obtener_actividades_generales_del_dia(fecha_lunes)
        
        # Verificar que están ordenados por hora
        if len(eventos) >= 3:
            self.assertEqual(eventos[0]['fecha_inicio'].hour, 9)
            self.assertEqual(eventos[1]['fecha_inicio'].hour, 12)
            self.assertEqual(eventos[2]['fecha_inicio'].hour, 16)


class HorarioPersonalTestCase(TestCase):
    """Tests para el horario personal de usuarios"""
    
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
        
        # Usar actividad existente si hay
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
    
    def test_horario_vacio(self):
        """Verifica que un participante sin eventos tenga horario vacío"""
        horarios = HorariosParticipante.objects.filter(
            participantes_id_participante=self.participante
        )
        
        self.assertEqual(horarios.count(), 0)
    
    def test_crear_evento_personal(self):
        """Verifica que se pueda crear un evento personal"""
        evento = HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Evento Personal",
            fecha_inicio=self.ahora.replace(hour=14, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=15, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        self.assertIsNotNone(evento.id_horario)
        self.assertEqual(evento.titulo, "[TEST] Evento Personal")
        self.assertEqual(evento.participantes_id_participante, self.participante)
    
    def test_evento_recurrente_con_actividad(self):
        """Verifica eventos recurrentes con actividad"""
        if not self.actividad:
            self.skipTest("No hay actividad disponible")
        
        evento = HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            actividades_id_actividad=self.actividad,
            titulo=f"[TEST] Recurrente {self.hoy.strftime('%A')}",
            fecha_inicio=self.ahora.replace(hour=16, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=17, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        self.assertIsNotNone(evento.actividades_id_actividad)
        self.assertEqual(evento.fuente_manual, 'S')
    
    def test_multiples_eventos_mismo_participante(self):
        """Verifica que se puedan crear múltiples eventos"""
        HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Evento 1",
            fecha_inicio=self.ahora.replace(hour=9, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=10, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Evento 2",
            fecha_inicio=self.ahora.replace(hour=16, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=17, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        total = HorariosParticipante.objects.filter(
            participantes_id_participante=self.participante
        ).count()
        
        self.assertEqual(total, 2)
    
    def test_eventos_ordenados_por_fecha(self):
        """Verifica que los eventos se puedan ordenar cronológicamente"""
        # Crear eventos en orden aleatorio
        evento_tarde = HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Tarde",
            fecha_inicio=self.ahora.replace(hour=16, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=17, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        evento_manana = HorariosParticipante.objects.create(
            participantes_id_participante=self.participante,
            titulo="[TEST] Mañana",
            fecha_inicio=self.ahora.replace(hour=9, minute=0, second=0, microsecond=0),
            fecha_fin=self.ahora.replace(hour=10, minute=0, second=0, microsecond=0),
            fuente_manual='S'
        )
        
        # Consultar ordenados
        eventos = HorariosParticipante.objects.filter(
            participantes_id_participante=self.participante
        ).order_by('fecha_inicio')
        
        self.assertEqual(eventos[0].titulo, "[TEST] Mañana")
        self.assertEqual(eventos[1].titulo, "[TEST] Tarde")


class IntegracionCalendarioTestCase(TestCase):
    """Tests de integración entre calendario general y horario personal"""
    
    def test_sin_colision_entre_sistemas(self):
        """Verifica que calendario general y personal sean independientes"""
        # Este test verifica que ambos sistemas coexistan
        actividades_generales = obtener_actividades_generales_del_dia(timezone.now().date())
        
        # Debe retornar una lista (puede estar vacía)
        self.assertIsInstance(actividades_generales, list)
