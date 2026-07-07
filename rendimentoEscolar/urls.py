"""
URL configuration for rendimentoEscolar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# rendimentoEscolar/urls.py
from django.contrib import admin
from django.urls import path, include
from escola.views import dashboard_aluno  # Mantendo seus imports existentes

urlpatterns = [
    path("admin/", admin.site.urls),
    # Inclui as rotas do aplicativo escola
    path("", include("escola.urls")),
    # Sua rota individual (exemplo com base no seu print de tela)
    path("dashboard/<int:aluno_id>/", dashboard_aluno, name="dashboard_aluno"),
]
