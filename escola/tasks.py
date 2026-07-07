import time
from celery import shared_task
from django.db import transaction
from .models import Aluno, Disciplina, MetricaDesempenho


@shared_task
def importar_metricas_em_massa_async(aluno_id, dados_metricas):
    """Tarefa assíncrona executada de forma otimizada via Bulk Insert."""
    print(f"Iniciando importação pesada para o aluno ID {aluno_id}...")

    # Simula o delay de processamento matemático pesado
    time.sleep(5)

    try:
        aluno = Aluno.objects.get(id=aluno_id)
    except Aluno.DoesNotExist:
        print(f"Erro: Aluno ID {aluno_id} não encontrado.")
        return "Falha: Aluno inexistente."

    # --- OTIMIZAÇÃO PARA FOREIGNEY ---
    # Coletamos todos os nomes de disciplinas únicas que vieram no payload
    nomes_disciplinas = {item["disciplina"].strip().upper() for item in dados_metricas}

    # Garantimos que todas existam no banco (se não existirem, criamos)
    dicionario_disciplinas = {}
    for nome in nomes_disciplinas:
        # Usando upper ou a formatação exata do seu Screenshot_2026-07-05_21-41-18.png
        disciplina_obj, _ = Disciplina.objects.get_or_create(nome=nome)
        dicionario_disciplinas[nome] = disciplina_obj
    # ---------------------------------

    # Criamos uma lista de instâncias em memória utilizando os objetos de Disciplina encontrados
    novas_metricas = [
        MetricaDesempenho(
            aluno=aluno,
            disciplina=dicionario_disciplinas[item["disciplina"].strip().upper()],
            nota=item["nota"],
            frequencia_porcentagem=item["frequencia"],
            data_avaliacao=item["data"],
        )
        for item in dados_metricas
    ]

    # Executa tudo em uma única transação atômica e em um só comando SQL INSERT
    with transaction.atomic():
        MetricaDesempenho.objects.bulk_create(novas_metricas)

    print(f"Importação concluída com sucesso para o aluno {aluno.nome}!")
    return f"Inseridas {len(novas_metricas)} métricas com bulk_create."
