"""
Script de données d'exemple.
Usage: python manage.py shell < seed_data.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'groupe_scolaire.settings')
django.setup()

from eleves.models import AnneeScolaire, Niveau, Classe, Eleve
from enseignants.models import Matiere, Enseignant
from datetime import date

# Année scolaire
annee, _ = AnneeScolaire.objects.get_or_create(
    libelle='2024-2025',
    defaults={'date_debut': date(2024, 9, 1), 'date_fin': date(2025, 6, 30), 'en_cours': True}
)
print(f"Année: {annee}")

# Niveaux
niveaux_data = [('CP', 1), ('CE1', 2), ('CE2', 3), ('CM1', 4), ('CM2', 5), ('6ème', 6), ('5ème', 7), ('4ème', 8), ('3ème', 9)]
niveaux = {}
for nom, ordre in niveaux_data:
    n, _ = Niveau.objects.get_or_create(nom=nom, defaults={'ordre': ordre})
    niveaux[nom] = n
print(f"Niveaux: {len(niveaux)}")

# Classes
classes_data = [('CP A', 'CP'), ('CE1 A', 'CE1'), ('CM2 A', 'CM2'), ('6ème A', '6ème'), ('3ème A', '3ème')]
classes = {}
for nom, niveau_nom in classes_data:
    c, _ = Classe.objects.get_or_create(nom=nom, annee_scolaire=annee, defaults={'niveau': niveaux[niveau_nom]})
    classes[nom] = c
print(f"Classes: {len(classes)}")

# Matières
matieres_data = [
    ('Mathématiques', 'MATH', 4), ('Français', 'FR', 4), ('Sciences', 'SCI', 2),
    ('Histoire-Géo', 'HG', 2), ('Anglais', 'ANG', 2), ('EPS', 'EPS', 1),
    ('Arts Plastiques', 'ART', 1), ('Informatique', 'INFO', 2),
]
for nom, code, coef in matieres_data:
    Matiere.objects.get_or_create(code=code, defaults={'nom': nom, 'coefficient': coef})
print("Matières créées")

# Élèves exemples
eleves_data = [
    ('E2024001', 'KOUASSI', 'Jean-Baptiste', 'M', date(2015, 3, 12), 'CP A', 'KOUASSI Paul', '0701234567'),
    ('E2024002', 'BAMBA', 'Fatou', 'F', date(2014, 7, 22), 'CE1 A', 'BAMBA Ibrahim', '0712345678'),
    ('E2024003', 'TRAORÉ', 'Moussa', 'M', date(2012, 1, 5), 'CM2 A', 'TRAORÉ Aminata', '0723456789'),
    ('E2024004', 'KONÉ', 'Mariam', 'F', date(2011, 9, 18), '6ème A', 'KONÉ Abdoulaye', '0734567890'),
    ('E2024005', 'DIALLO', 'Oumar', 'M', date(2008, 5, 30), '3ème A', 'DIALLO Kadiatou', '0745678901'),
]
for mat, nom, prenom, sexe, naissance, classe_nom, parent, tel in eleves_data:
    Eleve.objects.get_or_create(matricule=mat, defaults={
        'nom': nom, 'prenom': prenom, 'sexe': sexe,
        'date_naissance': naissance, 'classe': classes.get(classe_nom),
        'nom_parent': parent, 'telephone_parent': tel,
    })
print(f"Élèves: {Eleve.objects.count()}")
print("\n✅ Données d'exemple créées avec succès!")
print("   Connectez-vous avec: admin / admin123")
