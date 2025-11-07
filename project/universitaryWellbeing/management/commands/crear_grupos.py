# management/commands/crear_grupos.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Crea los grupos de roles con permisos especiales'

    def handle(self, *args, **kwargs):
        # Solo crear grupos para roles con permisos
        ROLES_ESPECIALES = {
            'Coordinador': ['view_actividad', 'add_actividad', 'change_actividad'],
            'Profesor': ['add_asistencia', 'change_asistencia', 'view_asistencia'],
            'Psicologo': ['view_cita', 'add_cita', 'change_cita'],
            'Admin_Bienestar': ['view_*', 'add_*', 'change_*'],  # Más permisos
            'Super_Admin': [],  # Será superuser
        }
        
        for rol, permisos_codenames in ROLES_ESPECIALES.items():
            group, created = Group.objects.get_or_create(name=rol)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Grupo "{rol}" creado'))
            else:
                self.stdout.write(self.style.WARNING(f'- Grupo "{rol}" ya existe'))
            
            # Asignar permisos (ajusta según tus modelos)
            # permisos = Permission.objects.filter(codename__in=permisos_codenames)
            # group.permissions.set(permisos)

        self.stdout.write(self.style.SUCCESS('\n✓ Grupos creados. Asígnalos desde el Admin.'))