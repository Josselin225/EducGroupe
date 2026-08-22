"""
Données de démonstration complètes — EduGroupe
Usage: python manage.py shell < seed_demo.py
"""
import os, django, random
from decimal import Decimal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'groupe_scolaire.settings')
django.setup()

from datetime import date, timedelta
from django.contrib.auth.models import User
from eleves.models import AnneeScolaire, Ecole, Niveau, Classe, Eleve, GroupeScolaire
from enseignants.models import Matiere, Enseignant
from emploi_du_temps.models import Salle, CreneauHoraire, Cours, ClasseMatiere
from notes.models import Evaluation, Note
from presences.models import Presence, FeuilleDAppel
from paiements.models import TypeFrais, Facture, Paiement

# ─── Groupe scolaire ───────────────────────────────────
g = GroupeScolaire.get()
g.nom = "Groupe Scolaire Les Palmiers"
g.sigle = "GSP"
g.ville = "Abidjan"
g.telephone = "+225 07 00 11 22 33"
g.email = "contact@gsp-abidjan.ci"
g.devise = "L'excellence au service de l'avenir"
g.save()
print("Groupe scolaire configuré")

# ─── Année scolaire ────────────────────────────────────
annee, _ = AnneeScolaire.objects.get_or_create(
    libelle='2025-2026',
    defaults={'date_debut': date(2025, 9, 1), 'date_fin': date(2026, 6, 30), 'en_cours': True}
)
annee.en_cours = True
annee.save()
print(f"Année : {annee}")

# ─── Écoles ────────────────────────────────────────────
ecole_p, _ = Ecole.objects.get_or_create(nom="École Primaire Les Palmiers",
    defaults={'adresse': 'Cocody, Abidjan', 'directeur': 'M. KONAN Yao', 'telephone': '07 11 22 33', 'type_ecole': 'primaire'})
ecole_m, _ = Ecole.objects.get_or_create(nom="École Maternelle Les Palmiers",
    defaults={'adresse': 'Cocody, Abidjan', 'directeur': 'Mme YAPI Adjoua', 'telephone': '07 44 55 66', 'type_ecole': 'maternelle'})
print("Écoles créées")

# ─── Niveaux ───────────────────────────────────────────
niveaux_data = [
    ('CP',  'CP',  'primaire', 1), ('CE1', 'CE1', 'primaire', 2),
    ('CE2', 'CE2', 'primaire', 3), ('CM1', 'CM1', 'primaire', 4),
    ('CM2', 'CM2', 'primaire', 5), ('6ème','6EME','primaire', 6),
    ('5ème','5EME','primaire', 7), ('4ème','4EME','primaire', 8),
    ('3ème','3EME','primaire', 9),
]
niveaux = {}
for nom, code, cycle, ordre in niveaux_data:
    n, _ = Niveau.objects.get_or_create(code=code, defaults={'nom': nom, 'cycle': cycle, 'ordre': ordre})
    niveaux[code] = n
print("Niveaux créés")

# ─── Matières ──────────────────────────────────────────
matieres_data = [
    ('Mathématiques', 'MATH', 4), ('Français', 'FR', 4),
    ('Sciences', 'SCI', 2), ('Histoire-Géo', 'HG', 2),
    ('Anglais', 'ANG', 2), ('EPS', 'EPS', 1),
    ('Arts Plastiques', 'ART', 1), ('Informatique', 'INFO', 2),
]
matieres = {}
for nom, code, coef in matieres_data:
    m, _ = Matiere.objects.get_or_create(code=code, defaults={'nom': nom, 'coefficient': coef})
    matieres[code] = m
print("Matières créées")

