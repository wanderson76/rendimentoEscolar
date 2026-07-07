import os
from django.core.management.base import BaseCommand, CommandError
from escola.services import importar_mapao


class Command(BaseCommand):
    help = "Importa de forma sequencial os dados dos mapões CSV obtidos do SED para o banco de dados."

    def add_arguments(self, parser):
        # Permite passar caminhos customizados via terminal se necessário, mantendo os originais como default
        parser.add_argument(
            "--b1",
            type=str,
            default="MAPAO_WALKIR_VERGANI_6082_-_DESENVOLVIMENTO_DE_SISTEMAS_-_2ª_SERIE_C_INTEGRAL_9H_ANUAL_CONSELHO_PRIMEIRO_BIMESTRE_03072026_1536 - Mapão.csv",
            help="Caminho do arquivo CSV do 1º Bimestre",
        )
        parser.add_argument(
            "--b2",
            type=str,
            default="MAPAO_WALKIR_VERGANI_6082_-_DESENVOLVIMENTO_DE_SISTEMAS_-_2ª_SERIE_C_INTEGRAL_9H_ANUAL_CONSELHO_SEGUNDO_BIMESTRE_03072026_1536 - Mapão.csv",
            help="Caminho do arquivo CSV do 2º Bimestre",
        )

    def handle(self, *args, **options):
        arquivos_importacao = [
            {"bimestre": 1, "caminho": options["b1"]},
            {"bimestre": 2, "caminho": options["b2"]},
        ]

        for item in arquivos_importacao:
            bimestre = item["bimestre"]
            caminho = item["caminho"]

            self.stdout.write(
                self.style.WARNING(f"👉 Verificando arquivo do {bimestre}º Bimestre...")
            )

            # Validação amigável se o arquivo existe antes de chamar o Pandas
            if not os.path.exists(caminho):
                raise CommandError(
                    f"Arquivo não encontrado no diretório atual: '{caminho}'. "
                    f"Verifique se o nome mudou ou se ele está na raiz do projeto."
                )

            try:
                self.stdout.write(
                    f"🚀 Processando e populando dados do {bimestre}º Bimestre..."
                )
                importar_mapao(caminho, bimestre=bimestre)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {bimestre}º Bimestre importado com sucesso!")
                )

            except Exception as e:
                raise CommandError(
                    f"Erro crítico ao processar o {bimestre}º Bimestre: {str(e)}"
                )

        self.stdout.write(
            self.style.SUCCESS("\n🎉 Processo de ETL concluído com sucesso!")
        )
