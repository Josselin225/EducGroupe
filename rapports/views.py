import zipfile
import pyzipper
import shutil
import logging
from pathlib import Path
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings
from django.db.models import Count, Sum, Q

from eleves.models import Eleve, Classe, AnneeScolaire, Ecole, Niveau
from enseignants.models import Enseignant
from presences.models import Presence
from paiements.models import Facture
from eleves.permissions import acces_requis

audit_log = logging.getLogger('edugroupe.audit')

# ─────────────────────────────────────────────────────
# RAPPORTS & STATISTIQUES
# ─────────────────────────────────────────────────────

@acces_requis("rapports")
def index(request):
    toutes_annees = AnneeScolaire.objects.order_by('-date_debut')
    annee_id = request.GET.get('annee')
    if annee_id:
        annee = toutes_annees.filter(pk=annee_id).first()
    else:
        annee = toutes_annees.filter(en_cours=True).first() or toutes_annees.first()
    if not annee:
        return render(request, 'rapports/index.html',
                      {'annee': None, 'toutes_annees': toutes_annees, 'page_title': 'Rapports & Statistiques', 'active': 'rapports'})

    global_stats = Eleve.objects.filter(classe__annee_scolaire=annee, statut='actif').aggregate(
        nb_eleves=Count('pk'),
        nb_garcons=Count('pk', filter=Q(sexe='M')),
        nb_filles=Count('pk', filter=Q(sexe='F')),
    )

    ecoles_data = (
        Eleve.objects.filter(classe__annee_scolaire=annee, statut='actif')
        .values('classe__ecole__id', 'classe__ecole__nom', 'classe__ecole__type_ecole')
        .annotate(nb_garcons=Count('pk', filter=Q(sexe='M')),
                  nb_filles=Count('pk', filter=Q(sexe='F')),
                  nb_total=Count('pk'))
        .order_by('classe__ecole__nom')
    )
    nb_classes_par_ecole = dict(
        Classe.objects.filter(annee_scolaire=annee)
        .values('ecole_id').annotate(nb=Count('pk')).values_list('ecole_id', 'nb')
    )
    TYPE_MAP = {'maternelle': 'Maternelle', 'primaire': 'Primaire', 'mixte': 'Maternelle + Primaire'}
    ecoles_stats = [
        {'nom': r['classe__ecole__nom'] or 'Sans école',
         'type_ecole': r['classe__ecole__type_ecole'] or '',
         'get_type_ecole_display': TYPE_MAP.get(r['classe__ecole__type_ecole'], '—'),
         'nb_classes': nb_classes_par_ecole.get(r['classe__ecole__id'], 0),
         'nb_garcons': r['nb_garcons'], 'nb_filles': r['nb_filles'], 'nb_total': r['nb_total']}
        for r in ecoles_data if r['classe__ecole__id']
    ]

    niveaux_data = (
        Eleve.objects.filter(classe__annee_scolaire=annee, statut='actif')
        .values('classe__niveau__id', 'classe__niveau__nom', 'classe__niveau__code',
                'classe__niveau__cycle', 'classe__niveau__ordre')
        .annotate(nb_garcons=Count('pk', filter=Q(sexe='M')),
                  nb_filles=Count('pk', filter=Q(sexe='F')),
                  nb_total=Count('pk'))
        .filter(nb_total__gt=0).order_by('classe__niveau__ordre')
    )
    CYCLE_MAP = {'maternelle': 'Maternelle', 'primaire': 'Primaire'}
    niveaux_stats = [
        {'nom': r['classe__niveau__nom'], 'code': r['classe__niveau__code'],
         'cycle': r['classe__niveau__cycle'],
         'get_cycle_display': CYCLE_MAP.get(r['classe__niveau__cycle'], '—'),
         'nb_garcons': r['nb_garcons'], 'nb_filles': r['nb_filles'], 'nb_total': r['nb_total']}
        for r in niveaux_data if r['classe__niveau__id']
    ]

    factures = Facture.objects.filter(annee_scolaire=annee)
    stats_p = factures.aggregate(
        total_attendu=Sum('montant_total'), total_encaisse=Sum('montant_paye'),
        nb_en_attente=Count('pk', filter=Q(statut='en_attente')),
        nb_partiel=Count('pk', filter=Q(statut='partiel')),
        nb_paye=Count('pk', filter=Q(statut='paye')),
    )
    total_attendu = stats_p['total_attendu'] or 0
    total_encaisse = stats_p['total_encaisse'] or 0
    taux = round(total_encaisse / total_attendu * 100, 1) if total_attendu else 0

    top_absences = list(
        Presence.objects.filter(eleve__classe__annee_scolaire=annee, cours__isnull=True)
        .values('eleve__nom', 'eleve__prenom', 'eleve__classe__nom')
        .annotate(nb_absences=Count('pk', filter=Q(statut='absent')),
                  nb_retards=Count('pk', filter=Q(statut='retard')))
        .filter(nb_absences__gt=0).order_by('-nb_absences')[:10]
    )

    presence_stats = Presence.objects.filter(eleve__classe__annee_scolaire=annee, cours__isnull=True).aggregate(
        total=Count('pk'), absents=Count('pk', filter=Q(statut='absent')),
    )
    total_jours_presence = presence_stats['total'] or 0
    taux_presence_global = (
        round((total_jours_presence - (presence_stats['absents'] or 0)) / total_jours_presence * 100)
        if total_jours_presence else 100
    )

    ens_stats = Enseignant.objects.filter(statut='actif').aggregate(
        hommes=Count('pk', filter=Q(sexe='M')), femmes=Count('pk', filter=Q(sexe='F')),
    )

    context = {
        'annee': annee,
        'nb_eleves': global_stats['nb_eleves'],
        'nb_garcons_total': global_stats['nb_garcons'],
        'nb_filles_total': global_stats['nb_filles'],
        'nb_classes': Classe.objects.filter(annee_scolaire=annee).count(),
        'nb_ecoles': Ecole.objects.count(),
        'nb_enseignants': Enseignant.objects.filter(statut='actif').count(),
        'nb_enseignants_hommes': ens_stats['hommes'],
        'nb_enseignants_femmes': ens_stats['femmes'],
        'taux_presence_global': taux_presence_global,
        'toutes_annees': toutes_annees,
        'ecoles_stats': ecoles_stats,
        'niveaux_stats': niveaux_stats,
        'total_attendu': total_attendu,
        'total_encaisse': total_encaisse,
        'total_restant': total_attendu - total_encaisse,
        'taux_recouvrement': taux,
        'nb_en_attente': stats_p['nb_en_attente'],
        'nb_partiel': stats_p['nb_partiel'],
        'nb_paye': stats_p['nb_paye'],
        'top_absences': top_absences,
        'niveaux_labels': [n['code'] for n in niveaux_stats],
        'niveaux_garcons': [n['nb_garcons'] for n in niveaux_stats],
        'niveaux_filles': [n['nb_filles'] for n in niveaux_stats],
        'ecoles_labels': [e['nom'] for e in ecoles_stats],
        'ecoles_totaux': [e['nb_total'] for e in ecoles_stats],
        'page_title': 'Rapports & Statistiques',
        'active': 'rapports',
    }
    return render(request, 'rapports/index.html', context)


