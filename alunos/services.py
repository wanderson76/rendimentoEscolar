# alunos/services.py
from django.db import connection


def obter_analise_profunda_aluno(aluno_id):
    """
    Calcula a média e o ranking considerando toda a turma (Subquery)
    e depois filtra os dados do aluno específico para exibição.
    """
    query = """
        WITH ranking_geral AS (
            SELECT 
                b.aluno_id,
                d.nome AS disciplina,
                b.bimestre,
                b.nota AS nota_aluno,
                b.faltas,
                ROUND(AVG(b.nota) OVER(PARTITION BY b.disciplina_id, b.bimestre)::numeric, 1) AS media_turma,
                RANK() OVER(PARTITION BY b.disciplina_id, b.bimestre ORDER BY b.nota DESC NULLS LAST) AS ranking_posicao,
                COUNT(*) OVER(PARTITION BY b.disciplina_id, b.bimestre) AS total_alunos_turma
            FROM escola_boletimbimestral b
            JOIN escola_disciplina d ON b.disciplina_id = d.id
        )
        SELECT 
            disciplina,
            bimestre,
            nota_aluno,
            faltas,
            media_turma,
            ranking_posicao,
            total_alunos_turma
        FROM ranking_geral
        WHERE aluno_id = %s
        ORDER BY bimestre ASC, disciplina ASC;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [aluno_id])
        colunas = [col[0] for col in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]


# Adicione ao final de alunos/services.py


def obter_top_10_alunos():
    """Retorna os 10 alunos com as maiores médias gerais consolidadas no banco."""
    query = """
        SELECT 
            a.id,
            a.nome,
            a.matricula,
            ROUND(AVG(b.nota)::numeric, 2) AS media_geral,
            SUM(b.faltas) AS total_faltas
        FROM escola_aluno a
        JOIN escola_boletimbimestral b ON a.id = b.aluno_id
        WHERE a.situacao = 'Ativo'
        GROUP BY a.id, a.nome, a.matricula
        HAVING AVG(b.nota) IS NOT NULL
        ORDER BY media_geral DESC
        LIMIT 10;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        colunas = [col[0] for col in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]


def obter_piores_10_alunos():
    """Retorna os 10 alunos com as menores médias gerais consolidadas (foco em intervenção)."""
    query = """
        SELECT 
            a.id,
            a.nome,
            a.matricula,
            ROUND(AVG(b.nota)::numeric, 2) AS media_geral,
            SUM(b.faltas) AS total_faltas
        FROM escola_aluno a
        JOIN escola_boletimbimestral b ON a.id = b.aluno_id
        WHERE a.situacao = 'Ativo'
        GROUP BY a.id, a.nome, a.matricula
        HAVING AVG(b.nota) IS NOT NULL
        ORDER BY media_geral ASC
        LIMIT 10;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        colunas = [col[0] for col in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]


# Adicione ao final de alunos/services.py


def obter_dados_comparativos(aluno_a_id, aluno_b_id=None):
    """
    Retorna as médias por disciplina de dois alunos para cruzamento no Gráfico Radar.
    """
    query = """
        SELECT 
            b.aluno_id,
            a.nome AS aluno_nome,
            d.nome AS disciplina,
            ROUND(AVG(b.nota)::numeric, 1) AS media_disciplina
        FROM escola_boletimbimestral b
        JOIN escola_aluno a ON b.aluno_id = a.id
        JOIN school_disciplina d ON b.disciplina_id = d.id
        WHERE b.aluno_id IN (%s, %s)
        GROUP BY b.aluno_id, a.nome, d.nome
        ORDER BY d.nome;
    """
    # Se não houver segundo aluno para comparar, passamos o primeiro ID duas vezes para não quebrar o IN
    aluno_b_id = aluno_b_id or aluno_a_id

    with connection.cursor() as cursor:
        cursor.execute(query, [aluno_a_id, aluno_b_id])
        colunas = [col[0] for col in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]
