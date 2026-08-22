# EduGroupe — Système de Gestion Scolaire Django

## 🚀 Démarrage rapide

```bash
# Installer les dépendances
pip install django pillow

# Appliquer les migrations
python manage.py migrate

# Créer un super-utilisateur
python manage.py createsuperuser

# Charger les données d'exemple (optionnel)
python seed_data.py

# Lancer le serveur
python manage.py runserver
```

Accès : http://127.0.0.1:8000  
Admin : http://127.0.0.1:8000/admin  
Compte par défaut : **admin / admin123**

---

## 📁 Structure du projet

```
groupe_scolaire/
├── eleves/          # Gestion élèves, classes, années scolaires
├── enseignants/     # Enseignants et matières
├── emploi_du_temps/ # Cours, salles, créneaux horaires
├── notes/           # Évaluations, notes, bulletins
├── presences/       # Présences, feuilles d'appel
├── paiements/       # Frais scolaires, factures, paiements
└── templates/       # Templates HTML (Bootstrap 5)
```

## 📊 Modèles de données

### 🎓 Élèves (`eleves`)
- **AnneeScolaire** — Année scolaire (une seule active à la fois)
- **Niveau** — Niveau scolaire (CP, CE1, 6ème…)
- **Classe** — Classe par année scolaire
- **Eleve** — Fiche élève complète (matricule, photo, contacts parent)

### 👨‍🏫 Enseignants (`enseignants`)
- **Matiere** — Matière avec coefficient
- **Enseignant** — Fiche enseignant (compte utilisateur optionnel)

### 📅 Emploi du temps (`emploi_du_temps`)
- **Salle** — Salle de classe
- **CreneauHoraire** — Plages horaires
- **Cours** — Affectation enseignant/matière/classe/salle/jour

### ⭐ Notes (`notes`)
- **Evaluation** — Devoir, composition, examen (par trimestre)
- **Note** — Note d'un élève à une évaluation
- **Bulletin** — Bulletin périodique avec moyenne et rang

### ✅ Présences (`presences`)
- **FeuilleDAppel** — Appel par cours et date
- **Presence** — Statut présence/absence/retard par élève

### 💰 Paiements (`paiements`)
- **TypeFrais** — Types de frais par année (inscription, scolarité…)
- **Facture** — Facture d'un élève (suivi automatique du solde)
- **Paiement** — Versement avec mise à jour automatique de la facture

## 🔐 Authentification
- Connexion via `/auth/login/`
- Toutes les vues protégées par `@login_required`
- Interface admin complète sur `/admin/`

## ⚙️ Configuration
Fichier : `groupe_scolaire/settings.py`
- Base de données : SQLite (dev) → PostgreSQL recommandé en production
- Fuseau horaire : `Africa/Abidjan`
- Langue : Français (`fr-fr`)
