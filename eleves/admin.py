from django.contrib import admin
from .models import AnneeScolaire, Ecole, Niveau, Classe, Eleve


@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'date_debut', 'date_fin', 'en_cours']
    list_editable = ['en_cours']


@admin.register(Ecole)
class EcoleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_ecole', 'directeur', 'telephone', 'nb_classes', 'nb_eleves']
    list_filter = ['type_ecole']
    search_fields = ['nom', 'directeur']


@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'cycle', 'ordre']
    list_filter = ['cycle']
    ordering = ['ordre']


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ecole', 'niveau', 'annee_scolaire', 'effectif', 'capacite_max']
    list_filter = ['ecole', 'annee_scolaire', 'niveau__cycle', 'niveau']
    search_fields = ['nom']


@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom', 'prenom', 'sexe', 'classe', 'statut']
    list_filter = ['statut', 'sexe', 'classe__ecole', 'classe__annee_scolaire', 'classe']
    search_fields = ['matricule', 'nom', 'prenom']
    list_per_page = 30
