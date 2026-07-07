import os
from celery import Celery

# Define o módulo de configurações padrão do Django para o 'celery'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rendimentoEscolar.settings")

app = Celery("rendimentoEscolar")

# Lê as configurações do Django usando o prefixo CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Carrega tarefas de todos os apps registrados (procura por tasks.py)
app.autodiscover_tasks()
