from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Aluno


class AlunoAPITestCase(APITestCase):

    def setUp(self):
        # Este método roda antes de cada teste, preparando dados iniciais se necessário
        self.url_listagem = reverse(
            "aluno-list"
        )  # Descobre a rota /api/v1/alunos/ automaticamente

    def test_deve_criar_um_aluno_valido_via_api(self):
        """Garante que a API consegue cadastrar um aluno com sucesso"""
        dados_novo_aluno = {
            "nome": "Carlos Silva",
            "email": "carlos.silva@escola.com",
            "matricula": "20260001",
        }

        # Simula uma requisição POST enviando o JSON
        resposta = self.client.post(self.url_listagem, dados_novo_aluno, format="json")

        # Asserções (Validações do TDD)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Aluno.objects.count(), 1)
        self.assertEqual(Aluno.objects.get().nome, "Carlos Silva")

    def test_nao_deve_permitir_duplicar_email_de_aluno(self):
        """Garante que a regra de unicidade do e-mail é respeitada pela API"""
        # Criamos o primeiro aluno diretamente no banco de teste
        Aluno.objects.create(
            nome="Existente", email="duplicado@escola.com", matricula="111"
        )

        # Tentamos enviar outro aluno com o mesmo e-mail via API
        dados_duplicados = {
            "nome": "Outro Nome",
            "email": "duplicado@escola.com",
            "matricula": "222",
        }

        resposta = self.client.post(self.url_listagem, dados_duplicados, format="json")

        # Deve retornar erro 400 (Bad Request) e não criar o registro
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Aluno.objects.count(), 1)
