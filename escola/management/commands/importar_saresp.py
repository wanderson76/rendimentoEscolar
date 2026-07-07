# escola/management/commands/importar_saresp.py
import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from escola.models import SarespResultado


class Command(BaseCommand):
    help = "Faz o parsing dinâmico e importa a tabela de cursos do arquivo Resultados SARESP TécnicoSSB.xlsx."

    def add_arguments(self, parser):
        parser.add_argument(
            "--arquivo",
            type=str,
            default="Resultados SARESP TécnicoSSB.xlsx",
            help="Nome do arquivo Excel do SARESP técnico",
        )

    def handle(self, *args, **options):
        caminho = options["arquivo"]

        if not os.path.exists(caminho):
            raise CommandError(
                f"Arquivo Excel '{caminho}' não foi encontrado na raiz do projeto."
            )

        self.stdout.write(
            self.style.WARNING(f"🚀 Lendo matriz bruta do SARESP: {caminho}...")
        )

        try:
            # Lê o Excel de forma bruta (sem assumir cabeçalhos na linha 0)
            df_bruto = pd.read_excel(caminho, engine="openpyxl", header=None)

            # 1. Encontra dinamicamente em qual linha está a tabela de cursos
            linha_cabecalho_idx = None
            for idx, row in df_bruto.iterrows():
                if "CURSO" in row.values:
                    linha_cabecalho_idx = idx
                    break

            if linha_cabecalho_idx is None:
                raise ValueError(
                    "Não foi possível encontrar a coluna 'CURSO' dentro do arquivo Excel."
                )

            # 2. Captura os nomes das colunas daquela linha específica
            colunas_reais = [
                str(col).strip() for col in df_bruto.iloc[linha_cabecalho_idx].tolist()
            ]

            # Descobre em qual índice numérico de coluna estão o 'CURSO' e a média ('Méd')
            idx_col_curso = colunas_reais.index("CURSO")

            if "Méd" in colunas_reais:
                idx_col_media = colunas_reais.index("Méd")
            elif "MÉD" in colunas_reais:
                idx_col_media = colunas_reais.index("MÉD")
            else:
                # Fallback caso usem outro nome (é a 7ª coluna com base no seu print anterior, ou seja, índice 6)
                idx_col_media = 6

            # 3. Corta os dados apenas para o que está abaixo do cabeçalho encontrado
            df_dados = df_bruto.iloc[linha_cabecalho_idx + 1 :]

            contador = 0

            for _, row in df_dados.iterrows():
                curso_raw = row.iloc[idx_col_curso]

                # Se a linha acabar ou chegar no totalizador geral, encerra o loop
                if (
                    pd.isna(curso_raw)
                    or str(curso_raw).strip() == ""
                    or str(curso_raw).upper() == "TOTAL IFTP"
                ):
                    continue

                nome_curso = str(curso_raw).strip()
                media_raw = row.iloc[idx_col_media]

                # Conversão numérica altamente resiliente
                try:
                    if isinstance(media_raw, str):
                        media_raw = media_raw.replace(",", ".")
                    media = (
                        float(media_raw)
                        if pd.notna(media_raw) and str(media_raw).strip() != ""
                        else 0.0
                    )
                except ValueError:
                    media = 0.0

                # Atualiza ou Cria no PostgreSQL
                SarespResultado.objects.update_or_create(
                    componente_tecnico=nome_curso,
                    defaults={
                        "media_estado": media,
                        "percentual_proficiencia_avancado": 0.0,
                    },
                )
                contador += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 Sucesso absoluto! {contador} cursos técnicos salvos e atualizados no PostgreSQL."
                )
            )

        except Exception as e:
            raise CommandError(f"Falha ao processar o arquivo Excel: {str(e)}")
