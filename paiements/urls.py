from django.urls import path
from . import views

app_name = 'paiements'
urlpatterns = [
    path('', views.index, name='index'),
    path('types-frais/', views.types_frais_liste, name='types_frais_liste'),
    path('types-frais/ajouter/', views.type_frais_ajouter, name='type_frais_ajouter'),
    path('types-frais/<int:pk>/modifier/', views.type_frais_modifier, name='type_frais_modifier'),
    path('factures/', views.factures_liste, name='factures_liste'),
    path('factures/ajouter/', views.facture_ajouter, name='facture_ajouter'),
    path('factures/<int:pk>/', views.facture_detail, name='facture_detail'),
    path('factures/<int:pk>/pdf/', views.facture_pdf, name='facture_pdf'),
    path('factures/<int:pk>/echeancier/pdf/', views.echeancier_pdf, name='echeancier_pdf'),
    path('paiements/<int:pk>/supprimer/', views.paiement_supprimer, name='paiement_supprimer'),
    path('paiements/<int:pk>/recu/', views.recu_paiement, name='recu_paiement'),
    path('factures/<int:facture_pk>/echeancier/', views.echeancier_generer, name='echeancier_generer'),
    path('echeances/<int:pk>/payer/', views.echeance_payer, name='echeance_payer'),
]
