# escola/urls.py
from django.urls import path
from . import views

app_name = "escola"

urlpatterns = [
    # Rota para a Visão Macro da Turma
    path("dashboard/macro/", views.dashboard_macro_turma, name="dashboard_macro"),
    # Rota para o Dashboard Individual do Aluno (Alvo da paginação e links)
    path("dashboard/<int:aluno_id>/", views.dashboard_aluno, name="dashboard_aluno"),
    # Endpoint da API do Gráfico Radar
    path("api/radar/<int:aluno_id>/", views.buscar_radar_aluno, name="api_radar_aluno"),
]