# ─── Enseignants ───────────────────────────────────────
enseignants_data = [
    ('T001', 'KOUAMÉ', 'Arsène',   'M', 'Mathématiques / Sciences',    ['MATH','SCI']),
    ('T002', 'N\'GUESSAN', 'Clarisse', 'F', 'Français / Histoire-Géo', ['FR','HG']),
    ('T003', 'BAMBA', 'Ibrahima',  'M', 'Anglais / Informatique',       ['ANG','INFO']),
    ('T004', 'KONÉ', 'Aminata',    'F', 'EPS / Arts Plastiques',        ['EPS','ART']),
    ('T005', 'DIALLO', 'Moussa',   'M', 'Mathématiques',                ['MATH']),
    ('T006', 'TRAORÉ', 'Kadiatou', 'F', 'Français',                     ['FR']),
]
enseignants = {}
for mat, nom, prenom, sexe, spec, mat_codes in enseignants_data:
    ens, created = Enseignant.objects.get_or_create(matricule=mat, defaults={
        'nom': nom, 'prenom': prenom, 'sexe': sexe,
        'specialite': spec, 'statut': 'actif',
        'date_embauche': date(2020, 9, 1),
        'telephone': f'07{random.randint(10000000,99999999)}',
    })
    for code in mat_codes:
        ens.matieres.add(matieres[code])
    enseignants[mat] = ens
print("Enseignants créés")

# ─── Classes ───────────────────────────────────────────
classes_cfg = [
    ('CP A',   'CP',   ecole_p, 'T002', 32),
    ('CE1 A',  'CE1',  ecole_p, 'T002', 35),
    ('CE2 A',  'CE2',  ecole_p, 'T001', 33),
    ('CM1 A',  'CM1',  ecole_p, 'T001', 30),
    ('CM2 A',  'CM2',  ecole_p, 'T005', 28),
    ('6ème A', '6EME', ecole_p, 'T003', 40),
]
classes = {}
for nom, niv_code, ecole, ens_mat, cap in classes_cfg:
    c, _ = Classe.objects.get_or_create(nom=nom, ecole=ecole, annee_scolaire=annee, defaults={
        'niveau': niveaux[niv_code], 'capacite_max': cap,
        'enseignant_principal': enseignants[ens_mat],
    })
    classes[nom] = c
print("Classes créées")

# ─── Salles & Créneaux ─────────────────────────────────
salles_noms = ['Salle 1', 'Salle 2', 'Salle 3', 'Salle 4', 'Salle Info', 'Gymnase']
salles = []
for s in salles_noms:
    salle, _ = Salle.objects.get_or_create(nom=s, defaults={'capacite': 40})
    salles.append(salle)

creneaux_data = [
    ('07:30', '09:30', '07h30 - 09h30'),
    ('09:30', '11:30', '09h30 - 11h30'),
    ('12:00', '14:00', '12h00 - 14h00'),
    ('14:00', '16:00', '14h00 - 16h00'),
]
from datetime import time
creneaux = []
for deb, fin, lib in creneaux_data:
    h_deb = time(*map(int, deb.split(':')))
    h_fin = time(*map(int, fin.split(':')))
    cr, _ = CreneauHoraire.objects.get_or_create(heure_debut=h_deb, heure_fin=h_fin, defaults={'libelle': lib})
    creneaux.append(cr)
print("Salles & créneaux créés")

