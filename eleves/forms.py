from django import forms
from .models import Ecole, Classe, Eleve, AnneeScolaire, Niveau, GroupeScolaire
from .validators import valider_image


class GroupeScolaireForm(forms.ModelForm):
    class Meta:
        model = GroupeScolaire
        fields = ['nom', 'sigle', 'devise', 'adresse', 'ville', 'pays', 'bp', 'telephone', 'email', 'site_web', 'logo']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: GS-LUMIERE'}),
            'devise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Slogan du groupe'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'bp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BP 0000'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['libelle', 'date_debut', 'date_fin']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2025-2026'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'libelle': 'Libellé',
            'date_debut': 'Date de début',
            'date_fin': 'Date de fin',
        }

    def clean(self):
        cleaned = super().clean()
        debut = cleaned.get('date_debut')
        fin = cleaned.get('date_fin')
        if debut and fin and fin <= debut:
            raise forms.ValidationError('La date de fin doit être postérieure à la date de début.')
        return cleaned


class EcoleForm(forms.ModelForm):
    class Meta:
        model = Ecole
        fields = ['nom', 'type_ecole', 'directeur', 'telephone', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'école'}),
            'type_ecole': forms.Select(attrs={'class': 'form-select'}),
            'directeur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du directeur'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: +225 07 00 00 00 00'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse complète'}),
        }


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'ecole', 'niveau', 'annee_scolaire', 'capacite_max', 'enseignant_principal']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CP1-A'}),
            'ecole': forms.Select(attrs={'class': 'form-select'}),
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
            'capacite_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'enseignant_principal': forms.Select(attrs={'class': 'form-select'}),
        }


class EleveForm(forms.ModelForm):
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'size') and photo != self.instance.photo:
            valider_image(photo)
        return photo

    class Meta:
        model = Eleve
        fields = [
            'matricule', 'nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance',
            'classe', 'nom_parent', 'telephone_parent', 'email_parent',
            'adresse', 'photo', 'statut', 'observations'
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'nom_parent': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_parent': forms.TextInput(attrs={'class': 'form-control'}),
            'email_parent': forms.EmailInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
