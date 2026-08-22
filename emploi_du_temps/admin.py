from django.contrib import admin
from .models import Salle, CreneauHoraire, Cours

admin.site.register(Salle)
admin.site.register(CreneauHoraire)

@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ['matiere', 'classe', 'enseignant', 'jour', 'creneau', 'salle']
    list_filter = ['jour', 'classe__annee_scolaire', 'classe', 'matiere']
