from django import forms
from .models import TypeFrais, Facture, Paiement, EcheancePaiement
from eleves.models import AnneeScolaire


class TypeFraisForm(forms.ModelForm):
    class Meta:
        model = TypeFrais
        fields = ['nom', 'type_frais', 'montant', 'annee_scolaire', 'obligatoire', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_frais': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '100'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
            'obligatoire': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ['numero', 'eleve', 'annee_scolaire', 'type_frais', 'montant_total', 'date_echeance', 'observations']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'eleve': forms.Select(attrs={'class': 'form-select'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
            'type_frais': forms.Select(attrs={'class': 'form-select'}),
            'montant_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '100'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['montant', 'date_paiement', 'mode_paiement', 'reference', 'recu_numero', 'observations']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '100'}),
            'date_paiement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° chèque, référence...'}),
            'recu_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EcheanceForm(forms.ModelForm):
    class Meta:
        model = EcheancePaiement
        fields = ['montant', 'date_echeance']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '100'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class GenererEcheancierForm(forms.Form):
    nb_tranches = forms.IntegerField(
        min_value=2, max_value=12, initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Nombre de tranches"
    )
    date_premiere_tranche = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date de la 1ère tranche"
    )
