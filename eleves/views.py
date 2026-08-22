from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator
from .models import Eleve, Classe, AnneeScolaire, Ecole, Niveau, GroupeScolaire
from .forms import EcoleForm, ClasseForm, EleveForm, AnneeScolaireForm, GroupeScolaireForm
from .permissions import acces_requis, get_classes_enseignant
from django.http import HttpResponse


def _render_pdf(template_name, context):
    """Génère un HttpResponse PDF à partir d'un template HTML."""
    from io import BytesIO
    from xhtml2pdf import pisa
    from django.template.loader import render_to_string
    html = render_to_string(template_name, context)
    buf = BytesIO()
    pisa.pisaDocument(BytesIO(html.encode('utf-8')), buf)
    buf.seek(0)
    return buf.read()


def _logo_placeholder_path():
    """Icône de secours (fichier image, pas un div) pour un rendu circulaire fiable dans les PDF."""
    from django.conf import settings
    dossier = settings.MEDIA_ROOT / 'generated'
    chemin = dossier / 'logo_placeholder.png'
    if chemin.exists():
        return str(chemin)

    dossier.mkdir(parents=True, exist_ok=True)
    from PIL import Image, ImageDraw

    size = 160
    img = Image.new('RGB', (size, size), (26, 60, 110))
    draw = ImageDraw.Draw(img)
    border = 6
    draw.ellipse([border, border, size - border, size - border],
                 fill=(53, 83, 129), outline=(232, 160, 32), width=border)

    cx, cy = size / 2, size / 2 - 6
    w = 64
    gold = (232, 160, 32)
    draw.polygon([(cx - w / 2, cy), (cx, cy - w / 4), (cx + w / 2, cy), (cx, cy + w / 4)], fill=gold)
    draw.rectangle([cx - w / 4, cy + w / 4 - 2, cx + w / 4, cy + w / 4 + 10], fill=gold)
    draw.line([(cx + w / 2 - 4, cy), (cx + w / 2 - 4, cy + 26)], fill=gold, width=4)
    draw.ellipse([cx + w / 2 - 8, cy + 22, cx + w / 2, cy + 30], fill=gold)

    img.save(chemin, format='PNG')
    return str(chemin)


def _photo_placeholder_path():
    """Avatar de secours (fichier image, pas un div) pour un rendu circulaire fiable dans les PDF."""
    from django.conf import settings
    dossier = settings.MEDIA_ROOT / 'generated'
    chemin = dossier / 'photo_placeholder.png'
    if chemin.exists():
        return str(chemin)

    dossier.mkdir(parents=True, exist_ok=True)
    from PIL import Image, ImageDraw

    size = 160
    img = Image.new('RGB', (size, size), (26, 60, 110))
    draw = ImageDraw.Draw(img)
    border = 8
    draw.ellipse([border, border, size - border, size - border],
                 fill=(53, 83, 129), outline=(232, 160, 32), width=border)

    silhouette = (200, 210, 225)
    cx = size / 2
    draw.ellipse([cx - 24, 44, cx + 24, 92], fill=silhouette)
    draw.pieslice([cx - 42, 88, cx + 42, 172], 180, 360, fill=silhouette)

    img.save(chemin, format='PNG')
    return str(chemin)


