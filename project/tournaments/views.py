# tournaments/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, FormView
from django.shortcuts import redirect, render
from django.db import transaction
from django.db.models import Q, Exists, OuterRef

# IMPORTA DESDE ESTA APP (tu models genérico está dentro de tournaments/models.py)
from .models import (
    Torneos,
    Equipos,
    TorneosEquipos,
    EquiposParticipantes,
    Participantes,
)

from .forms import TeamCreateForm, InscripcionForm


class TournamentListView(ListView):
    model = Torneos
    template_name = "list_tournament.html"
    context_object_name = "tournaments"

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        qs = (
            Torneos.objects
            .select_related("disciplinas_id_disciplina")
            .annotate(
                tiene_equipos=Exists(
                    TorneosEquipos.objects.filter(torneos_id_torneo=OuterRef("pk"))
                )
            )
            .order_by("fecha_inicio")
        )
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(disciplinas_id_disciplina__nombre__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search"] = self.request.GET.get("q", "")
        return ctx


class TournamentDetailView(DetailView):
    model = Torneos
    template_name = "tournament_detail.html"
    context_object_name = "tournament"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        torneo = self.object

        equipos_ids = (
            TorneosEquipos.objects
            .filter(torneos_id_torneo=torneo)
            .values_list("equipos_id_equipo", flat=True)
        )
        ctx["teams"] = Equipos.objects.filter(pk__in=equipos_ids)

        ctx["join_form"] = InscripcionForm(torneo=torneo)
        return ctx


class TeamCreateView(LoginRequiredMixin, CreateView):
    form_class = TeamCreateForm
    template_name = "create_team.html"

    def form_valid(self, form):
        team = form.save(commit=False)
        team.save()
        return redirect("tournaments:team_detail", pk=team.pk)


class TeamDetailView(DetailView):
    model = Equipos
    template_name = "team_detail.html"
    context_object_name = "team"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        team = self.object
        miembros = []

        # En tu modelo actual: una fila por equipo con 2 slots:
        #   - id_participante (FK)
        #   - id_participante1 (FloatField con el id)
        try:
            ep = EquiposParticipantes.objects.get(equipos_id_equipo=team)
            if ep.id_participante_id:
                try:
                    miembros.append(Participantes.objects.get(pk=ep.id_participante_id))
                except Participantes.DoesNotExist:
                    pass
            if ep.id_participante1:
                try:
                    miembros.append(Participantes.objects.get(pk=ep.id_participante1))
                except Participantes.DoesNotExist:
                    pass
        except EquiposParticipantes.DoesNotExist:
            pass

        ctx["members"] = miembros
        return ctx


class JoinTeamView(LoginRequiredMixin, FormView):
    """
    - Si el torneo tiene equipos: añade el participante a EquiposParticipantes (hasta 2 slots).
    - Si es individual (sin equipos asociados): muestra aviso (no hay tabla Torneo↔Participante).
    """
    form_class = InscripcionForm
    template_name = "join_team.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        t_id = self.request.GET.get("t")
        if t_id:
            try:
                kwargs["torneo"] = Torneos.objects.get(pk=t_id)
            except Torneos.DoesNotExist:
                pass
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        torneo = form.cleaned_data["torneo"]
        correo = form.cleaned_data["correo"]

        # Participante por correo
        try:
            participante = Participantes.objects.get(correo=correo)
        except Participantes.DoesNotExist:
            form.add_error("correo", "No existe un participante con ese correo.")
            return self.form_invalid(form)

        # ¿El torneo tiene equipos?
        equipos_ids = (
            TorneosEquipos.objects
            .filter(torneos_id_torneo=torneo)
            .values_list("equipos_id_equipo", flat=True)
        )
        hay_equipos = Equipos.objects.filter(pk__in=equipos_ids).exists()

        if hay_equipos:
            equipo = form.cleaned_data.get("team")
            if equipo is None:
                form.add_error("team", "Debes seleccionar un equipo.")
                return self.form_invalid(form)

            # Validar pertenencia del equipo al torneo
            if not TorneosEquipos.objects.filter(
                torneos_id_torneo=torneo, equipos_id_equipo=equipo
            ).exists():
                form.add_error("team", "Este equipo no pertenece a este torneo.")
                return self.form_invalid(form)

            # Fila única por equipo con dos slots
            ep, _ = EquiposParticipantes.objects.get_or_create(
                equipos_id_equipo=equipo,
                defaults={"id_participante": None, "id_participante1": None},
            )

            # ¿ya está?
            if ep.id_participante_id == participante.pk or ep.id_participante1 == participante.pk:
                form.add_error(None, "Este participante ya está en el equipo.")
                return self.form_invalid(form)

            # ocupar slot A o B
            if ep.id_participante_id is None:
                ep.id_participante = participante
                ep.save()
            elif not ep.id_participante1:
                ep.id_participante1 = float(participante.pk)  # segundo slot es FloatField
                ep.save()
            else:
                form.add_error(None, "El equipo está lleno.")
                return self.form_invalid(form)

            return redirect("tournaments:team_detail", pk=equipo.pk)

        # MODO INDIVIDUAL: aún no hay tabla Torneo↔Participante en la BD
        context = {
            "tournament": torneo,
            "teams": [],
            "join_form": InscripcionForm(torneo=torneo),
            "warning_individual": (
                "Torneo detectado como INDIVIDUAL, pero no existe una tabla de inscripciones "
                "Torneo↔Participante en la BD. Sugerencia: crear 'torneos_participantes' "
                "(PK compuesta: torneos_id_torneo + id_participante, o surrogate key)."
            ),
        }
        return render(self.request, "tournament_detail.html", context)
