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
    """
    Renderiza o dashboard individual do aluno com dados estruturados para o Chart.js
    e suporte a paginação sequencial (Avançar/Recuar).
    """
    # Proteção: Se o aluno não existir, retorna 404 limpo
    aluno = get_object_or_404(Aluno, id=aluno_id)

    # ⏭️ Motor de Paginação Sequencial (Apenas alunos com situação Ativo)
    aluno_anterior = (
        Aluno.objects.filter(id__lt=aluno_id, situacao="Ativo").order_by("-id").first()
    )
    aluno_proximo = (
        Aluno.objects.filter(id__gt=aluno_id, situacao="Ativo").order_by("id").first()
    )

    # Otimização: Traz todos os boletins necessários em uma única consulta ao banco
    boletins = BoletimBimestral.objects.filter(aluno=aluno).select_related("disciplina")

    # Extrai os nomes das disciplinas de forma única
    labels_disciplinas = list(
        boletins.values_list("disciplina__nome", flat=True).distinct()
    )

    notas_b1 = []
    notas_b2 = []
    engajamento = []

    # Organiza os dados em memória (evita consultas repetidas ao banco dentro do loop)
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
        "aluno_anterior_id": aluno_anterior.id if aluno_anterior else None,
        "aluno_proximo_id": aluno_proximo.id if aluno_proximo else None,
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
    Agrupa os boletins por disciplina e gera as médias em tempo real,
    capturando dinamicamente o referer para voltar à ficha do aluno correta.
    """
    resultados_saresp = list(SarespResultado.objects.all())
    tabela_performance = []

    # 🎯 CAPTURA DINÂMICA DO REFERER (Origem da navegação)
    # Se veio de um diagnóstico (ex: /alunos/diagnostico/30/), ele guarda essa URL exata.
    url_anterior = request.META.get("HTTP_REFERER", "")

    if "alunos/diagnostico/" in url_anterior:
        url_retorno = url_anterior
    else:
        # Fallback de segurança caso acesse a visão macro diretamente sem vir de um aluno
        url_retorno = "/alunos/diagnostico/30/"

    # Agregação dinâmica direta via banco de dados
    dados_agregados = BoletimBimestral.objects.values("disciplina__nome").annotate(
        media_1b=Avg("nota", filter=Q(bimestre=1)),
        media_2b=Avg("nota", filter=Q(bimestre=2)),
        total_faltas=Sum("faltas"),
    )

    for item in dados_agregados:
        nome_disciplina = item["disciplina__nome"]

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
        desvío = round(media_2b - media_estado, 2)

        tabela_performance.append(
            {
                "disciplina": nome_disciplina,
                "media_1b": round(item["media_1b"], 2) if item["media_1b"] else 0.0,
                "media_2b": media_2b,
                "total_faltas": item["total_faltas"] or 0,
                "media_estado_saresp": media_estado,
                "desvio_estratetigo": desvío,
                "status": (
                    "🟢 Acima da Média Estadual"
                    if desvío >= 0
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
        "url_retorno": url_retorno,  # 🌟 Enviando para o HTML
    }
    return render(request, "escola/dashboard_macro.html", context)


@api_view(["GET"])
def buscar_radar_aluno(request, aluno_id):
    """API que alimenta o Gráfico Radar de competências."""
    componentes = ["LÓGICA", "METODOLOGIAS ÁGEIS", "CARREIRA", "REDES"]

    # CORREÇÃO: Como disciplina é uma ForeignKey, acessamos o nome usando o lookahead '__nome__iexact__in'
    metricas = MetricaDesempenho.objects.filter(
        aluno_id=aluno_id, disciplina__nome__iexact__in=componentes
    ).select_related("disciplina")

    dados_grafico = {comp: 0.0 for comp in componentes}
    for m in metricas:
        nome_comp = m.disciplina.nome.upper()
        if nome_comp in dados_grafico:
            dados_grafico[nome_comp] = float(m.nota)

    return JsonResponse(
        {
            "labels": list(dados_grafico.keys()),
            "notas": list(dados_grafico.values()),
            "corte": [6.0] * len(componentes),
        }
    )
