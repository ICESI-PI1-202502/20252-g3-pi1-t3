# universitaryWellbeing/management/commands/cambiar_rol_participante.py
from django.core.management.base import BaseCommand
from universitaryWellbeing.models import Participantes, Roles
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Cambia el rol de un participante y sincroniza con grupos de Django'

    def add_arguments(self, parser):
        parser.add_argument('id_participante', type=int, help='ID del participante')
        parser.add_argument('nuevo_rol', type=str, help='Nombre del nuevo rol')

    def handle(self, *args, **options):
        id_participante = options['id_participante']
        nuevo_rol_nombre = options['nuevo_rol']
        
        try:
            # Buscar participante
            participante = Participantes.objects.get(id_participante=id_participante)
            self.stdout.write(f'\n📊 Participante: {participante.nombre} {participante.apellido}')
            self.stdout.write(f'   Rol actual: {participante.roles_id_rol.nombre_rol if participante.roles_id_rol else "Sin rol"}')
            
            # Buscar el nuevo rol (case-insensitive)
            try:
                nuevo_rol = Roles.objects.get(nombre_rol__iexact=nuevo_rol_nombre)
            except Roles.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'\n✗ Rol "{nuevo_rol_nombre}" no existe'))
                self.stdout.write('\nRoles disponibles:')
                for rol in Roles.objects.all():
                    self.stdout.write(f'   - {rol.nombre_rol}')
                return
            
            # Actualizar el rol del participante
            participante.roles_id_rol = nuevo_rol
            participante.save()
            self.stdout.write(self.style.SUCCESS(f'\n✓ Rol actualizado a: {nuevo_rol.nombre_rol}'))
            
            # Sincronizar con grupos de Django
            user = participante.user
            if user:
                # Limpiar grupos anteriores relacionados con roles
                roles_grupos = ['Coordinador', 'Profesor', 'Psicólogo', 'Admin Bienestar', 'Super Admin']
                user.groups.filter(name__in=roles_grupos).delete()
                
                # Asignar el nuevo grupo si el rol lo tiene
                if nuevo_rol.grupo_d:
                    user.groups.add(nuevo_rol.grupo_d)
                    self.stdout.write(self.style.SUCCESS(f'✓ Grupo de Django agregado: {nuevo_rol.grupo_d.name}'))
                else:
                    self.stdout.write(self.style.WARNING('⚠ El rol no tiene grupo de Django asociado'))
                
                # Mostrar grupos actuales
                grupos = user.groups.all()
                if grupos:
                    self.stdout.write('\n📋 Grupos actuales del usuario:')
                    for g in grupos:
                        self.stdout.write(f'   - {g.name}')
            else:
                self.stdout.write(self.style.WARNING('\n⚠ El participante no tiene usuario de Django asociado'))
            
        except Participantes.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'\n✗ Participante {id_participante} no existe'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error: {e}'))