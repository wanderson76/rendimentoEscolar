# escola/services.py
import re
import numpy as np
import pandas as pd
from django.db import connection, transaction
from .models import Aluno, Disciplina, BoletimBimestral


def extrair_alertas_intervencao():
    """
    Busca a evolução de notas comparando o Bimestre 1 com o Bimestre 2
    direto na tabela do banco usando SQL nativo.
    """
    query = """
        SELECT 
            a.nome AS aluno_nome,
            d.nome AS disciplina,
            b1.nota AS nota_1b,
            b2.nota AS nota_2b,
            (b2.nota - b1.nota) AS evolucao,
            CASE 
                WHEN b2.nota < 6.0 AND (b2.nota - b1.nota) < 0 THEN '🔴 Intervenção Crítica'
                WHEN b2.nota < 6.0 THEN '🟡 Atenção'
                ELSE '🟢 Estável'
            END AS status_pedagogico
        FROM escola_aluno a
        JOIN escola_boletimbimestral b1 ON a.id = b1.aluno_id AND b1.bimestre = 1
        JOIN escola_boletimbimestral b2 ON a.id = b2.aluno_id AND b2.bimestre = 2 AND b1.disciplina_id = b2.disciplina_id
        JOIN escola_disciplina d ON b1.disciplina_id = d.id
        WHERE (b2.nota - b1.nota) < 0 OR b2.nota < 6.0
        ORDER BY evolucao ASC;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        colunas = [col[0] for col in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]


def importar_mapao(caminho_csv, bimestre):
    """
    Parser avançado calibrado para a estrutura de matriz espalhada do Mapão da SED.
    Mapeia subcolunas baseadas na estrutura real: Nº, M (Nota), F (Faltas), AC.
    """
    try:
        df_bruto = pd.read_csv(
            caminho_csv, sep=None, engine="python", header=None, encoding="utf-8"
        )
    except UnicodeDecodeError:
        df_bruto = pd.read_csv(
            caminho_csv, sep=None, engine="python", header=None, encoding="iso-8859-1"
        )

    # 1. Encontrar onde a tabela real começa
    linha_cabecalho_index = None
    for idx, row in df_bruto.iterrows():
        if "ALUNO" in row.values or "SITUAÇÃO" in row.values:
            linha_cabecalho_index = idx
            break

    if linha_cabecalho_index is None:
        raise ValueError(
            "Não foi possível identificar a linha de cabeçalho (ALUNO/SITUAÇÃO) no arquivo."
        )

    # 2. Mapear as colunas de disciplinas
    linha_disciplinas = df_bruto.iloc[linha_cabecalho_index].tolist()
    mapeamento_disciplinas = {}
    disciplina_atual = None

    for col_idx, valor in enumerate(linha_disciplinas):
        valor_str = str(valor).strip()
        if valor_str and valor_str not in ["ALUNO", "SITUAÇÃO", "TOTAL", "nan"]:
            disciplina_atual = valor_str.split("\n")[0].strip().upper()
            mapeamento_disciplinas[col_idx] = disciplina_atual
        elif valor_str == "nan" and disciplina_atual:
            mapeamento_disciplinas[col_idx] = disciplina_atual
        elif valor_str in ["TOTAL", "ALUNO", "SITUAÇÃO"]:
            disciplina_atual = None

    # 3. Processar linhas de dados (Pula a linha de cabeçalho + a linha com "Nº, M, F, AC")
    df_dados = df_bruto.iloc[linha_cabecalho_index + 2 :]

    with transaction.atomic():
        matricula_base = 20260000

        for idx_linha, row in df_dados.iterrows():
            nome_aluno = str(row.iloc[0]).strip()
            situacao_aluno = str(row.iloc[1]).strip()

            # Evita processar metadados do rodapé da planilha da SED
            if (
                not nome_aluno
                or nome_aluno in ["nan", "", "TOTAL", "MÉDIA", "Percentual", "Legenda"]
                or "Aulas Dadas" in nome_aluno
                or "Menção" in nome_aluno
            ):
                continue

            matricula_gerada = str(matricula_base + idx_linha)

            # Salvar/Atualizar Aluno
            aluno, _ = Aluno.objects.update_or_create(
                id=int(idx_linha),
                defaults={
                    "nome": nome_aluno,
                    "matricula": matricula_gerada,
                    "situacao": situacao_aluno if situacao_aluno != "nan" else "Ativo",
                },
            )

            # Agrupar colunas por matéria
            materias_do_aluno = {}
            for col_idx, nome_materia in mapeamento_disciplinas.items():
                if nome_materia not in materias_do_aluno:
                    materias_do_aluno[nome_materia] = []
                materias_do_aluno[nome_materia].append(row.iloc[col_idx])

            for nome_materia, sub_colunas in materias_do_aluno.items():
                # AJUSTE FIXO:
                # sub_colunas[0] -> Número de chamada
                # sub_colunas[1] -> Menção / Nota
                # sub_colunas[2] -> Faltas
                nota_raw = sub_colunas[1] if len(sub_colunas) > 1 else None
                faltas_raw = sub_colunas[2] if len(sub_colunas) > 2 else 0

                try:
                    if isinstance(nota_raw, str):
                        nota_raw = nota_raw.replace(",", ".")
                    nota = (
                        float(nota_raw)
                        if pd.notna(nota_raw)
                        and str(nota_raw).strip() not in ["", "nan"]
                        else None
                    )
                except ValueError:
                    nota = None

                try:
                    faltas = (
                        int(float(faltas_raw))
                        if pd.notna(faltas_raw)
                        and str(faltas_raw).strip() not in ["", "nan"]
                        else 0
                    )
                except ValueError:
                    faltas = 0

                disciplina, _ = Disciplina.objects.get_or_create(
                    nome=nome_materia, defaults={"codigo": nome_materia[:10]}
                )

                # Persistir Boletim
                BoletimBimestral.objects.update_or_create(
                    aluno=aluno,
                    disciplina=disciplina,
                    bimestre=int(bimestre),
                    defaults={"nota": nota, "faltas": faltas, "aulas_computadas": 40},
                )
