from django import forms
from django.forms import ModelForm
from .models import Equipos, Torneos, TorneosEquipos

class TeamCreateForm(ModelForm):
    class Meta:
        model = Equipos
        fields = [
            "nombre",
            "fecha_creacion",
            "cantidad_personas",
            "participantes_id_participante",   # antes: 'responsable'
            "disciplinas_id_disciplina",
            "capacidad_min",
            "capacidad_max",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre del equipo"}),
            "fecha_creacion": forms.DateInput(attrs={"type": "date"}),
        }

class InscripcionForm(forms.Form):
    correo = forms.EmailField(label="Correo del participante")

    torneo = forms.ModelChoiceField(
        queryset=Torneos.objects.all(),
        widget=forms.HiddenInput()
    )
    team = forms.ModelChoiceField(
        queryset=Equipos.objects.none(),
        required=False,
        label="Equipo"
    )

    def __init__(self, *args, torneo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if torneo:
            self.fields["torneo"].initial = torneo
            ids = (TorneosEquipos.objects
                   .filter(torneos_id_torneo=torneo)
                   .values_list("equipos_id_equipo", flat=True))
            self.fields["team"].queryset = Equipos.objects.filter(pk__in=ids)
