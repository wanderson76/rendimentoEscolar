# test_db_performance.py
import os
import time
import django
from django.db import connection

# Inicializa o ambiente do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rendimentoEscolar.settings")
django.setup()


def rodar_teste_performance(nome_teste, query, params=None):
    """Executa a query com EXPLAIN ANALYZE para medir a performance real do Postgres."""
    print(f"\n==================================================")
    print(f" 🏃 Rodando: {nome_teste}")
    print(f"==================================================")

    # Adicionamos EXPLAIN ANALYZE para o Postgres detalhar o plano de execução
    query_com_explain = f"EXPLAIN ANALYZE {query}"

    inicio = time.perf_counter()
    with connection.cursor() as cursor:
        cursor.execute(query_com_explain, params or [])
        linhas = cursor.fetchall()

        # Exibe o relatório de planejamento e tempo do próprio PostgreSQL
        for linha in linhas:
            texto_plano = linha[0]
            # Destaca alertas de performance visualmente no terminal
            if "Seq Scan" in texto_plano:
                print(f"⚠️  {texto_plano}")
            elif "Index Scan" in texto_plano:
                print(f"✅ {texto_plano}")
            else:
                print(f"   {texto_plano}")

    fim = time.perf_counter()
    tempo_django = (fim - inicio) * 1000
    print(f"--------------------------------------------------")
    print(f"⏱️  Tempo total capturado pelo Python: {tempo_django:.2f} ms")


# --- CENTRAL DE QUERIES DE SIMULAÇÃO (TODOS OS RELACIONAMENTOS) ---

# 1. Teste de Filtro Simples (Foco em verificar Index vs Seq Scan)
query_filtro = """
    SELECT id, nome, matricula FROM escola_aluno WHERE id = %s;
"""

# 2. Teste de JOIN Complexo (Cruzando Boletim, Aluno e Disciplina)
# Corrigido: filtro do bimestre alterado de '1ºB' (string) para 1 (integer)
query_join = """
    SELECT a.nome, d.nome, b.nota, b.bimestre
    FROM escola_boletimbimestral b
    JOIN escola_aluno a ON b.aluno_id = a.id
    JOIN escola_disciplina d ON b.disciplina_id = d.id
    WHERE a.situacao = 'Ativo' AND b.bimestre = 1;
"""

# 3. Teste da nossa Window Function (A mais pesada do ecossistema)
# Corrigido: Ajustado para refletir a subquery/CTE usada no services.py
query_window = """
    WITH ranking_geral AS (
        SELECT 
            b.aluno_id,
            d.nome AS disciplina,
            b.bimestre,
            b.nota AS nota_aluno,
            ROUND(AVG(b.nota) OVER(PARTITION BY b.disciplina_id, b.bimestre)::numeric, 1) AS media_turma,
            RANK() OVER(PARTITION BY b.disciplina_id, b.bimestre ORDER BY b.nota DESC NULLS LAST) AS ranking_posicao
        FROM escola_boletimbimestral b
        JOIN escola_disciplina d ON b.disciplina_id = d.id
    )
    SELECT * FROM ranking_geral WHERE aluno_id = %s;
"""

if __name__ == "__main__":
    print("🚀 INICIANDO AUDITORIA DE PERFORMANCE DO POSTGRESQL...")

    # ID de teste baseado na Anjolita (ID 4)
    id_teste = 4

    # Executa a bateria de testes simulados
    rodar_teste_performance(
        "Teste 1: Filtro Simples por ID de Aluno", query_filtro, [id_teste]
    )
    rodar_teste_performance(
        "Teste 2: Junção Geral de Relacionamentos (JOINs)", query_join
    )
    rodar_teste_performance(
        "Teste 3: Window Functions e Agregações de Janela", query_window, [id_teste]
    )

    print("\n🏁 Auditoria concluída. Revise as linhas de 'Execution Time' acima!")
