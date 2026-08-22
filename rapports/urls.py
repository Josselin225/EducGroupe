from django.urls import path
from . import views

app_name = 'rapports'
urlpatterns = [
    path('', views.index, name='index'),
    path('connexions/', views.connexions, name='connexions'),
    path('connexions/purger/', views.purger_journal, name='purger_journal'),
    path('connexions/supprimer/', views.supprimer_journal_selection, name='supprimer_journal_selection'),
    path('sauvegardes/', views.sauvegardes, name='sauvegardes'),
    path('sauvegardes/<str:nom>/telecharger/', views.telecharger_backup, name='telecharger_backup'),
]
