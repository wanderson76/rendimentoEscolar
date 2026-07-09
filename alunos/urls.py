# alunos/urls.py
from django.urls import path
from . import views

app_name = "alunos"

urlpatterns = [
    # Painel Geral de Extremos (Top 10 / Alerta 10)
    path("extremos/", views.painel_extremos_turma, name="painel_extremos"),
    # Ficha de Diagnóstico Individual e Triagem
    path(
        "diagnostico/<int:aluno_id>/",
        views.diagnostico_individual,
        name="diagnostico_individual",
    ),
    # Cruzamento Clínico Avançado e Gráfico Radar
    path(
        "clinico/<int:aluno_id>/", views.diagnostico_clinico, name="diagnostico_clinico"
    ),
]