# ─────────────────────────────────────────────────────
# SAUVEGARDES
# ─────────────────────────────────────────────────────

BACKUP_DIR = settings.BASE_DIR / 'backups'


def _taille_lisible(octets):
    for unite in ('o', 'Ko', 'Mo', 'Go'):
        if octets < 1024:
            return f"{octets:.1f} {unite}"
        octets /= 1024
    return f"{octets:.1f} To"


@login_required
def sauvegardes(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('/')

    BACKUP_DIR.mkdir(exist_ok=True)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'creer':
            try:
                horodatage = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_pwd = getattr(settings, 'BACKUP_PASSWORD', '')
                suffix = '_enc' if backup_pwd else ''
                nom_zip = f"edugroupe_backup_{horodatage}{suffix}.zip"
                chemin_zip = BACKUP_DIR / nom_zip

                def _ajouter_fichiers(zf):
                    db_path = settings.BASE_DIR / 'db.sqlite3'
                    if db_path.exists():
                        zf.write(db_path, 'db.sqlite3')
                    media_root = Path(settings.MEDIA_ROOT)
                    if media_root.exists():
                        for fichier in media_root.rglob('*'):
                            if fichier.is_file():
                                zf.write(fichier, 'media/' + str(fichier.relative_to(media_root)))

                if backup_pwd:
                    with pyzipper.AESZipFile(
                        chemin_zip, 'w',
                        compression=pyzipper.ZIP_DEFLATED,
                        encryption=pyzipper.WZ_AES,
                    ) as zf:
                        zf.setpassword(backup_pwd.encode('utf-8'))
                        _ajouter_fichiers(zf)
                    chiffrement_info = ' [chiffré AES-256]'
                else:
                    with zipfile.ZipFile(chemin_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                        _ajouter_fichiers(zf)
                    chiffrement_info = ''

                taille = chemin_zip.stat().st_size
                audit_log.info(f"BACKUP CRÉÉ par {request.user.username} — {nom_zip} ({_taille_lisible(taille)}){chiffrement_info}")
                messages.success(request, f'Sauvegarde créée : {nom_zip} ({_taille_lisible(taille)}){chiffrement_info}')
            except Exception as e:
                messages.error(request, f'Erreur lors de la sauvegarde : {e}')

        elif action == 'supprimer':
            nom = request.POST.get('nom', '')
            # Sécurité : interdire path traversal
            if '/' in nom or '\\' in nom or '..' in nom:
                messages.error(request, 'Nom de fichier invalide.')
            else:
                chemin = BACKUP_DIR / nom
                if chemin.exists() and chemin.suffix == '.zip':
                    chemin.unlink()
                    audit_log.info(f"BACKUP SUPPRIMÉ par {request.user.username} — {nom}")
                    messages.success(request, f'Sauvegarde {nom} supprimée.')
                else:
                    messages.error(request, 'Fichier introuvable.')

        return redirect('rapports:sauvegardes')

    # Liste des sauvegardes existantes
    backups = []
    for f in sorted(BACKUP_DIR.glob('*.zip'), reverse=True):
        stat = f.stat()
        backups.append({
            'nom': f.name,
            'taille': _taille_lisible(stat.st_size),
            'date': datetime.fromtimestamp(stat.st_mtime),
        })

    context = {
        'backups': backups,
        'page_title': 'Sauvegardes',
        'active': 'rapports',
    }
    return render(request, 'rapports/sauvegardes.html', context)


@acces_requis("rapports")
def connexions(request):
    from eleves.models import ConnexionLog
    from django.core.paginator import Paginator
    logs = ConnexionLog.objects.select_related('user').all()
    # Filtres
    type_filtre = request.GET.get('type', '')
    search = request.GET.get('q', '').strip()
    if type_filtre:
        logs = logs.filter(type_event=type_filtre)
    if search:
        logs = logs.filter(username_tente__icontains=search)
    paginator = Paginator(logs, 11)
    page = paginator.get_page(request.GET.get('page'))
    context = {
        'page_obj': page,
        'type_filtre': type_filtre,
        'search': search,
        'page_title': "Journal d'activité",
        'active': 'connexions',
    }
    return render(request, 'rapports/connexions.html', context)


JOURNAL_RETENTION_JOURS = 90


@login_required
def purger_journal(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('rapports:connexions')

    if request.method == 'POST':
        from datetime import timedelta
        from django.utils import timezone
        from eleves.models import ConnexionLog
        seuil = timezone.now() - timedelta(days=JOURNAL_RETENTION_JOURS)
        nb_supprimees, _ = ConnexionLog.objects.filter(date__lt=seuil).delete()
        audit_log.info(f"JOURNAL PURGÉ par {request.user.username} — {nb_supprimees} entrée(s) de plus de {JOURNAL_RETENTION_JOURS} jours")
        messages.success(request, f"{nb_supprimees} entrée(s) de plus de {JOURNAL_RETENTION_JOURS} jours supprimée(s).")

    return redirect('rapports:connexions')


@login_required
def supprimer_journal_selection(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('rapports:connexions')

    if request.method == 'POST':
        from eleves.models import ConnexionLog
        ids = request.POST.getlist('ids')
        nb_supprimees, _ = ConnexionLog.objects.filter(pk__in=ids).delete()
        audit_log.info(f"JOURNAL — SUPPRESSION SÉLECTION par {request.user.username} — {nb_supprimees} entrée(s)")
        if nb_supprimees:
            messages.success(request, f"{nb_supprimees} entrée(s) supprimée(s).")
        else:
            messages.warning(request, "Aucune entrée sélectionnée.")

    redirect_url = request.POST.get('next') or 'rapports:connexions'
    return redirect(redirect_url)


@login_required
def telecharger_backup(request, nom):
    if not request.user.is_superuser and not request.user.is_staff:
        raise Http404()
    if '/' in nom or '\\' in nom or '..' in nom or not nom.endswith('.zip'):
        raise Http404()
    chemin = BACKUP_DIR / nom
    if not chemin.exists():
        raise Http404()
    audit_log.info(f"BACKUP TÉLÉCHARGÉ par {request.user.username} — {nom}")
    return FileResponse(open(chemin, 'rb'), as_attachment=True, filename=nom)
