# escola/views.py
import json
from django.db.models import Avg, Sum, Q
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view

from .models import (
    Aluno,
    BoletimBimestral,
    SarespResultado,
    IntervencaoPedagogica,
    MetricaDesempenho,
)
from .services import extrair_alertas_intervencao


def dashboard_aluno(request, aluno_id):
    # Proteção: Se o aluno não existir, retorna 404 limpo em vez de quebrar com Erro 500
    aluno = get_object_or_404(Aluno, id=aluno_id)

    # Otimização: Traz todos os boletins necessários em uma única consulta ao banco
    boletins = BoletimBimestral.objects.filter(aluno=aluno).select_related("disciplina")

    # Extrai os nomes das disciplinas de forma única
    labels_disciplinas = list(
        boletins.values_list("disciplina__nome", flat=True).distinct()
    )

    notas_b1 = []
    notas_b2 = []
    engajamento = []

    # Organiza os dados em memória (evita dezenas de consultas repetidas ao banco)
    for disc in labels_disciplinas:
        b1 = next(
            (b for b in boletins if b.disciplina.nome == disc and b.bimestre == 1), None
        )
        b2 = next(
            (b for b in boletins if b.disciplina.nome == disc and b.bimestre == 2), None
        )

        notas_b1.append(float(b1.nota) if b1 and b1.nota is not None else 0.0)
        notas_b2.append(float(b2.nota) if b2 and b2.nota is not None else 0.0)

        if b2 and b2.aulas_computadas > 0:
            freq = ((b2.aulas_computadas - b2.faltas) / b2.aulas_computadas) * 100
        else:
            freq = 100.0
        engajamento.append(round(freq, 1))

    context = {
        "aluno": aluno,
        "labels_disciplinas": json.dumps(labels_disciplinas),
        "notas_b1": json.dumps(notas_b1),
        "notas_b2": json.dumps(notas_b2),
        "engajamento": json.dumps(engajamento),
    }
    return render(request, "escola/dashboard.html", context)


def painel_professor(request):
    alertas = extrair_alertas_intervencao()
    context = {
        "alertas_criticos": alertas,
    }
    return render(request, "escola/painel_professor.html", context)


def dashboard_macro_turma(request):
    """
    Refatorado de forma dinâmica. Agrupa boletins por disciplina e gera
    as médias gerais em tempo real direto dos dados do Mapão da SED.
    """
    # 1. Carrega os resultados do SARESP previamente para evitar consultas N+1
    resultados_saresp = list(SarespResultado.objects.all())
    tabela_performance = []

    # 2. Agregação dinâmica: Calcula médias de notas por bimestre e soma as faltas de toda a turma
    dados_agregados = BoletimBimestral.objects.values("disciplina__nome").annotate(
        media_1b=Avg("nota", filter=Q(bimestre=1)),
        media_2b=Avg("nota", filter=Q(bimestre=2)),
        total_faltas=Sum("faltas"),
    )

    # 3. Faz o cruzamento inteligente com a planilha do SARESP populada via Excel
    for item in dados_agregados:
        nome_disciplina = item["disciplina__nome"]

        # Faz a busca em memória do benchmark do estado
        referencia_saresp = next(
            (
                r
                for r in resultados_saresp
                if nome_disciplina[:15].lower() in r.componente_tecnico.lower()
            ),
            None,
        )

        media_estado = referencia_saresp.media_estado if referencia_saresp else 6.0
        media_2b = round(item["media_2b"], 2) if item["media_2b"] else 0.0
        desvio = round(media_2b - media_estado, 2)

        tabela_performance.append(
            {
                "disciplina": nome_disciplina,
                "media_1b": round(item["media_1b"], 2) if item["media_1b"] else 0.0,
                "media_2b": media_2b,
                "total_faltas": item["total_faltas"] or 0,
                "media_estado_saresp": media_estado,
                "desvio_estratetigo": desvio,
                "status": (
                    "🟢 Acima da Média Estadual"
                    if desvio >= 0
                    else "🔴 Defasagem Curricular"
                ),
            }
        )

    intervencoes_ativas = IntervencaoPedagogica.objects.filter(
        status__in=["PENDENTE", "EM_ANDAMENTO"]
    )

    context = {
        "tabela_performance": tabela_performance,
        "intervencoes_ativas": intervencoes_ativas,
    }
    return render(request, "escola/dashboard_macro.html", context)


@api_view(["GET"])
def buscar_radar_aluno(request, aluno_id):
    componentes = ["LÓGICA", "METODOLOGIAS ÁGEIS", "CARREIRA", "REDES"]

    # Otimização: Traz as métricas filtrando apenas o que é estritamente necessário
    metricas = MetricaDesempenho.objects.filter(
        aluno_id=aluno_id, disciplina__iexact__in=componentes
    )

    dados_grafico = {comp: 0.0 for comp in componentes}
    for m in metricas:
        nome_comp = m.disciplina.upper()
        if nome_comp in dados_grafico:
            dados_grafico[nome_comp] = float(m.nota)

    return JsonResponse(
        {
            "labels": list(dados_grafico.keys()),
            "notas": list(dados_grafico.values()),
            "corte": [6.0] * len(componentes),
        }
    )
