from django.db import models
from eleves.models import Eleve, AnneeScolaire
from django.contrib.auth.models import User

TYPE_FRAIS = [
    ('inscription', 'Inscription'), ('scolarite', 'Scolarité'),
    ('cantine', 'Cantine'), ('transport', 'Transport'),
    ('uniforme', 'Uniforme'), ('autre', 'Autre'),
]
STATUT_PAIEMENT = [
    ('en_attente', 'En attente'), ('partiel', 'Partiel'),
    ('paye', 'Payé'), ('annule', 'Annulé'),
]
MODE_PAIEMENT = [
    ('especes', 'Espèces'), ('cheque', 'Chèque'),
    ('virement', 'Virement'), ('mobile_money', 'Mobile Money'),
]

class TypeFrais(models.Model):
    nom = models.CharField(max_length=100)
    type_frais = models.CharField(max_length=20, choices=TYPE_FRAIS)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='types_frais')
    description = models.TextField(blank=True)
    obligatoire = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} - {self.montant} FCFA"

    class Meta:
        verbose_name = "Type de frais"
        verbose_name_plural = "Types de frais"


class Facture(models.Model):
    numero = models.CharField(max_length=30, unique=True)
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='factures')
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='factures')
    type_frais = models.ForeignKey(TypeFrais, on_delete=models.CASCADE, related_name='factures')
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT, default='en_attente', db_index=True)
    date_echeance = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    observations = models.TextField(blank=True)

    def solde_restant(self):
        return self.montant_total - self.montant_paye

    def __str__(self):
        return f"Facture {self.numero} - {self.eleve}"

    class Meta:
        verbose_name = "Facture"
        ordering = ['-date_creation']
        unique_together = ('eleve', 'type_frais', 'annee_scolaire')


class Paiement(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT)
    reference = models.CharField(max_length=100, blank=True)
    recu_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='paiements_recus')
    recu_numero = models.CharField(max_length=30, blank=True)
    observations = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.db.models import Sum as DSum
        facture = self.facture
        total_paye = facture.paiements.aggregate(t=DSum('montant'))['t'] or 0
        facture.montant_paye = total_paye
        if total_paye >= facture.montant_total:
            facture.statut = 'paye'
        elif total_paye > 0:
            facture.statut = 'partiel'
        else:
            facture.statut = 'en_attente'
        facture.save(update_fields=['montant_paye', 'statut'])

    def __str__(self):
        return f"Paiement {self.montant} - {self.facture}"

    class Meta:
        verbose_name = "Paiement"
        ordering = ['-date_paiement']


class EcheancePaiement(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='echeances')
    numero = models.PositiveSmallIntegerField()
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_echeance = models.DateField()
    paiement = models.OneToOneField(Paiement, on_delete=models.SET_NULL, null=True, blank=True, related_name='echeance')

    @property
    def est_paye(self):
        return self.paiement is not None

    def __str__(self):
        return f"Tranche {self.numero} — {self.facture.numero}"

    class Meta:
        verbose_name = "Échéance"
        ordering = ['numero']
        unique_together = ('facture', 'numero')
