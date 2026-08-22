from django.contrib import admin
from .models import TypeFrais, Facture, Paiement

class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0
    readonly_fields = ['recu_par']

@admin.register(TypeFrais)
class TypeFraisAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_frais', 'montant', 'annee_scolaire', 'obligatoire']
    list_filter = ['type_frais', 'annee_scolaire', 'obligatoire']

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero', 'eleve', 'type_frais', 'montant_total', 'montant_paye', 'statut']
    list_filter = ['statut', 'annee_scolaire', 'type_frais']
    search_fields = ['numero', 'eleve__nom', 'eleve__prenom']
    inlines = [PaiementInline]
    readonly_fields = ['montant_paye', 'statut']

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['facture', 'montant', 'date_paiement', 'mode_paiement', 'recu_par']
    list_filter = ['mode_paiement', 'date_paiement']
    date_hierarchy = 'date_paiement'
