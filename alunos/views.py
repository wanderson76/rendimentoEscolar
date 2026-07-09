# alunos/views.py
from django.shortcuts import render, get_object_or_404
from escola.models import Aluno

from .services import (
    obter_top_10_alunos,
    obter_piores_10_alunos,
    obter_analise_profunda_aluno,
    obter_dados_comparativos,
)


def diagnostico_individual(request, aluno_id):
    """Exibe o painel de triagem individual do aluno com botões Próximo/Anterior."""
    aluno = get_object_or_404(Aluno, id=aluno_id)

    # ⏭️ Motor de Paginação Sequencial (Alunos Ativos)
    aluno_anterior = (
        Aluno.objects.filter(id__lt=aluno_id, situacao="Ativo").order_by("-id").first()
    )
    aluno_proximo = (
        Aluno.objects.filter(id__gt=aluno_id, situacao="Ativo").order_by("id").first()
    )

    # Executa a query de alta performance do PostgreSQL
    boletim_analitico = obter_analise_profunda_aluno(aluno_id)

    # Motor de Tomada de Decisão Pedagógica (Geração de Alertas)
    alertas_intervencao = []
    for item in boletim_analitico:
        # Alerta de Nota abaixo da Média da Sala
        if (
            item["nota_aluno"]
            and item["nota_aluno"] < 6.0
            and item["nota_aluno"] < item["media_turma"]
        ):
            alertas_intervencao.append(
                {
                    "disciplina": item["disciplina"],
                    "bimestre": item["bimestre"],
                    "motivo": f"Nota ({item['nota_aluno']}) abaixo da média da turma ({item['media_turma']}). Posição atual: {item['ranking_posicao']}º no ranking.",
                    "grau_risco": "🔴 Crítico (Defasagem)",
                }
            )

        # Alerta de Absenteísmo (Risco por Faltas)
        if item["faltas"] > 10:
            alertas_intervencao.append(
                {
                    "disciplina": item["disciplina"],
                    "bimestre": item["bimestre"],
                    "motivo": f"O estudante acumula {item['faltas']} faltas neste componente curricular.",
                    "grau_risco": "🟡 Atenção (Frequência)",
                }
            )

    context = {
        "aluno": aluno,
        "boletim_analitico": boletim_analitico,
        "alertas_intervencao": alertas_intervencao,
        "aluno_anterior_id": aluno_anterior.id if aluno_anterior else None,
        "aluno_proximo_id": aluno_proximo.id if aluno_proximo else None,
    }
    return render(request, "alunos/diagnostico.html", context)


def painel_extremos_turma(request):
    top_10 = obter_top_10_alunos()
    piores_10 = obter_piores_10_alunos()

    context = {
        "top_10": top_10,
        "piores_10": piores_10,
    }
    return render(request, "alunos/extremos.html", context)


def diagnostico_clinico(request, aluno_id):
    """Painel de cruzamento de dados com Gráfico Radar e suporte à Neuropsicologia/ABA."""
    aluno_alvo = get_object_or_404(Aluno, id=aluno_id)

    # Corrigido: alterado order_index para order_by
    todos_alunos = Aluno.objects.filter(situacao="Ativo").order_by("nome")

    # Captura o ID do aluno comparativo via query string (ex: ?comparar_com=5)
    comparar_com_id = request.GET.get("comparar_com")

    # Dados de boletim analítico tradicional
    historico = obter_analise_profunda_aluno(aluno_id)

    # Processa dados para o Gráfico Radar
    dados_radar = obter_dados_comparativos(aluno_id, comparar_com_id)

    # Estrutura os dados para o Chart.js ler nativamente no Javascript
    disciplinas = sorted(list(set(item["disciplina"] for item in dados_radar)))

    notas_aluno_a = []
    notas_aluno_b = []
    nome_aluno_b = "Comparativo não selecionado"

    for disc in disciplinas:
        # Aluno Principal
        nota_a = next(
            (
                x["media_disciplina"]
                for x in dados_radar
                if x["aluno_id"] == aluno_id and x["disciplina"] == disc
            ),
            0,
        )
        notas_aluno_a.append(float(nota_a))

        # Aluno Comparativo
        if comparar_com_id:
            nota_b = next(
                (
                    x["media_disciplina"]
                    for x in dados_radar
                    if x["aluno_id"] == int(comparar_com_id) and x["disciplina"] == disc
                ),
                0,
            )
            notas_aluno_b.append(float(nota_b))
            if dados_radar:
                nome_aluno_b = next(
                    (
                        x["aluno_nome"]
                        for x in dados_radar
                        if x["aluno_id"] == int(comparar_com_id)
                    ),
                    "Aluno B",
                )

    context = {
        "aluno": aluno_alvo,
        "todos_alunos": todos_alunos,
        "historico": historico,
        "chart_labels": disciplinas,
        "chart_data_a": notas_aluno_a,
        "chart_data_b": notas_aluno_b,
        "nome_aluno_b": nome_aluno_b,
        "comparar_com_id": comparar_com_id,
    }
    return render(request, "alunos/diagnostico_clinico.html", context)
