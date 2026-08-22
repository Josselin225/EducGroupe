from django.contrib import admin
from .models import Matiere, Enseignant

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'coefficient']
    search_fields = ['nom', 'code']

@admin.register(Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom', 'prenom', 'specialite', 'statut']
    list_filter = ['statut', 'sexe']
    search_fields = ['matricule', 'nom', 'prenom']
    filter_horizontal = ['matieres']
