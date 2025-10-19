from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from datetime import timedelta
from ..models import Actividades, Participantes, Participaciones, Asistencias, EstadosAsistencia, HistorialParticipaciones, TiposActividad
from django.views.decorators.http import require_http_methods  # Añadido para corregir el error

class ViewsTestCase(TestCase):
    def setUp(self):
        # Configurar cliente de prueba
        self.client = Client()
        
        # Crear usuario administrador
        self.user = User.objects.create_user(username='admin', password='testpass123', is_staff=True)
        
        # Crear datos de prueba
        self.tipo_actividad = TiposActividad.objects.create(id_tipo=1.0, nombre_tipo="Deporte")
        self.actividad = Actividades.objects.create(
            id_actividad=1,
            nombre="Fútbol",
            tipos_actividad=self.tipo_actividad
        )
        self.participante = Participantes.objects.create(
            id_participante=1,
            nombre="Juan",
            apellido="Pérez",
            correo="juan@example.com",
            user=self.user
        )
        self.participacion = Participaciones.objects.create(
            id_participacion=1,
            fecha_inscripcion=timezone.now().date(),
            participantes=self.participante,
            actividades=self.actividad
        )
        self.estado_presente = EstadosAsistencia.objects.create(id_estado_asistencia=1, nombre="Presente")
        self.asistencia = Asistencias.objects.create(
            id_asistencia=1,
            fecha=timezone.now().date(),
            estados_asistencia=self.estado_presente,
            participaciones=self.participacion
        )
        self.historial = HistorialParticipaciones.objects.create(
            id_historial=1,
            participaciones=self.participacion,
            fecha=timezone.now().date(),
            nota="Nota de prueba"
        )

    def test_analisis_comportamiento_get(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('analisis_comportamiento'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analisis.html')
        self.assertIn('data', response.context)
        self.assertIn('tipos_actividad', response.context)

        response = self.client.get(reverse('analisis_comportamiento'), {'tipo_actividad': '1.0', 'min_frecuencia': '1'})
        self.assertEqual(response.status_code, 200)

    def test_comparaciones_get(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('comparaciones'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comparaciones.html')
        self.assertIn('resultados', response.context)
        self.assertIn('metricas', response.context)

        response = self.client.get(reverse('comparaciones'), {'tiempo': 'semestre', 'semestre_filtro': '1'})
        self.assertEqual(response.status_code, 200)

    def test_recomendaciones_get(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('recomendaciones'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recomendaciones.html')
        self.assertIn('estudiantes_activos', response.context)

        response = self.client.get(reverse('recomendaciones'), {'enviar_notificaciones': 'true'})
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.message == 'Notificaciones enviadas correctamente.' for msg in messages))

    def test_gestion_asistencia_get(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('gestion_asistencia'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_asistencia.html')
        self.assertIn('asistencias', response.context)
        self.assertIn('actividades', response.context)
        self.assertIn('estados_asistencia', response.context)
        self.assertIn('stats', response.context)

        response = self.client.get(reverse('gestion_asistencia'), {'fecha': (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')})
        self.assertEqual(response.status_code, 200)

    def test_historial_participante_get(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('historial_participante', kwargs={'participante_id': self.participante.id_participante}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'historial_participante.html')
        self.assertIn('participante', response.context)
        self.assertIn('historial_data', response.context)
        self.assertIn('notas_historial', response.context)

    def test_asistencia_get(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('asistencia'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'asistencia.html')
        self.assertIn('data', response.context)

    def test_registrar_asistencia_cedula_view_get(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('registrar_asistencia_cedula_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registrar_asistencia_cedula.html')
        self.assertIn('actividades', response.context)
        self.assertIn('estados_asistencia', response.context)
        self.assertIn('stats', response.context)

    @require_http_methods(["POST"])
    def test_registrar_asistencia_rapido_post(self):
        self.client.login(username='admin', password='testpass123')
        data = {
            'cedula': '12345',
            'estado_id': '1',
            'actividad_id': '1',
            'fecha': timezone.now().date().strftime('%Y-%m-%d')
        }
        response = self.client.post(reverse('registrar_asistencia_rapido'), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertIn('message', response.json())

        response = self.client.post(reverse('registrar_asistencia_rapido'), {'cedula': '12345'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_registrar_asistencia_manual_post(self):
        self.client.login(username='admin', password='testpass123')
        data = {
            'actividad_id': '1',
            'fecha': timezone.now().date().strftime('%Y-%m-%d'),
            'cedulas': '12345\n67890'
        }
        response = self.client.post(reverse('registrar_asistencia_manual'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registrar_asistencia.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level == messages.SUCCESS for msg in messages))

        response = self.client.post(reverse('registrar_asistencia_manual'), {'actividad_id': '', 'fecha': '', 'cedulas': ''})
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level == messages.ERROR for msg in messages))

    def test_unauthorized_access(self):
        response = self.client.get(reverse('analisis_comportamiento'))
        self.assertEqual(response.status_code, 302)  # Redirección a login
        self.client.login(username='user', password='testpass123')
        user = User.objects.create_user(username='user', password='testpass123')
        response = self.client.get(reverse('analisis_comportamiento'))
        self.assertEqual(response.status_code, 403)  # Prohibido para no staff