from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from eleves.permissions import acces_requis, get_classes_enseignant, get_role, get_enseignant
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from .models import Evaluation, Note, Bulletin
from .forms import EvaluationForm
from eleves.models import Eleve, Classe, AnneeScolaire
from enseignants.models import Matiere


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


@acces_requis("notes")
def index(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    evaluations = Evaluation.objects.filter(annee_scolaire=annee).select_related('matiere', 'classe') if annee else []
    context = {
        'annee': annee,
        'total_evaluations': evaluations.count() if annee else 0,
        'evaluations_recentes': evaluations[:5],
        'page_title': 'Notes & Bulletins',
        'active': 'notes',
    }
    return render(request, 'notes/index.html', context)


# ──────────────────────────────────────────────
# ÉVALUATIONS
# ──────────────────────────────────────────────

@acces_requis("notes")
def evaluations_liste(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes_ids = get_classes_enseignant(request.user)
    evaluations = Evaluation.objects.select_related('matiere', 'classe__ecole', 'enseignant').filter(annee_scolaire=annee) if annee else []
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    if classes_ids is not None:
        evaluations = evaluations.filter(classe__in=classes_ids)
        classes = classes.filter(pk__in=classes_ids)
    classe_filtre = request.GET.get('classe')
    periode_filtre = request.GET.get('periode')
    if classe_filtre:
        evaluations = evaluations.filter(classe__id=classe_filtre)
    if periode_filtre:
        evaluations = evaluations.filter(periode=periode_filtre)
    context = {
        'evaluations': evaluations,
        'classes': classes,
        'annee': annee,
        'periodes': Evaluation.periode.field.choices,
        'page_title': 'Évaluations',
        'active': 'notes',
    }
    return render(request, 'notes/evaluations/liste.html', context)


@acces_requis("notes")
def evaluation_ajouter(request):
    classes_ids = get_classes_enseignant(request.user)
    form = EvaluationForm(request.POST or None)
    if classes_ids is not None:
        form.fields['classe'].queryset = Classe.objects.filter(pk__in=classes_ids)
        enseignant = get_enseignant(request.user)
        if enseignant:
            from enseignants.models import Enseignant as EnseignantModel
            form.fields['enseignant'].queryset = EnseignantModel.objects.filter(pk=enseignant.pk)
            form.fields['enseignant'].initial = enseignant
    if form.is_valid():
        form.save()
        messages.success(request, 'Évaluation créée. Vous pouvez maintenant saisir les notes.')
        return redirect('notes:evaluations_liste')
    context = {'form': form, 'page_title': 'Nouvelle évaluation', 'active': 'notes'}
    return render(request, 'notes/evaluations/form.html', context)


def _check_eval_access(request, evaluation):
    """Vérifie qu'un enseignant a accès à cette évaluation. Retourne un redirect ou None."""
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and evaluation.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès à cette évaluation.")
        return redirect('notes:evaluations_liste')
    return None


@acces_requis("notes")
def evaluation_modifier(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    guard = _check_eval_access(request, evaluation)
    if guard:
        return guard
    form = EvaluationForm(request.POST or None, instance=evaluation)
    if form.is_valid():
        form.save()
        messages.success(request, 'Évaluation modifiée.')
        return redirect('notes:evaluations_liste')
    context = {'form': form, 'evaluation': evaluation, 'page_title': f'Modifier — {evaluation.intitule}', 'active': 'notes'}
    return render(request, 'notes/evaluations/form.html', context)


@acces_requis("notes")
def evaluation_supprimer(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    guard = _check_eval_access(request, evaluation)
    if guard:
        return guard
    if request.method == 'POST':
        evaluation.delete()
        messages.success(request, 'Évaluation supprimée.')
        return redirect('notes:evaluations_liste')
    context = {'evaluation': evaluation, 'page_title': f'Supprimer — {evaluation.intitule}', 'active': 'notes'}
    return render(request, 'notes/evaluations/confirmer_suppression.html', context)


# ──────────────────────────────────────────────
# SAISIE DES NOTES
# ──────────────────────────────────────────────

@acces_requis("notes")
def saisie_notes(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    guard = _check_eval_access(request, evaluation)
    if guard:
        return guard
    eleves = Eleve.objects.filter(classe=evaluation.classe, statut='actif').order_by('nom', 'prenom')
    notes_existantes = {n.eleve_id: n for n in Note.objects.filter(evaluation=evaluation)}

    if request.method == 'POST':
        with transaction.atomic():
            for eleve in eleves:
                valeur_str = request.POST.get(f'note_{eleve.pk}', '').strip()
                absent = request.POST.get(f'absent_{eleve.pk}') == 'on'
                observation = request.POST.get(f'obs_{eleve.pk}', '').strip()
                note = notes_existantes.get(eleve.pk)

                if absent:
                    if note:
                        note.absent = True
                        note.valeur = Decimal('0')
                        note.observation = observation
                        note.save()
                    else:
                        Note.objects.create(evaluation=evaluation, eleve=eleve,
                                            valeur=Decimal('0'), absent=True, observation=observation)
                elif valeur_str:
                    try:
                        valeur = Decimal(valeur_str)
                        if valeur < 0:
                            valeur = Decimal('0')
                        if valeur > evaluation.note_max:
                            valeur = evaluation.note_max
                        if note:
                            note.valeur = valeur
                            note.absent = False
                            note.observation = observation
                            note.save()
                        else:
                            Note.objects.create(evaluation=evaluation, eleve=eleve,
                                                valeur=valeur, absent=False, observation=observation)
                    except InvalidOperation:
                        pass

        messages.success(request, f'Notes enregistrées pour {evaluation.intitule}.')
        return redirect('notes:saisie_notes', pk=pk)

    lignes = []
    for eleve in eleves:
        note = notes_existantes.get(eleve.pk)
        lignes.append({
            'eleve': eleve,
            'note': note,
            'valeur': note.valeur if note and not note.absent else '',
            'absent': note.absent if note else False,
            'observation': note.observation if note else '',
        })

    context = {
        'evaluation': evaluation,
        'lignes': lignes,
        'nb_notes': sum(1 for l in lignes if l['note'] and not l['absent']),
        'page_title': f'Saisie — {evaluation.intitule}',
        'active': 'notes',
    }
    return render(request, 'notes/evaluations/saisie_notes.html', context)


# ──────────────────────────────────────────────
# BULLETINS
# ──────────────────────────────────────────────

@acces_requis("notes")
def bulletins_liste(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes_ids = get_classes_enseignant(request.user)
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    if classes_ids is not None:
        classes = classes.filter(pk__in=classes_ids)
    classe_id = request.GET.get('classe')
    periode = request.GET.get('periode', 'T1')
    eleves = []
    classe_selectionnee = None

    if classe_id:
        classe_selectionnee = get_object_or_404(Classe, pk=classe_id)
        if classes_ids is not None and classe_selectionnee.pk not in classes_ids:
            messages.error(request, "Vous n'avez pas accès aux bulletins de cette classe.")
            return redirect('notes:bulletins_liste')
        eleves = Eleve.objects.filter(classe=classe_selectionnee, statut='actif').order_by('nom')

    context = {
        'classes': classes,
        'classe_selectionnee': classe_selectionnee,
        'eleves': eleves,
        'periodes': Evaluation.periode.field.choices,
        'periode': periode,
        'annee': annee,
        'page_title': 'Bulletins',
        'active': 'notes',
    }
    return render(request, 'notes/bulletins/liste.html', context)


def _calcul_bulletin(eleve, evaluations, notes_dict=None):
    """Calcule les lignes + moyenne générale pour un élève donné.

    notes_dict : {evaluation_id: Note} pré-chargé en dehors (évite N+1 sur les appels en lot).
    Si absent, une requête est faite ici (cas single-élève : bulletin_detail).
    """
    if notes_dict is None:
        notes_dict = {
            n.evaluation_id: n
            for n in Note.objects.filter(evaluation__in=evaluations, eleve=eleve)
        }
    matieres_data = {}
    for ev in evaluations:
        m = ev.matiere
        if m.id not in matieres_data:
            matieres_data[m.id] = {
                'matiere': m, 'notes': [],
                'total_points': Decimal('0'), 'total_coeff': 0,
                'moyenne': None, 'coefficient': m.coefficient,
            }
        note = notes_dict.get(ev.pk)
        if note and not note.absent:
            note_max = ev.note_max if ev.note_max else Decimal('20')
            matieres_data[m.id]['notes'].append({
                'evaluation': ev, 'note': note,
                'sur_20': round(note.valeur * 20 / note_max, 2),
            })
            matieres_data[m.id]['total_points'] += note.valeur * ev.coefficient
            matieres_data[m.id]['total_coeff'] += ev.coefficient * int(note_max)
        else:
            matieres_data[m.id]['notes'].append({'evaluation': ev, 'note': note, 'sur_20': None})

    total_points_gen = Decimal('0')
    total_coeff_gen = Decimal('0')
    lignes = []
    for data in matieres_data.values():
        if data['total_coeff'] > 0:
            moy = round(data['total_points'] * 20 / data['total_coeff'], 2)
            data['moyenne'] = moy
            total_points_gen += moy * data['coefficient']
            total_coeff_gen += data['coefficient']
        lignes.append(data)

    max_notes = max((len(d['notes']) for d in lignes), default=0)
    for data in lignes:
        data['padding'] = range(max_notes - len(data['notes']))

    moyenne_generale = round(total_points_gen / total_coeff_gen, 2) if total_coeff_gen else None
    return lignes, moyenne_generale


@acces_requis("notes")
def bulletins_imprimer_classe(request, classe_id, periode):
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and int(classe_id) not in classes_ids:
        messages.error(request, "Vous n'avez pas accès aux bulletins de cette classe.")
        return redirect('notes:bulletins_liste')
    classe = get_object_or_404(Classe, pk=classe_id)
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    eleves = list(Eleve.objects.filter(classe=classe, statut='actif').order_by('nom', 'prenom'))

    evaluations = list(
        Evaluation.objects.filter(classe=classe, periode=periode, annee_scolaire=annee)
        .select_related('matiere').order_by('matiere__nom')
    )

    # Charger TOUTES les notes en une seule requête, puis distribuer par élève
    toutes_notes = Note.objects.filter(evaluation__in=evaluations).select_related('eleve')
    notes_par_eleve = {}
    for n in toutes_notes:
        notes_par_eleve.setdefault(n.eleve_id, {})[n.evaluation_id] = n

    bulletins_data = []
    moyennes_map = {}
    for eleve in eleves:
        lignes, moy = _calcul_bulletin(eleve, evaluations, notes_par_eleve.get(eleve.pk, {}))
        moyennes_map[eleve.pk] = moy
        bulletin, _ = Bulletin.objects.update_or_create(
            eleve=eleve, annee_scolaire=annee, periode=periode,
            defaults={'moyenne_generale': moy}
        )
        bulletins_data.append({'eleve': eleve, 'lignes': lignes, 'moyenne_generale': moy, 'bulletin': bulletin})

    # Rangs globaux sur la classe
    sorted_ids = [eid for eid, _ in sorted(
        ((eid, m) for eid, m in moyennes_map.items() if m is not None),
        key=lambda x: x[1], reverse=True
    )]
    rang_map = {eid: i + 1 for i, eid in enumerate(sorted_ids)}
    total_eleves = len(eleves)
    for bd in bulletins_data:
        bd['rang'] = rang_map.get(bd['eleve'].pk)
        bd['bulletin'].rang = bd['rang']
        bd['bulletin'].save()

    context = {
        'classe': classe,
        'annee': annee,
        'periode': periode,
        'periode_display': dict(Evaluation.periode.field.choices).get(periode, periode),
        'bulletins_data': bulletins_data,
        'total_eleves': total_eleves,
        'page_title': f'Bulletins — {classe.nom}',
        'active': 'notes',
    }
    return render(request, 'notes/bulletins/impression_classe.html', context)


@acces_requis("notes")
def bulletin_detail(request, eleve_id, periode):
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and eleve.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès au bulletin de cet élève.")
        return redirect('notes:bulletins_liste')
    annee = AnneeScolaire.objects.filter(en_cours=True).first()

    evaluations = list(
        Evaluation.objects.filter(classe=eleve.classe, periode=periode, annee_scolaire=annee)
        .select_related('matiere').order_by('matiere__nom')
    )

    lignes, moyenne_generale = _calcul_bulletin(eleve, evaluations)

    bulletin, _ = Bulletin.objects.update_or_create(
        eleve=eleve, annee_scolaire=annee, periode=periode,
        defaults={'moyenne_generale': moyenne_generale}
    )

    # Calcul du rang — sécurisé contre ValueError
    eleves_classe = Eleve.objects.filter(classe=eleve.classe, statut='actif')
    bulletins_classe = list(
        Bulletin.objects.filter(eleve__in=eleves_classe, annee_scolaire=annee, periode=periode)
        .order_by('-moyenne_generale')
        .values_list('eleve_id', flat=True)
    )
    try:
        rang = bulletins_classe.index(eleve.pk) + 1
    except ValueError:
        rang = None
    bulletin.rang = rang
    bulletin.save()

    context = {
        'eleve': eleve,
        'annee': annee,
        'periode': periode,
        'periode_display': dict(Evaluation.periode.field.choices).get(periode, periode),
        'lignes': lignes,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'total_eleves': eleves_classe.count(),
        'bulletin': bulletin,
        'page_title': f'Bulletin — {eleve.nom_complet()}',
        'active': 'notes',
    }
    return render(request, 'notes/bulletins/detail.html', context)


@acces_requis("notes")
def bulletin_pdf(request, eleve_id, periode):
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and eleve.classe_id not in classes_ids:
        messages.error(request, "Vous n'avez pas accès au bulletin de cet élève.")
        return redirect('notes:bulletins_liste')
    annee = AnneeScolaire.objects.filter(en_cours=True).first()

    evaluations = list(
        Evaluation.objects.filter(classe=eleve.classe, periode=periode, annee_scolaire=annee)
        .select_related('matiere').order_by('matiere__nom')
    )
    lignes, moyenne_generale = _calcul_bulletin(eleve, evaluations)

    bulletin, _ = Bulletin.objects.update_or_create(
        eleve=eleve, annee_scolaire=annee, periode=periode,
        defaults={'moyenne_generale': moyenne_generale}
    )
    eleves_classe = Eleve.objects.filter(classe=eleve.classe, statut='actif')
    bulletins_classe = list(
        Bulletin.objects.filter(eleve__in=eleves_classe, annee_scolaire=annee, periode=periode)
        .order_by('-moyenne_generale').values_list('eleve_id', flat=True)
    )
    try:
        rang = bulletins_classe.index(eleve.pk) + 1
    except ValueError:
        rang = None

    from eleves.context_processors import groupe_scolaire
    groupe_ctx = groupe_scolaire(request)

    context = {
        'eleve': eleve,
        'annee': annee,
        'periode': periode,
        'periode_display': dict(Evaluation.periode.field.choices).get(periode, periode),
        'lignes': lignes,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'total_eleves': eleves_classe.count(),
        'bulletin': bulletin,
        **groupe_ctx,
    }

    pdf_bytes = _render_pdf('notes/bulletins/bulletin_pdf.html', context)
    nom_fichier = f"bulletin_{eleve.matricule}_{periode}.pdf"
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    return response


