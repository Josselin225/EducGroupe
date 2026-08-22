from django.contrib import admin
from .models import Presence, FeuilleDAppel

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'date', 'cours', 'statut']
    list_filter = ['statut', 'date']
    search_fields = ['eleve__nom', 'eleve__prenom']
    date_hierarchy = 'date'

@admin.register(FeuilleDAppel)
class FeuilleDAppelAdmin(admin.ModelAdmin):
    list_display = ['cours', 'date', 'fait']
    list_filter = ['fait', 'date']
