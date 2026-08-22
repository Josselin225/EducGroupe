from django import forms
from .models import Cours, CreneauHoraire, Salle
from eleves.models import Classe
from enseignants.models import Matiere, Enseignant


class CreneauForm(forms.ModelForm):
    class Meta:
        model = CreneauHoraire
        fields = ['heure_debut', 'heure_fin', 'libelle']
        widgets = {
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Matin 1'}),
        }


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ['classe', 'matiere', 'enseignant', 'salle', 'jour', 'creneau']
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'salle': forms.Select(attrs={'class': 'form-select'}),
            'jour': forms.Select(attrs={'class': 'form-select'}),
            'creneau': forms.Select(attrs={'class': 'form-select'}),
        }