def _eleve_photo_pdf_path(eleve):
    """Recopie la photo de l'élève vers un nom de fichier ASCII sûr : certains noms de fichiers
    uploadés contiennent un encodage corrompu que xhtml2pdf ne parvient pas à charger, alors que
    le navigateur (via l'URL HTTP) s'en accommode sans problème."""
    if not eleve.photo:
        return None
    from django.conf import settings
    from PIL import Image

    dossier = settings.MEDIA_ROOT / 'generated' / 'photos_pdf'
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f'{eleve.pk}.jpg'
    img = Image.open(eleve.photo.path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.save(chemin, format='JPEG', quality=90)
    return str(chemin)


@login_required
def dashboard(request):
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Sum, Q as DQ
    from paiements.models import Facture, Paiement
    from presences.models import Presence
    from enseignants.models import Enseignant
    from notes.models import Evaluation, Bulletin

    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    aujourd_hui = timezone.localdate()
    classes_ids = get_classes_enseignant(request.user)
    est_enseignant = classes_ids is not None

    # ── Élèves
    eleves_qs = Eleve.objects.filter(statut='actif')
    if est_enseignant:
        eleves_qs = eleves_qs.filter(classe__in=classes_ids)
    total_eleves = eleves_qs.count()
    total_garcons = eleves_qs.filter(sexe='M').count()
    total_filles = eleves_qs.filter(sexe='F').count()

    # ── Classes & Écoles
    if est_enseignant:
        total_classes = len(classes_ids)
        total_ecoles = 0
        total_enseignants = 0
    else:
        total_classes = Classe.objects.filter(annee_scolaire=annee).count() if annee else 0
        total_ecoles = Ecole.objects.count()
        total_enseignants = Enseignant.objects.filter(statut='actif').count()

    # ── Présences du jour
    presences_qs = Presence.objects.filter(date=aujourd_hui, cours__isnull=True)
    if est_enseignant:
        presences_qs = presences_qs.filter(eleve__classe__in=classes_ids)
    absents_jour = presences_qs.filter(statut='absent').count()
    retards_jour = presences_qs.filter(statut='retard').count()

    # ── Absences 7 derniers jours (graphique tendance)
    dates_7j = [(aujourd_hui - timedelta(days=i)) for i in range(6, -1, -1)]
    absences_7j_labels = []
    absences_7j_data = []
    for d in dates_7j:
        qs = Presence.objects.filter(date=d, cours__isnull=True, statut='absent')
        if est_enseignant:
            qs = qs.filter(eleve__classe__in=classes_ids)
        absences_7j_labels.append(d.strftime('%a %d'))
        absences_7j_data.append(qs.count())

    # ── Paiements
    total_attendu = total_encaisse = total_restant = nb_impayes = taux_recouvrement = 0
    paiements_recents = []
    if not est_enseignant and annee:
        factures = Facture.objects.filter(annee_scolaire=annee)
        stats = factures.aggregate(total_attendu=Sum('montant_total'), total_encaisse=Sum('montant_paye'))
        total_attendu = stats['total_attendu'] or 0
        total_encaisse = stats['total_encaisse'] or 0
        total_restant = total_attendu - total_encaisse
        nb_impayes = factures.filter(statut__in=['en_attente', 'partiel']).count()
        taux_recouvrement = round(total_encaisse / total_attendu * 100) if total_attendu else 0
        paiements_recents = list(
            Paiement.objects.select_related('facture__eleve', 'facture__type_frais')
            .order_by('-date_paiement', '-pk')[:6]
        )

    # ── Évaluations à venir (7 j)
    evals_prochaines = []
    if annee:
        eqs = Evaluation.objects.filter(
            annee_scolaire=annee,
            date__gte=aujourd_hui,
            date__lte=aujourd_hui + timedelta(days=7),
        ).select_related('matiere', 'classe').order_by('date')
        if est_enseignant:
            eqs = eqs.filter(classe__in=classes_ids)
        evals_prochaines = list(eqs[:8])

    # ── Top absents (non-enseignant)
    top_absents = []
    if not est_enseignant:
        top_absents = list(
            Presence.objects.filter(cours__isnull=True, statut='absent', eleve__statut='actif')
            .values('eleve__nom', 'eleve__prenom', 'eleve__classe__nom', 'eleve__pk')
            .annotate(nb=Count('pk'))
            .order_by('-nb')[:5]
        )

    # ── Inscriptions récentes / mes élèves
    if est_enseignant:
        dernieres_inscriptions = list(
            eleves_qs.select_related('classe__ecole', 'classe__niveau').order_by('nom', 'prenom')[:8]
        )
    else:
        dernieres_inscriptions = list(
            Eleve.objects.filter(statut='actif')
            .select_related('classe__ecole', 'classe__niveau').order_by('-date_inscription')[:6]
        )

    # ── Répartition par école
    ecoles_data = []
    if not est_enseignant:
        for ecole in Ecole.objects.all():
            nb = Eleve.objects.filter(statut='actif', classe__ecole=ecole).count()
            if nb > 0:
                ecoles_data.append({'nom': ecole.nom, 'nb': nb})

    context = {
        'annee': annee,
        'aujourd_hui': aujourd_hui,
        'est_enseignant': est_enseignant,
        'total_eleves': total_eleves,
        'total_garcons': total_garcons,
        'total_filles': total_filles,
        'total_classes': total_classes,
        'total_ecoles': total_ecoles,
        'total_enseignants': total_enseignants,
        'absents_jour': absents_jour,
        'retards_jour': retards_jour,
        'total_attendu': total_attendu,
        'total_encaisse': total_encaisse,
        'total_restant': total_restant,
        'nb_impayes': nb_impayes,
        'taux_recouvrement': taux_recouvrement,
        'paiements_recents': paiements_recents,
        'absences_7j_labels': absences_7j_labels,
        'absences_7j_data': absences_7j_data,
        'evals_prochaines': evals_prochaines,
        'top_absents': top_absents,
        'dernieres_inscriptions': dernieres_inscriptions,
        'ecoles_data': ecoles_data,
        'page_title': 'Tableau de bord',
        'active': 'dashboard',
    }
    return render(request, 'dashboard.html', context)


# ──────────────────────────────────────────────
# PARAMÈTRES DU GROUPE
# ──────────────────────────────────────────────

@acces_requis("parametres")
def parametres(request):
    groupe = GroupeScolaire.get()
    form = GroupeScolaireForm(request.POST or None, request.FILES or None, instance=groupe)
    if form.is_valid():
        form.save()
        messages.success(request, 'Paramètres enregistrés.')
        return redirect('eleves:parametres')
    context = {'form': form, 'groupe': groupe, 'page_title': 'Paramètres', 'active': 'parametres'}
    return render(request, 'eleves/parametres.html', context)


# ──────────────────────────────────────────────
# ANNÉES SCOLAIRES
# ──────────────────────────────────────────────

@acces_requis("annees")
def annees_liste(request):
    annees = AnneeScolaire.objects.annotate(
        nb_classes=Count('classes', distinct=True),
        nb_eleves=Count('classes__eleves', distinct=True),
    ).order_by('-date_debut')
    context = {
        'annees': annees,
        'page_title': 'Années scolaires',
        'active': 'annees',
    }
    return render(request, 'eleves/annees/liste.html', context)


@acces_requis("annees")
def annee_ajouter(request):
    form = AnneeScolaireForm(request.POST or None)
    if form.is_valid():
        annee = form.save(commit=False)
        annee.en_cours = False
        annee.save()
        messages.success(request, f'Année scolaire {annee.libelle} créée.')
        return redirect('eleves:annees_liste')
    context = {'form': form, 'page_title': 'Nouvelle année scolaire', 'active': 'annees'}
    return render(request, 'eleves/annees/form.html', context)


@acces_requis("annees")
def annee_modifier(request, pk):
    annee = get_object_or_404(AnneeScolaire, pk=pk)
    form = AnneeScolaireForm(request.POST or None, instance=annee)
    if form.is_valid():
        form.save()
        messages.success(request, f'Année scolaire {annee.libelle} modifiée.')
        return redirect('eleves:annees_liste')
    context = {'form': form, 'annee': annee, 'page_title': f'Modifier — {annee.libelle}', 'active': 'annees'}
    return render(request, 'eleves/annees/form.html', context)


@acces_requis("annees")
def annee_activer(request, pk):
    annee = get_object_or_404(AnneeScolaire, pk=pk)
    if request.method == 'POST':
        annee.en_cours = True
        annee.save()
        messages.success(request, f'Année scolaire {annee.libelle} activée.')
    return redirect('eleves:annees_liste')


@acces_requis("annees")
def promotion(request):
    """Promotion automatique : affecte les élèves aux classes de la nouvelle année."""
    annee_actuelle = AnneeScolaire.objects.filter(en_cours=True).first()
    toutes_annees = AnneeScolaire.objects.order_by('-date_debut')
    niveaux = Niveau.objects.order_by('ordre')

    # Mapping de promotion : niveau actuel -> niveau suivant
    niveaux_list = list(niveaux)
    promotion_map = {}
    for i, n in enumerate(niveaux_list):
        if i + 1 < len(niveaux_list):
            promotion_map[n.pk] = niveaux_list[i + 1]

    if request.method == 'POST':
        annee_source_id = request.POST.get('annee_source')
        annee_dest_id = request.POST.get('annee_dest')
        annee_source = get_object_or_404(AnneeScolaire, pk=annee_source_id)
        annee_dest = get_object_or_404(AnneeScolaire, pk=annee_dest_id)

        promus = 0
        non_affectes = 0

        eleves = Eleve.objects.filter(
            classe__annee_scolaire=annee_source, statut='actif'
        ).select_related('classe__niveau')

        for eleve in eleves:
            niveau_actuel = eleve.classe.niveau
            niveau_suivant = promotion_map.get(niveau_actuel.pk)
            if not niveau_suivant:
                non_affectes += 1
                continue

            # Chercher une classe du niveau suivant dans la même école
            classe_dest = Classe.objects.filter(
                annee_scolaire=annee_dest,
                niveau=niveau_suivant,
                ecole=eleve.classe.ecole,
            ).first()

            if classe_dest:
                eleve.classe = classe_dest
                eleve.save()
                promus += 1
            else:
                non_affectes += 1

        messages.success(
            request,
            f'{promus} élève(s) promus vers {annee_dest.libelle}. '
            f'{non_affectes} élève(s) non affecté(s) (classe manquante ou fin de cycle).'
        )
        return redirect('eleves:promotion')

    # Aperçu des effectifs par niveau
    apercu = []
    if annee_actuelle:
        for niveau in niveaux_list:
            nb = Eleve.objects.filter(
                classe__annee_scolaire=annee_actuelle,
                classe__niveau=niveau,
                statut='actif'
            ).count()
            suivant = promotion_map.get(niveau.pk)
            apercu.append({'niveau': niveau, 'nb_eleves': nb, 'vers': suivant})

    context = {
        'annee_actuelle': annee_actuelle,
        'toutes_annees': toutes_annees,
        'apercu': apercu,
        'page_title': 'Promotion des élèves',
        'active': 'annees',
    }
    return render(request, 'eleves/annees/promotion.html', context)


# ──────────────────────────────────────────────
# ÉCOLES
# ──────────────────────────────────────────────

@acces_requis("ecoles")
def ecoles_liste(request):
    ecoles = Ecole.objects.all()
    context = {
        'ecoles': ecoles,
        'page_title': 'Écoles',
        'active': 'ecoles',
    }
    return render(request, 'eleves/ecoles/liste.html', context)


@acces_requis("ecoles")
def ecole_ajouter(request):
    form = EcoleForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'École ajoutée avec succès.')
        return redirect('eleves:ecoles_liste')
    context = {'form': form, 'page_title': 'Ajouter une école', 'active': 'ecoles'}
    return render(request, 'eleves/ecoles/form.html', context)


