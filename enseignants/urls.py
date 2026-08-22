from django.urls import path
from . import views

app_name = 'enseignants'
urlpatterns = [
    path('', views.index, name='index'),
    path('ajouter/', views.enseignant_ajouter, name='ajouter'),
    path('<int:pk>/', views.enseignant_detail, name='detail'),
    path('<int:pk>/modifier/', views.enseignant_modifier, name='modifier'),
    path('<int:pk>/statut/', views.enseignant_desactiver, name='statut'),
    path('<int:pk>/carte/', views.carte_professionnelle, name='carte'),
    path('<int:pk>/compte/', views.gerer_compte, name='gerer_compte'),
    path('comptes/initialiser/', views.initialiser_comptes, name='initialiser_comptes'),
    path('matieres/', views.matieres_liste, name='matieres_liste'),
    path('matieres/ajouter/', views.matiere_ajouter, name='matiere_ajouter'),
    path('matieres/<int:pk>/modifier/', views.matiere_modifier, name='matiere_modifier'),
]