# ─── Élèves ────────────────────────────────────────────
eleves_data = [
    # (matricule, nom, prenom, sexe, naissance, classe, parent, tel)
    ('E2526001','KOUASSI','Jean-Baptiste','M',date(2017,3,12),'CP A','KOUASSI Paul','0701234567'),
    ('E2526002','BAMBA','Fatou','F',date(2017,7,22),'CP A','BAMBA Ibrahim','0712345678'),
    ('E2526003','KONÉ','Aya','F',date(2017,1,5),'CP A','KONÉ Sali','0723456789'),
    ('E2526004','DIALLO','Seydou','M',date(2016,9,18),'CE1 A','DIALLO Kadiatou','0734567890'),
    ('E2526005','OUATTARA','Marie','F',date(2016,5,30),'CE1 A','OUATTARA Drissa','0745678901'),
    ('E2526006','TRAORÉ','Lamine','M',date(2016,11,14),'CE1 A','TRAORÉ Aminata','0756789012'),
    ('E2526007','YAO','Christophe','M',date(2015,4,2),'CE2 A','YAO Kouakou','0767890123'),
    ('E2526008','FOFANA','Mariam','F',date(2015,8,25),'CE2 A','FOFANA Boubakar','0778901234'),
    ('E2526009','SORO','Ernest','M',date(2015,2,17),'CE2 A','SORO Tenin','0789012345'),
    ('E2526010','COULIBALY','Aïcha','F',date(2014,6,9),'CM1 A','COULIBALY Mamadou','0700123456'),
    ('E2526011','KONAN','Patrick','M',date(2014,10,21),'CM1 A','KONAN Yao','0711234567'),
    ('E2526012','SÉKA','Rosalie','F',date(2014,3,30),'CM1 A','SÉKA Kouamé','0722345678'),
    ('E2526013','GBAGBO','Narcisse','M',date(2013,7,15),'CM2 A','GBAGBO Agnès','0733456789'),
    ('E2526014','LOROUGNON','Sophie','F',date(2013,12,3),'CM2 A','LOROUGNON Pierre','0744567890'),
    ('E2526015','AKAFFOU','Hervé','M',date(2013,5,19),'CM2 A','AKAFFOU Clémence','0755678901'),
    ('E2526016','MÉITÉ','Ibrahim','M',date(2012,8,7),'6ème A','MÉITÉ Salimata','0766789012'),
    ('E2526017','KOUYATÉ','Fatoumata','F',date(2012,2,28),'6ème A','KOUYATÉ Lassana','0777890123'),
    ('E2526018','BROU','Gilles','M',date(2012,11,11),'6ème A','BROU Adjoua','0788901234'),
    ('E2526019','ADOU','Carine','F',date(2012,4,4),'6ème A','ADOU Konan','0799012345'),
    ('E2526020','ZADI','Michel','M',date(2012,9,23),'6ème A','ZADI Marie','0700234567'),
]
eleves = {}
for mat, nom, prenom, sexe, naiss, classe_nom, parent, tel in eleves_data:
    e, _ = Eleve.objects.get_or_create(matricule=mat, defaults={
        'nom': nom, 'prenom': prenom, 'sexe': sexe,
        'date_naissance': naiss, 'classe': classes[classe_nom],
        'nom_parent': parent, 'telephone_parent': tel, 'statut': 'actif',
    })
    eleves[mat] = e
print(f"Élèves créés : {Eleve.objects.count()}")

# ─── ClasseMatieres (coefficients par classe) ──────────
mat_par_classe = ['MATH','FR','SCI','HG','ANG','EPS','ART']
ens_map = {'MATH':'T001','FR':'T002','SCI':'T001','HG':'T002','ANG':'T003','EPS':'T004','ART':'T004'}
for classe in classes.values():
    for code in mat_par_classe:
        ClasseMatiere.objects.get_or_create(
            classe=classe, matiere=matieres[code],
            defaults={'enseignant': enseignants[ens_map[code]], 'coefficient': matieres[code].coefficient}
        )
print("ClasseMatieres créées")

# ─── Évaluations & Notes ───────────────────────────────
evals_cfg = [
    ('Devoir 1 T1', 'devoir', 'T1', date(2025, 10, 10)),
    ('Composition T1', 'composition', 'T1', date(2025, 11, 28)),
    ('Devoir 1 T2', 'devoir', 'T2', date(2026, 1, 20)),
    ('Composition T2', 'composition', 'T2', date(2026, 3, 13)),
]
matieres_eval = ['MATH', 'FR', 'SCI', 'HG', 'ANG']

random.seed(42)
for classe_nom, classe in classes.items():
    eleves_classe = [e for e in eleves.values() if e.classe == classe]
    for intitule, type_ev, periode, date_ev in evals_cfg:
        for m_code in matieres_eval[:3]:
            ev, _ = Evaluation.objects.get_or_create(
                intitule=intitule, matiere=matieres[m_code], classe=classe,
                defaults={
                    'type_evaluation': type_ev, 'periode': periode,
                    'date': date_ev, 'note_max': Decimal('20'),
                    'coefficient': matieres[m_code].coefficient,
                    'enseignant': enseignants[ens_map[m_code]],
                    'annee_scolaire': annee,
                }
            )
            for eleve in eleves_classe:
                Note.objects.get_or_create(eleve=eleve, evaluation=ev, defaults={
                    'valeur': Decimal(str(round(random.uniform(8, 19), 2))),
                    'absent': False,
                })
