from django.db import models
from django.contrib.auth.models import Group

class TestRoles(models.Model):
    nombre_rol = models.CharField(max_length=100)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        db_table = 'roles'       # usa el mismo nombre de tabla
        managed = True 