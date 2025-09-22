from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    path("", views.TournamentListView.as_view(), name="list"),
    path("<int:pk>/", views.TournamentDetailView.as_view(), name="detail"),
    path("teams/create/", views.TeamCreateView.as_view(), name="create_team"),
    path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("join/", views.JoinTeamView.as_view(), name="join_team"),
]

