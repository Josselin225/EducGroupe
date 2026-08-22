from django.db import models
from eleves.models import Classe, AnneeScolaire
from enseignants.models import Enseignant, Matiere

JOURS = [
    (1, 'Lundi'), (2, 'Mardi'), (3, 'Mercredi'),
    (4, 'Jeudi'), (5, 'Vendredi'), (6, 'Samedi'),
]

class Salle(models.Model):
    nom = models.CharField(max_length=50)
    capacite = models.PositiveSmallIntegerField(default=40)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Salle"


class CreneauHoraire(models.Model):
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    libelle = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.libelle or f"{self.heure_debut:%H:%M} - {self.heure_fin:%H:%M}"

    class Meta:
        verbose_name = "Créneau horaire"
        verbose_name_plural = "Créneaux horaires"
        ordering = ['heure_debut']



class Cours(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='cours')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='cours')
    enseignant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, related_name='cours')
    salle = models.ForeignKey(Salle, on_delete=models.SET_NULL, null=True, blank=True, related_name='cours')
    jour = models.PositiveSmallIntegerField(choices=JOURS)
    creneau = models.ForeignKey(CreneauHoraire, on_delete=models.CASCADE, related_name='cours')

    def __str__(self):
        return f"{self.matiere} - {self.classe} ({self.get_jour_display()})"

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['jour', 'creneau__heure_debut']
        unique_together = ('classe', 'jour', 'creneau')
