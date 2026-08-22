from django.urls import path
from . import views

app_name = 'presences'
urlpatterns = [
    path('', views.index, name='index'),
    path('appel/', views.appel_selection, name='appel_selection'),
    path('appel/<int:classe_id>/<str:date_str>/', views.appel, name='appel'),
    path('suivi/', views.suivi, name='suivi'),
    path('suivi/eleve/<int:eleve_id>/', views.historique_eleve, name='historique_eleve'),
    path('statistiques/', views.statistiques, name='statistiques'),
]
