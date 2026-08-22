from django.contrib import admin
from .models import Evaluation, Note, Bulletin

class NoteInline(admin.TabularInline):
    model = Note
    extra = 0

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['intitule', 'type_evaluation', 'matiere', 'classe', 'periode', 'date']
    list_filter = ['type_evaluation', 'periode', 'annee_scolaire', 'classe']
    inlines = [NoteInline]

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'evaluation', 'valeur', 'absent']
    list_filter = ['evaluation__periode', 'absent']
    search_fields = ['eleve__nom', 'eleve__prenom']

@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'periode', 'annee_scolaire', 'moyenne_generale', 'rang']
    list_filter = ['periode', 'annee_scolaire']
