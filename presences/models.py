from django.db import models
from eleves.models import Eleve, Classe
from emploi_du_temps.models import Cours

STATUT_PRESENCE = [
    ('present', 'Présent'), ('absent', 'Absent'),
    ('retard', 'En retard'), ('excuse', 'Absent excusé'),
]

class Presence(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='presences')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='presences', null=True, blank=True)
    date = models.DateField(db_index=True)
    statut = models.CharField(max_length=20, choices=STATUT_PRESENCE, default='present', db_index=True)
    motif = models.CharField(max_length=200, blank=True)
    justificatif = models.FileField(upload_to='presences/justificatifs/', blank=True, null=True)

    def __str__(self):
        return f"{self.eleve} - {self.date} ({self.get_statut_display()})"

    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        unique_together = ('eleve', 'cours', 'date')
        ordering = ['-date']


class FeuilleDAppel(models.Model):
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='feuilles_appel', null=True, blank=True)
    date = models.DateField()
    fait = models.BooleanField(default=False)
    observations = models.TextField(blank=True)
    date_saisie = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appel {self.cours} - {self.date}"

    class Meta:
        verbose_name = "Feuille d'appel"
        verbose_name_plural = "Feuilles d'appel"
        unique_together = ('cours', 'date')
        ordering = ['-date']
