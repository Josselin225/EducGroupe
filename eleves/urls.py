from django.urls import path
from . import views

app_name = 'eleves'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('eleves/', views.index, name='index'),
    path('eleves/ajouter/', views.eleve_ajouter, name='eleve_ajouter'),
    path('eleves/<int:pk>/modifier/', views.eleve_modifier, name='eleve_modifier'),
    path('eleves/<int:pk>/supprimer/', views.eleve_supprimer, name='eleve_supprimer'),
    path('eleves/<int:pk>/inscription/', views.fiche_inscription, name='fiche_inscription'),
    path('eleves/<int:pk>/inscription/pdf/', views.fiche_inscription_pdf, name='fiche_inscription_pdf'),
    path('eleves/<int:pk>/carte/', views.carte_scolaire, name='carte_scolaire'),
    path('eleves/<int:pk>/dossier/', views.eleve_dossier, name='eleve_dossier'),
    path('eleves/cartes/', views.cartes_scolaires_classe, name='cartes_scolaires_classe'),
    path('parametres/', views.parametres, name='parametres'),
    path('annees/', views.annees_liste, name='annees_liste'),
    path('annees/ajouter/', views.annee_ajouter, name='annee_ajouter'),
    path('annees/<int:pk>/modifier/', views.annee_modifier, name='annee_modifier'),
    path('annees/<int:pk>/activer/', views.annee_activer, name='annee_activer'),
    path('annees/promotion/', views.promotion, name='promotion'),
    path('ecoles/', views.ecoles_liste, name='ecoles_liste'),
    path('ecoles/ajouter/', views.ecole_ajouter, name='ecole_ajouter'),
    path('ecoles/<int:pk>/modifier/', views.ecole_modifier, name='ecole_modifier'),
    path('ecoles/<int:pk>/supprimer/', views.ecole_supprimer, name='ecole_supprimer'),
    path('classes/', views.classes_liste, name='classes_liste'),
    path('classes/ajouter/', views.classe_ajouter, name='classe_ajouter'),
    path('classes/<int:pk>/modifier/', views.classe_modifier, name='classe_modifier'),
    path('classes/<int:pk>/supprimer/', views.classe_supprimer, name='classe_supprimer'),
]
