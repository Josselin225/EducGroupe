from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from eleves.permissions import acces_requis, get_classes_enseignant, get_role
from django.contrib import messages
from .models import Cours, CreneauHoraire, Salle, JOURS
from .forms import CoursForm, CreneauForm
from eleves.models import Classe, AnneeScolaire, Ecole


JOURS_DICT = dict(JOURS)


@acces_requis("emploi_du_temps")
def index(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('ecole', 'niveau') if annee else []
    classes_ids = get_classes_enseignant(request.user)
    if classes_ids is not None and annee:
        classes = classes.filter(pk__in=classes_ids)
    classe_id = request.GET.get('classe')
    classe_selectionnee = None
    grille = {}

    creneaux = CreneauHoraire.objects.all().order_by('heure_debut')

    if classe_id:
        classe_selectionnee = get_object_or_404(Classe, pk=classe_id)
        cours_qs = Cours.objects.filter(classe=classe_selectionnee).select_related(
            'matiere', 'enseignant', 'creneau', 'salle'
        )
        for cours in cours_qs:
            grille.setdefault(cours.creneau_id, {})[cours.jour] = cours

    # Construire les lignes sous forme de liste exploitable dans le template
    grille_rows = []
    for creneau in creneaux:
        cells = []
        for jour_num, jour_label in JOURS:
            cours = grille.get(creneau.pk, {}).get(jour_num)
            cells.append({'jour': jour_num, 'cours': cours})
        grille_rows.append({'creneau': creneau, 'cells': cells})

    jours = JOURS
    context = {
        'annee': annee,
        'classes': classes,
        'classe_selectionnee': classe_selectionnee,
        'creneaux': creneaux,
        'jours': jours,
        'grille_rows': grille_rows,
        'page_title': 'Emploi du temps',
        'active': 'emploi_du_temps',
    }
    return render(request, 'emploi_du_temps/index.html', context)


def detecter_chevauchement(form, instance=None):
    """Vérifie qu'un enseignant n'est pas dans 2 classes au même créneau."""
    enseignant = form.cleaned_data.get('enseignant')
    jour = form.cleaned_data.get('jour')
    creneau = form.cleaned_data.get('creneau')
    if enseignant and jour and creneau:
        qs = Cours.objects.filter(enseignant=enseignant, jour=jour, creneau=creneau)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            autre = qs.first()
            return f"{enseignant} enseigne déjà {autre.matiere} en {autre.classe} à ce créneau."
    return None


@acces_requis("emploi_du_temps")
def cours_ajouter(request):
    if get_role(request.user) == 'enseignant':
        messages.error(request, "Les enseignants ne peuvent pas modifier l'emploi du temps.")
        return redirect('emploi_du_temps:index')
    form = CoursForm(request.POST or None)
    if form.is_valid():
        conflit = detecter_chevauchement(form)
        if conflit:
            messages.warning(request, f'Chevauchement détecté : {conflit}')
        try:
            form.save()
            messages.success(request, 'Cours ajouté.')
            return redirect('emploi_du_temps:index')
        except Exception:
            messages.error(request, 'Ce créneau est déjà occupé pour cette classe.')
    context = {'form': form, 'page_title': 'Ajouter un cours', 'active': 'emploi_du_temps'}
    return render(request, 'emploi_du_temps/cours_form.html', context)


@acces_requis("emploi_du_temps")
def cours_modifier(request, pk):
    if get_role(request.user) == 'enseignant':
        messages.error(request, "Les enseignants ne peuvent pas modifier l'emploi du temps.")
        return redirect('emploi_du_temps:index')
    cours = get_object_or_404(Cours, pk=pk)
    form = CoursForm(request.POST or None, instance=cours)
    if form.is_valid():
        conflit = detecter_chevauchement(form, instance=cours)
        if conflit:
            messages.warning(request, f'Chevauchement détecté : {conflit}')
        form.save()
        messages.success(request, 'Cours modifié.')
        return redirect('emploi_du_temps:index')
    context = {'form': form, 'cours': cours, 'page_title': 'Modifier le cours', 'active': 'emploi_du_temps'}
    return render(request, 'emploi_du_temps/cours_form.html', context)


@acces_requis("emploi_du_temps")
def cours_supprimer(request, pk):
    if get_role(request.user) == 'enseignant':
        messages.error(request, "Les enseignants ne peuvent pas modifier l'emploi du temps.")
        return redirect('emploi_du_temps:index')
    cours = get_object_or_404(Cours, pk=pk)
    if request.method == 'POST':
        cours.delete()
        messages.success(request, 'Cours supprimé.')
    return redirect('emploi_du_temps:index')




@acces_requis("emploi_du_temps")
def creneaux_liste(request):
    creneaux = CreneauHoraire.objects.all().order_by('heure_debut')
    form = CreneauForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Créneau ajouté.')
        return redirect('emploi_du_temps:creneaux')
    context = {'creneaux': creneaux, 'form': form, 'page_title': 'Créneaux horaires', 'active': 'emploi_du_temps'}
    return render(request, 'emploi_du_temps/creneaux.html', context)
