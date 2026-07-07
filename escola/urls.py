# escola/urls.py
from django.urls import path
from .views import dashboard_macro_turma

app_name = "escola"

urlpatterns = [
    # Rota para a Visão Macro da Turma
    path("dashboard/macro/", dashboard_macro_turma, name="dashboard_macro"),
]
