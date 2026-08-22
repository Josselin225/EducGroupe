from django import forms
from .models import Evaluation, Note
from eleves.models import Classe, AnneeScolaire
from enseignants.models import Matiere, Enseignant


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['intitule', 'type_evaluation', 'matiere', 'classe', 'enseignant',
                  'periode', 'date', 'note_max', 'coefficient', 'annee_scolaire']
        widgets = {
            'intitule': forms.TextInput(attrs={'class': 'form-control'}),
            'type_evaluation': forms.Select(attrs={'class': 'form-select'}),
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'periode': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'note_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['valeur', 'absent', 'observation']
        widgets = {
            'valeur': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.25', 'min': '0'}),
            'absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observation': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }
