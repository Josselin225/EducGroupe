from django.db import models
from eleves.models import Eleve, Classe, AnneeScolaire
from enseignants.models import Matiere, Enseignant

TYPE_EVALUATION = [
    ('devoir', 'Devoir'), ('composition', 'Composition'),
    ('interrogation', 'Interrogation'), ('examen', 'Examen'),
]
PERIODE = [
    ('T1', 'Trimestre 1'), ('T2', 'Trimestre 2'), ('T3', 'Trimestre 3'),
    ('S1', 'Semestre 1'), ('S2', 'Semestre 2'),
]

class Evaluation(models.Model):
    intitule = models.CharField(max_length=200)
    type_evaluation = models.CharField(max_length=20, choices=TYPE_EVALUATION)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='evaluations')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='evaluations')
    enseignant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, related_name='evaluations')
    periode = models.CharField(max_length=5, choices=PERIODE, db_index=True)
    date = models.DateField()
    note_max = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    coefficient = models.PositiveSmallIntegerField(default=1)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='evaluations')

    def __str__(self):
        return f"{self.intitule} - {self.matiere} ({self.classe})"

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['classe', 'periode', 'annee_scolaire'], name='eval_classe_periode_idx'),
        ]


class Note(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='notes')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='notes')
    valeur = models.DecimalField(max_digits=5, decimal_places=2)
    absent = models.BooleanField(default=False)
    observation = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.eleve} - {self.evaluation}: {self.valeur}"

    class Meta:
        verbose_name = "Note"
        unique_together = ('eleve', 'evaluation')
        ordering = ['eleve__nom']


class Bulletin(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='bulletins')
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='bulletins')
    periode = models.CharField(max_length=5, choices=PERIODE)
    moyenne_generale = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rang = models.PositiveSmallIntegerField(null=True, blank=True)
    appreciation = models.TextField(blank=True)
    date_generation = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bulletin {self.eleve} - {self.periode} {self.annee_scolaire}"

    class Meta:
        verbose_name = "Bulletin"
        unique_together = ('eleve', 'annee_scolaire', 'periode')
        ordering = ['-annee_scolaire__date_debut', 'periode']
