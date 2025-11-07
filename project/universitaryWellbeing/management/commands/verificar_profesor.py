# universitaryWellbeing/management/commands/verificar_profesor.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from universitaryWellbeing.models import Participantes

class Command(BaseCommand):
    help = 'Verifica el rol del usuario 333 (nuevo@gmail.com)'

    def handle(self, *args, **options):
        try:
            # Buscar por ID de participante
            participante = Participantes.objects.get(id_participante=333)
            
            self.stdout.write(f'\n📊 Participante ID: {participante.id_participante}')
            self.stdout.write(f'   Nombre: {participante.nombre} {participante.apellido}')
            self.stdout.write(f'   Email: {participante.correo}')
            
            # Verificar usuario asociado
            if participante.user:
                user = participante.user
                self.stdout.write(f'\n👤 Usuario Django:')
                self.stdout.write(f'   Username: {user.username}')
                self.stdout.write(f'   ID: {user.id}')
                self.stdout.write(f'   Superuser: {user.is_superuser}')
            else:
                self.stdout.write(self.style.ERROR('\n✗ No tiene usuario de Django asociado'))
                return
            
            # Verificar rol
            if participante.roles_id_rol:
                rol = participante.roles_id_rol
                self.stdout.write(f'\n🎭 Rol:')
                self.stdout.write(f'   ID: {rol.id_rol}')
                self.stdout.write(f'   Nombre: "{rol.nombre_rol}"')
                self.stdout.write(f'   Nombre (lower): "{rol.nombre_rol.lower()}"')
                self.stdout.write(f'   Nombre (strip): "{rol.nombre_rol.strip()}"')
                
                # Verificar grupo asociado al rol
                if rol.grupo_d:
                    self.stdout.write(f'\n✓ Grupo Django asociado al rol:')
                    self.stdout.write(f'   Nombre: {rol.grupo_d.name}')
                    self.stdout.write(f'   ID: {rol.grupo_d.id}')
                else:
                    self.stdout.write(self.style.WARNING('\n⚠ El rol NO tiene grupo de Django asociado'))
            else:
                self.stdout.write(self.style.ERROR('\n✗ Sin rol asignado'))
                return
            
            # Verificar grupos del usuario
            grupos = user.groups.all()
            if grupos:
                self.stdout.write(f'\n✓ Grupos asignados al usuario:')
                for g in grupos:
                    self.stdout.write(f'   - {g.name} (ID: {g.id})')
            else:
                self.stdout.write(self.style.WARNING('\n⚠ El usuario NO tiene grupos asignados'))
            
            # Test del context processor
            self.stdout.write(f'\n🧪 Simulación del context processor:')
            rol_nombre = rol.nombre_rol.lower().strip()
            self.stdout.write(f'   rol_nombre procesado: "{rol_nombre}"')
            self.stdout.write(f'   es_profesor: {rol_nombre in ["profesor", "teacher"]}')
            
        except Participantes.DoesNotExist:
            self.stdout.write(self.style.ERROR('\n✗ Participante 333 no existe'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error: {e}'))