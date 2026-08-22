from django.urls import path
from . import views

app_name = 'emploi_du_temps'
urlpatterns = [
    path('', views.index, name='index'),
    path('cours/ajouter/', views.cours_ajouter, name='cours_ajouter'),
    path('cours/<int:pk>/modifier/', views.cours_modifier, name='cours_modifier'),
    path('cours/<int:pk>/supprimer/', views.cours_supprimer, name='cours_supprimer'),
    path('creneaux/', views.creneaux_liste, name='creneaux'),
]
