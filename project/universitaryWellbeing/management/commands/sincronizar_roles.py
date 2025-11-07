# universitaryWellbeing/management/commands/sincronizar_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from universitaryWellbeing.models import Roles

class Command(BaseCommand):
    help = 'Sincroniza roles de BD con grupos de Django'

    def handle(self, *args, **options):
        ROLES_PERMISOS = {
            'coordinador': 'Coordinador',
            'profesor': 'Profesor',
            'psicologo': 'Psicólogo',
            'admin_bienestar': 'Admin Bienestar',
            'super_admin': 'Super Admin'
        }

        for rol_bd, nombre_grupo in ROLES_PERMISOS.items():
            # Buscar o crear el rol en BD
            rol, created = Roles.objects.get_or_create(
                nombre_rol=rol_bd,
                defaults={'nombre_rol': rol_bd}
            )
            
            # Buscar o crear el grupo
            grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
            
            # Conectarlos
            if not rol.grupo_d:
                rol.grupo_d = grupo
                rol.save()
                self.stdout.write(f'✓ {rol_bd} → {nombre_grupo}')
            else:
                self.stdout.write(f'- {rol_bd} ya estaba conectado')

        self.stdout.write(self.style.SUCCESS('\n✓ Sincronización completa'))