print(f"Évaluations: {Evaluation.objects.count()}, Notes: {Note.objects.count()}")

# ─── Présences (les 20 derniers jours ouvrés) ──────────
today = date(2026, 6, 16)
jours_ouvres = []
d = today - timedelta(days=1)
while len(jours_ouvres) < 20:
    if d.weekday() < 5:
        jours_ouvres.append(d)
    d -= timedelta(days=1)

for jour in jours_ouvres:
    for classe in classes.values():
        eleves_classe = [e for e in eleves.values() if e.classe == classe]
        for eleve in eleves_classe:
            if random.random() < 0.08:
                statut = random.choice(['absent', 'retard', 'excuse'])
            else:
                statut = 'present'
            Presence.objects.get_or_create(
                eleve=eleve, cours=None, date=jour,
                defaults={'statut': statut, 'motif': 'Maladie' if statut == 'excuse' else ''}
            )
print(f"Présences enregistrées : {Presence.objects.count()}")

# ─── Paiements ─────────────────────────────────────────
frais_data = [
    ('Inscription 2025-2026', 'inscription', Decimal('25000')),
    ('Scolarité T1 2025-2026', 'scolarite',  Decimal('60000')),
    ('Scolarité T2 2025-2026', 'scolarite',  Decimal('60000')),
    ('Scolarité T3 2025-2026', 'scolarite',  Decimal('60000')),
]
types_frais = []
for nom, type_f, montant in frais_data:
    tf, _ = TypeFrais.objects.get_or_create(nom=nom, annee_scolaire=annee,
        defaults={'type_frais': type_f, 'montant': montant, 'obligatoire': True})
    types_frais.append(tf)

admin_user = User.objects.filter(is_superuser=True).first()
compteur = Facture.objects.count()
for i, eleve in enumerate(eleves.values()):
    for j, tf in enumerate(types_frais):
        compteur += 1
        num = f"F2526-{compteur:04d}"
        facture, created = Facture.objects.get_or_create(
            eleve=eleve, type_frais=tf, annee_scolaire=annee,
            defaults={
                'numero': num,
                'montant_total': tf.montant,
                'montant_paye': Decimal('0'),
                'statut': 'en_attente',
                'date_echeance': date(2026, 6, 30),
            }
        )
        if not created:
            continue
        # Paiement selon le type
        if j == 0:  # inscription : tous payé
            Paiement.objects.create(
                facture=facture, montant=tf.montant,
                date_paiement=date(2025, 9, 5),
                mode_paiement='especes', recu_par=admin_user
            )
        elif j == 1:  # T1 : tous payé
            Paiement.objects.create(
                facture=facture, montant=tf.montant,
                date_paiement=date(2025, 10, 3),
                mode_paiement=random.choice(['especes', 'mobile_money']),
                recu_par=admin_user
            )
        elif j == 2:  # T2 : 70% payé, 30% partiel
            if random.random() < 0.7:
                Paiement.objects.create(
                    facture=facture, montant=tf.montant,
                    date_paiement=date(2026, 1, 10),
                    mode_paiement=random.choice(['especes', 'mobile_money', 'virement']),
                    recu_par=admin_user
                )
            else:
                Paiement.objects.create(
                    facture=facture, montant=Decimal('30000'),
                    date_paiement=date(2026, 1, 15),
                    mode_paiement='especes', recu_par=admin_user
                )
        # T3 : laissé en attente pour certains

print(f"Factures: {Facture.objects.count()}, Paiements: {Paiement.objects.count()}")

print("\n✅ Données de démonstration chargées avec succès !")
print(f"   Élèves      : {Eleve.objects.count()}")
print(f"   Classes     : {Classe.objects.count()}")
print(f"   Enseignants : {Enseignant.objects.count()}")
print(f"   Évaluations : {Evaluation.objects.count()}")
print(f"   Notes       : {Note.objects.count()}")
print(f"   Présences   : {Presence.objects.count()}")
print(f"   Factures    : {Facture.objects.count()}")
print(f"   Paiements   : {Paiement.objects.count()}")
print("\n   Connexion : admin / admin123")
print("   URL       : http://127.0.0.1:8000/")
