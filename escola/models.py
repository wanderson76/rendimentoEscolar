from django.db import models


class Aluno(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    matricula = models.CharField(max_length=20, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class MetricaDesempenho(models.Model):
    # Relacionamento 1:N (Um aluno tem várias métricas)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="metricas")
    disciplina = models.CharField(max_length=100)
    nota = models.DecimalField(max_digits=5, decimal_places=2)
    frequencia_porcentagem = models.IntegerField()
    data_avaliacao = models.DateField()

    # Regra de Negócio incorporada no modelo
    @property
    def aprovado(self):
        return self.nota >= 7.0 and self.frequencia_porcentagem >= 75

    def __str__(self):
        return f"{self.aluno.nome} - {self.disciplina}: {self.nota}"
