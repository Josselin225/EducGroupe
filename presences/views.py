from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from eleves.permissions import acces_requis, get_classes_enseignant
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from datetime import date as date_type, timedelta
from .models import Presence, FeuilleDAppel, STATUT_PRESENCE
from eleves.models import Eleve, Classe, AnneeScolaire, Ecole


@acces_requis("presences")
def index(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    aujourd_hui = timezone.localdate()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and annee:
        classes = classes.filter(pk__in=classes_ids)

    # Stats du jour
    presences_jour = Presence.objects.filter(date=aujourd_hui)
    absents_jour = presences_jour.filter(statut='absent').count()
    retards_jour = presences_jour.filter(statut='retard').count()
    appels_faits = FeuilleDAppel.objects.filter(date=aujourd_hui, fait=True).count()

    context = {
        'annee': annee,
        'aujourd_hui': aujourd_hui,
        'classes': classes,
        'absents_jour': absents_jour,
        'retards_jour': retards_jour,
        'appels_faits': appels_faits,
        'total_classes': classes.count() if annee else 0,
        'page_title': 'Présences',
        'active': 'presences',
    }
    return render(request, 'presences/index.html', context)


# ──────────────────────────────────────────────
# FEUILLE D'APPEL
# ──────────────────────────────────────────────

@acces_requis("presences")
def appel_selection(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and annee:
        classes = classes.filter(pk__in=classes_ids)
    ecoles = Ecole.objects.all()

    if request.method == 'POST':
        classe_id = request.POST.get('classe')
        date_str = request.POST.get('date')
        if classe_id and date_str:
            return redirect('presences:appel', classe_id=classe_id, date_str=date_str)

    context = {
        'classes': classes,
        'ecoles': ecoles,
        'aujourd_hui': timezone.localdate().isoformat(),
        'page_title': 'Feuille d\'appel',
        'active': 'presences',
    }
    return render(request, 'presences/appel_selection.html', context)


@acces_requis("presences")
def appel(request, classe_id, date_str):
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and int(classe_id) not in classes_ids:
        messages.error(request, "Vous n'avez pas accès à l'appel de cette classe.")
        return redirect('presences:appel_selection')
    classe = get_object_or_404(Classe, pk=classe_id)
    try:
        from datetime import datetime
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Date invalide.')
        return redirect('presences:appel_selection')

    eleves = Eleve.objects.filter(classe=classe, statut='actif').order_by('nom', 'prenom')
    presences_existantes = {
        p.eleve_id: p
        for p in Presence.objects.filter(eleve__in=eleves, date=date, cours__isnull=True)
    }

    if request.method == 'POST':
        from .notifications import notifier_absence
        with transaction.atomic():
            for eleve in eleves:
                statut = request.POST.get(f'statut_{eleve.pk}', 'present')
                motif = request.POST.get(f'motif_{eleve.pk}', '').strip()
                prev = presences_existantes.get(eleve.pk)
                prev_statut = prev.statut if prev else 'present'
                Presence.objects.update_or_create(
                    eleve=eleve, date=date, cours=None,
                    defaults={'statut': statut, 'motif': motif}
                )
                if statut in ('absent', 'retard', 'excuse') and prev_statut != statut:
                    notifier_absence(eleve, date, statut, motif)
            FeuilleDAppel.objects.update_or_create(
                cours=None, date=date,
                defaults={'fait': True, 'observations': request.POST.get('observations', '')}
            )
        messages.success(request, f'Appel enregistré pour {classe.nom} le {date.strftime("%d/%m/%Y")}.')
        return redirect('presences:appel', classe_id=classe_id, date_str=date_str)

    lignes = []
    for eleve in eleves:
        p = presences_existantes.get(eleve.pk)
        lignes.append({
            'eleve': eleve,
            'statut': p.statut if p else 'present',
            'motif': p.motif if p else '',
        })

    nb_presents = sum(1 for l in lignes if l['statut'] == 'present')
    nb_absents = sum(1 for l in lignes if l['statut'] in ('absent', 'excuse'))
    nb_retards = sum(1 for l in lignes if l['statut'] == 'retard')

    context = {
        'classe': classe,
        'date': date,
        'lignes': lignes,
        'statuts': STATUT_PRESENCE,
        'nb_presents': nb_presents,
        'nb_absents': nb_absents,
        'nb_retards': nb_retards,
        'page_title': f'Appel — {classe.nom} — {date.strftime("%d/%m/%Y")}',
        'active': 'presences',
    }
    return render(request, 'presences/appel.html', context)


# ──────────────────────────────────────────────
# SUIVI DES ABSENCES
# ──────────────────────────────────────────────

@acces_requis("presences")
def suivi(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and annee:
        classes = classes.filter(pk__in=classes_ids)
    classe_id = request.GET.get('classe')
    classe_selectionnee = None
    rapport = []

    if classe_id:
        classe_selectionnee = get_object_or_404(Classe, pk=classe_id)
        eleves = Eleve.objects.filter(
            classe=classe_selectionnee, statut='actif'
        ).order_by('nom', 'prenom').annotate(
            total_absences=Count('presences', filter=Q(presences__statut='absent', presences__cours__isnull=True)),
            total_excuses=Count('presences', filter=Q(presences__statut='excuse', presences__cours__isnull=True)),
            total_retards=Count('presences', filter=Q(presences__statut='retard', presences__cours__isnull=True)),
            total_jours=Count('presences', filter=Q(presences__cours__isnull=True)),
        )
        rapport = [
            {
                'eleve': eleve,
                'total_absences': eleve.total_absences,
                'total_excuses': eleve.total_excuses,
                'total_retards': eleve.total_retards,
                'total_jours': eleve.total_jours,
            }
            for eleve in eleves
        ]

    context = {
        'classes': classes,
        'classe_selectionnee': classe_selectionnee,
        'rapport': rapport,
        'page_title': 'Suivi des absences',
        'active': 'presences',
    }
    return render(request, 'presences/suivi.html', context)


@acces_requis("presences")
def historique_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and eleve.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès aux données de cet élève.")
        return redirect('presences:suivi')
    presences = Presence.objects.filter(eleve=eleve, cours__isnull=True).order_by('-date')
    context = {
        'eleve': eleve,
        'presences': presences,
        'total_absences': presences.filter(statut='absent').count(),
        'total_excuses': presences.filter(statut='excuse').count(),
        'total_retards': presences.filter(statut='retard').count(),
        'page_title': f'Historique — {eleve.nom_complet()}',
        'active': 'presences',
    }
    return render(request, 'presences/historique_eleve.html', context)


@acces_requis("presences")
def statistiques(request):
    from calendar import month_name
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and annee:
        classes = classes.filter(pk__in=classes_ids)

    classe_id = request.GET.get('classe')
    classe_selectionnee = None
    stats_eleves = []
    absences_par_mois = []

    if classe_id:
        if classes_ids is not None and int(classe_id) not in classes_ids:
            messages.error(request, "Vous n'avez pas accès à cette classe.")
            return redirect('presences:statistiques')
        classe_selectionnee = get_object_or_404(Classe, pk=classe_id)
        eleves = Eleve.objects.filter(classe=classe_selectionnee, statut='actif').order_by('nom', 'prenom')

        # Stats par élève
        for eleve in eleves:
            pqs = Presence.objects.filter(eleve=eleve, cours__isnull=True)
            total = pqs.count()
            abs_count = pqs.filter(statut='absent').count()
            ret_count = pqs.filter(statut='retard').count()
            exc_count = pqs.filter(statut='excuse').count()
            taux = round((total - abs_count) / total * 100) if total else 100
            stats_eleves.append({
                'eleve': eleve,
                'total': total,
                'absences': abs_count,
                'retards': ret_count,
                'excuses': exc_count,
                'taux_presence': taux,
                'alerte': abs_count >= 5,
            })
        # Trier par nb absences décroissant
        stats_eleves.sort(key=lambda x: x['absences'], reverse=True)

        # Absences par mois
        from django.db.models.functions import TruncMonth
        mois_data = (
            Presence.objects.filter(
                eleve__classe=classe_selectionnee, cours__isnull=True, statut__in=['absent', 'excuse']
            )
            .annotate(mois=TruncMonth('date'))
            .values('mois')
            .annotate(nb=Count('pk'))
            .order_by('mois')
        )
        absences_par_mois = [
            {'mois': row['mois'].strftime('%b %Y'), 'nb': row['nb']}
            for row in mois_data if row['mois']
        ]

    context = {
        'classes': classes,
        'classe_selectionnee': classe_selectionnee,
        'stats_eleves': stats_eleves,
        'absences_par_mois': absences_par_mois,
        'page_title': 'Statistiques de présence',
        'active': 'presences',
    }
    return render(request, 'presences/statistiques.html', context)