@acces_requis("ecoles")
def ecole_modifier(request, pk):
    ecole = get_object_or_404(Ecole, pk=pk)
    form = EcoleForm(request.POST or None, instance=ecole)
    if form.is_valid():
        form.save()
        messages.success(request, 'École modifiée avec succès.')
        return redirect('eleves:ecoles_liste')
    context = {'form': form, 'ecole': ecole, 'page_title': f'Modifier — {ecole.nom}', 'active': 'ecoles'}
    return render(request, 'eleves/ecoles/form.html', context)


@acces_requis("ecoles")
def ecole_supprimer(request, pk):
    ecole = get_object_or_404(Ecole, pk=pk)
    if request.method == 'POST':
        ecole.delete()
        messages.success(request, 'École supprimée.')
        return redirect('eleves:ecoles_liste')
    context = {'ecole': ecole, 'page_title': f'Supprimer — {ecole.nom}', 'active': 'ecoles'}
    return render(request, 'eleves/ecoles/confirmer_suppression.html', context)


# ──────────────────────────────────────────────
# CLASSES
# ──────────────────────────────────────────────

@acces_requis("classes")
def classes_liste(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes = Classe.objects.select_related('ecole', 'niveau', 'annee_scolaire').filter(annee_scolaire=annee) if annee else []
    ecoles = Ecole.objects.all()
    ecole_filtre = request.GET.get('ecole')
    if ecole_filtre:
        classes = classes.filter(ecole__id=ecole_filtre)
    context = {
        'classes': classes,
        'ecoles': ecoles,
        'annee': annee,
        'page_title': 'Classes',
        'active': 'classes',
    }
    return render(request, 'eleves/classes/liste.html', context)


@acces_requis("classes")
def classe_ajouter(request):
    form = ClasseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Classe ajoutée avec succès.')
        return redirect('eleves:classes_liste')
    context = {'form': form, 'page_title': 'Ajouter une classe', 'active': 'classes'}
    return render(request, 'eleves/classes/form.html', context)


@acces_requis("classes")
def classe_modifier(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    form = ClasseForm(request.POST or None, instance=classe)
    if form.is_valid():
        form.save()
        messages.success(request, 'Classe modifiée avec succès.')
        return redirect('eleves:classes_liste')
    context = {'form': form, 'classe': classe, 'page_title': f'Modifier — {classe.nom}', 'active': 'classes'}
    return render(request, 'eleves/classes/form.html', context)


@acces_requis("classes")
def classe_supprimer(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    if request.method == 'POST':
        classe.delete()
        messages.success(request, 'Classe supprimée.')
        return redirect('eleves:classes_liste')
    context = {'classe': classe, 'page_title': f'Supprimer — {classe.nom}', 'active': 'classes'}
    return render(request, 'eleves/classes/confirmer_suppression.html', context)


# ──────────────────────────────────────────────
# ÉLÈVES
# ──────────────────────────────────────────────

@acces_requis("eleves")
def index(request):
    from .permissions import get_classes_enseignant
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    eleves = Eleve.objects.filter(statut='actif').select_related('classe__niveau', 'classe__ecole')
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('niveau', 'ecole') if annee else []
    ecoles = Ecole.objects.all()

    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None:
        eleves = eleves.filter(classe__in=classes_ids)
        classes = classes.filter(pk__in=classes_ids)
        ecoles = Ecole.objects.filter(classes__pk__in=classes_ids).distinct() if classes_ids else Ecole.objects.none()

    classe_filtre = request.GET.get('classe')
    ecole_filtre = request.GET.get('ecole')
    if ecole_filtre:
        eleves = eleves.filter(classe__ecole__id=ecole_filtre)
        classes = classes.filter(ecole__id=ecole_filtre)
    if classe_filtre:
        eleves = eleves.filter(classe__id=classe_filtre)
    search = request.GET.get('q', '').strip()
    if search:
        from django.db.models import Q
        eleves = eleves.filter(Q(nom__icontains=search) | Q(prenom__icontains=search) | Q(matricule__icontains=search))
    total_eleves = eleves.count()
    context = {
        'eleves': eleves,
        'classes': classes,
        'ecoles': ecoles,
        'annee': annee,
        'total_eleves': total_eleves,
        'total_garcons': eleves.filter(sexe='M').count(),
        'total_filles': eleves.filter(sexe='F').count(),
        'search': search,
        'page_title': 'Gestion des Élèves',
        'active': 'eleves',
    }
    return render(request, 'eleves/index.html', context)


@acces_requis("eleves", ecriture=True)
def eleve_ajouter(request):
    form = EleveForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Élève ajouté avec succès.')
        return redirect('eleves:index')
    context = {'form': form, 'page_title': 'Ajouter un élève', 'active': 'eleves'}
    return render(request, 'eleves/eleve_form.html', context)


@acces_requis("eleves", ecriture=True)
def eleve_modifier(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    form = EleveForm(request.POST or None, request.FILES or None, instance=eleve)
    if form.is_valid():
        form.save()
        messages.success(request, 'Élève modifié avec succès.')
        return redirect('eleves:index')
    context = {'form': form, 'eleve': eleve, 'page_title': f'Modifier — {eleve.nom_complet()}', 'active': 'eleves'}
    return render(request, 'eleves/eleve_form.html', context)


@acces_requis("eleves")
def carte_scolaire(request, pk):
    """Carte scolaire individuelle d'un élève."""
    eleve = get_object_or_404(Eleve, pk=pk)
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and eleve.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès à cet élève.")
        return redirect('eleves:index')
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    context = {
        'eleves': [eleve],
        'annee': annee,
        'page_title': f'Carte scolaire — {eleve.nom_complet()}',
        'active': 'eleves',
    }
    return render(request, 'eleves/cartes_scolaires.html', context)


@acces_requis("eleves")
def cartes_scolaires_classe(request):
    """Impression en lot des cartes scolaires d'une classe."""
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and annee:
        classes = classes.filter(pk__in=classes_ids)

    classe_id = request.GET.get('classe')
    eleves = []
    classe_selectionnee = None

    if classe_id:
        classe_selectionnee = get_object_or_404(Classe, pk=classe_id)
        if classes_ids is not None and int(classe_id) not in classes_ids:
            messages.error(request, "Vous n'avez pas accès à cette classe.")
            return redirect('eleves:cartes_scolaires_classe')
        eleves = Eleve.objects.filter(
            classe=classe_selectionnee, statut='actif'
        ).select_related('classe__ecole', 'classe__niveau', 'classe__annee_scolaire').order_by('nom', 'prenom')

    if request.GET.get('imprimer') and eleves:
        context = {
            'eleves': eleves,
            'annee': annee,
            'page_title': f'Cartes scolaires — {classe_selectionnee.nom}',
            'active': 'eleves',
            'mode_impression': True,
        }
        return render(request, 'eleves/cartes_scolaires.html', context)

    context = {
        'classes': classes,
        'classe_selectionnee': classe_selectionnee,
        'eleves': eleves,
        'annee': annee,
        'page_title': 'Cartes scolaires',
        'active': 'eleves',
    }
    return render(request, 'eleves/cartes_selection.html', context)


@acces_requis("eleves")
def fiche_inscription(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and eleve.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès à cet élève.")
        return redirect('eleves:index')
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    context = {
        'eleve': eleve,
        'annee': annee,
        'page_title': f'Fiche d\'inscription — {eleve.nom_complet()}',
        'active': 'eleves',
    }
    return render(request, 'eleves/fiche_inscription.html', context)


@acces_requis("eleves")
def fiche_inscription_pdf(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and eleve.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès à cet élève.")
        return redirect('eleves:index')
    annee = AnneeScolaire.objects.filter(en_cours=True).first()

    from eleves.context_processors import groupe_scolaire
    groupe_ctx = groupe_scolaire(request)

    context = {
        'eleve': eleve,
        'annee': annee,
        'logo_placeholder': _logo_placeholder_path(),
        'photo_placeholder': _photo_placeholder_path(),
        'eleve_photo_path': _eleve_photo_pdf_path(eleve),
        **groupe_ctx,
    }
    pdf_bytes = _render_pdf('eleves/fiche_inscription_pdf.html', context)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="fiche_inscription_{eleve.matricule}.pdf"'
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response


@acces_requis("eleves", ecriture=True)
def eleve_supprimer(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        eleve.statut = 'inactif'
        eleve.save()
        messages.success(request, f'{eleve.nom_complet()} a été désactivé.')
        return redirect('eleves:index')
    context = {'eleve': eleve, 'page_title': f'Désactiver — {eleve.nom_complet()}', 'active': 'eleves'}
    return render(request, 'eleves/eleve_confirmer_suppression.html', context)


@acces_requis("eleves")
def eleve_dossier(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and eleve.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès à cet élève.")
        return redirect('eleves:index')
    annee = AnneeScolaire.objects.filter(en_cours=True).first()

    # Notes par période
    from notes.models import Evaluation, Note, Bulletin
    from django.db.models import Avg
    bulletins = Bulletin.objects.filter(
        eleve=eleve, annee_scolaire=annee
    ).order_by('periode') if annee else []

    # Présences
    from presences.models import Presence
    from django.db.models import Count, Q as QQ
    presences_stats = Presence.objects.filter(eleve=eleve, cours__isnull=True).aggregate(
        total=Count('pk'),
        absences=Count('pk', filter=QQ(statut='absent')),
        retards=Count('pk', filter=QQ(statut='retard')),
        excuses=Count('pk', filter=QQ(statut='excuse')),
    )
    total_jours = presences_stats['total'] or 0
    taux_presence = round((total_jours - (presences_stats['absences'] or 0)) / total_jours * 100) if total_jours else 100

    # Paiements
    from paiements.models import Facture
    factures = Facture.objects.filter(eleve=eleve, annee_scolaire=annee).select_related('type_frais') if annee else []

    context = {
        'eleve': eleve,
        'annee': annee,
        'bulletins': bulletins,
        'presences_stats': presences_stats,
        'taux_presence': taux_presence,
        'factures': factures,
        'page_title': f'Dossier — {eleve.nom_complet()}',
        'active': 'eleves',
    }
    return render(request, 'eleves/dossier.html', context)
