from django.contrib import admin
from .models import Aluno


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    # Removido o 'email' que estava gerando o erro de validação
    list_display = ("id", "nome", "matricula", "situacao")
    search_fields = ("nome", "matricula")
