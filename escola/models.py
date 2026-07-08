from django.db import models


class Aluno(models.Model):
    nome = models.CharField("Nome do Aluno", max_length=255)
    matricula = models.CharField(
        "Matrícula (SED)", max_length=50, unique=True, null=True, blank=True
    )
    situacao = models.CharField("Situação Acadêmica", max_length=50, default="Ativo")

    def __str__(self):
        return self.nome


class Disciplina(models.Model):
    nome = models.CharField("Nome do Componente Curricular", max_length=255)
    codigo = models.CharField(
        "Código da Disciplina", max_length=20, null=True, blank=True
    )

    def __str__(self):
        return self.nome


class BoletimBimestral(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="boletins")
    disciplina = models.ForeignKey(
        Disciplina, on_delete=models.CASCADE, related_name="boletins"
    )
    bimestre = models.IntegerField(
        "Bimestre", choices=[(1, "1º Bimestre"), (2, "2º Bimestre")]
    )
    nota = models.FloatField("Nota Real", null=True, blank=True)
    faltas = models.IntegerField("Quantidade de Faltas", default=0)
    aulas_computadas = models.IntegerField("Aulas Dadas", default=0)

    class Meta:
        verbose_name = "Boletim Bimestral"
        verbose_name_plural = "Boletins Bimestrais"
        constraints = [
            models.UniqueConstraint(
                fields=["aluno", "disciplina", "bimestre"],
                name="unique_boletim_aluno_disciplina_bimestre",
            )
        ]
        # INTERVENÇÃO DE PERFORMANCE NO POSTGRESQL
        indexes = [
            # Turbina buscas micro de boletins de um aluno específico
            models.Index(fields=["aluno", "disciplina", "bimestre"]),
            # Turbina agregações dinâmicas macro (Média de notas e soma de faltas por matéria)
            models.Index(fields=["disciplina", "bimestre"]),
        ]

    def __str__(self):
        return f"{self.aluno.nome} - {self.disciplina.nome} ({self.bimestre}ºB)"


class DiagnosticoTurma(models.Model):
    """Mapeia a VIEW virtual analítica do SQLite diretamente para o ORM do Django"""

    disciplina = models.CharField(max_length=255)
    media_turma_1b = models.FloatField()
    media_turma_2b = models.FloatField()
    total_faltas_acumuladas = models.IntegerField()

    class Meta:
        managed = (
            False  # Impede o Django de tentar criar ou destruir essa tabela fisicamente
        )
        db_table = "view_diagnostico_turma"
        verbose_name = "Diagnóstico da Turma"
        verbose_name_plural = "Diagnósticos da Turma"

    def __str__(self):
        return self.disciplina


class SarespResultado(models.Model):
    """Armazena as métricas de proficiência externa obtidas do arquivo Excel do SARESP"""

    componente_tecnico = models.CharField(
        "Componente Técnico", max_length=150, unique=True
    )
    media_estado = models.FloatField("Média do Estado")
    percentual_proficiencia_avancado = models.FloatField(
        " % Avançado (Estado)", default=0.0
    )

    class Meta:
        verbose_name = "Resultado SARESP"
        verbose_name_plural = "Resultados SARESP"

    def __str__(self):
        return f"SARESP - {self.componente_tecnico}"


class IntervencaoPedagogica(models.Model):
    """Registra as ações tomadas pelo corpo docente para reverter cenários críticos"""

    STATUS_CHOICES = [
        ("PENDENTE", "Planejada / Pendente"),
        ("EM_ANDAMENTO", "Em Execução"),
        ("CONCLUIDA", "Concluída com Sucesso"),
        ("INEFICAZ", "Executada sem Evolução"),
    ]

    aluno = models.ForeignKey(
        Aluno, on_delete=models.CASCADE, related_name="intervencoes"
    )
    disciplina = models.ForeignKey(
        Disciplina, on_delete=models.CASCADE, related_name="intervencoes"
    )
    descricao_acao = models.TextField(
        "Descrição da Intervenção (Ex: Recuperação Paralela, Mudança de Assento)"
    )
    data_inicio = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDENTE")
    observacoes_retorno = models.TextField(
        "Feedback / Evolução do Estudante", blank=True, null=True
    )

    class Meta:
        verbose_name = "Intervenção Pedagógica"
        verbose_name_plural = "Intervenções Pedagógicas"
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Intervenção: {self.aluno.nome} - {self.disciplina.nome} ({self.get_status_display()})"


class MetricaDesempenho(models.Model):
    """Armazena as métricas consolidadas por componente curricular para o Gráfico Radar"""

    aluno = models.ForeignKey(
        Aluno, on_delete=models.CASCADE, related_name="metricas_desempenho"
    )
    disciplina = models.ForeignKey(
        Disciplina, on_delete=models.CASCADE, related_name="metricas_desempenho"
    )
    nota = models.DecimalField("Nota Consolidada", max_digits=5, decimal_places=2)
    frequencia_porcentagem = models.DecimalField(
        "Frequência (%)", max_digits=5, decimal_places=2, null=True, blank=True
    )
    data_avaliacao = models.DateField("Data da Avaliação", null=True, blank=True)

    class Meta:
        verbose_name = "Métrica de Desempenho"
        verbose_name_plural = "Métricas de Desempenho"
        constraints = [
            models.UniqueConstraint(
                fields=["aluno", "disciplina"],
                name="unique_metricas_aluno_disciplina",
            )
        ]
        indexes = [
            # Otimiza o filtro .filter(disciplina__iexact=...) do gráfico radar
            models.Index(fields=["disciplina"]),
        ]

    def __str__(self):
        return f"{self.aluno.nome} - {self.disciplina.nome}: {self.nota}"
