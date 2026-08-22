from django.urls import path
from . import views

app_name = 'notes'
urlpatterns = [
    path('', views.index, name='index'),
    path('evaluations/', views.evaluations_liste, name='evaluations_liste'),
    path('evaluations/ajouter/', views.evaluation_ajouter, name='evaluation_ajouter'),
    path('evaluations/<int:pk>/modifier/', views.evaluation_modifier, name='evaluation_modifier'),
    path('evaluations/<int:pk>/supprimer/', views.evaluation_supprimer, name='evaluation_supprimer'),
    path('evaluations/<int:pk>/notes/', views.saisie_notes, name='saisie_notes'),
    path('bulletins/', views.bulletins_liste, name='bulletins_liste'),
    path('bulletins/<int:eleve_id>/<str:periode>/', views.bulletin_detail, name='bulletin_detail'),
    path('bulletins/<int:eleve_id>/<str:periode>/pdf/', views.bulletin_pdf, name='bulletin_pdf'),
    path('bulletins/imprimer/<int:classe_id>/<str:periode>/', views.bulletins_imprimer_classe, name='bulletins_imprimer_classe'),
]
