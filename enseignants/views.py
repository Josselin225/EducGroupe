from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from eleves.permissions import acces_requis
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.utils.text import slugify
from .models import Enseignant, Matiere
from .forms import EnseignantForm, MatiereForm


def _creer_ou_lier_compte(enseignant, mot_de_passe=None):
    """
    Crée un compte User pour cet enseignant s'il n'en a pas.
    Retourne (user, mot_de_passe_en_clair) ou (user_existant, None).
    """
    groupe, _ = Group.objects.get_or_create(name='Enseignant')
    if enseignant.user:
        enseignant.user.groups.add(groupe)
        return enseignant.user, None

    username = slugify(enseignant.matricule)
    # Rendre l'username unique si nécessaire
    base, i = username, 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{i}"
        i += 1

    pwd = mot_de_passe or enseignant.matricule
    user = User.objects.create_user(
        username=username,
        password=pwd,
        first_name=enseignant.prenom,
        last_name=enseignant.nom,
        email=enseignant.email,
    )
    user.groups.add(groupe)
    enseignant.user = user
    enseignant.save(update_fields=['user'])
    return user, pwd


@acces_requis("enseignants")
def index(request):
    enseignants = Enseignant.objects.prefetch_related('matieres').select_related('user').filter(statut='actif')
    sans_compte = enseignants.filter(user__isnull=True).count()
    context = {
        'enseignants': enseignants,
        'total': enseignants.count(),
        'total_hommes': enseignants.filter(sexe='M').count(),
        'total_femmes': enseignants.filter(sexe='F').count(),
        'sans_compte': sans_compte,
        'page_title': 'Enseignants',
        'active': 'enseignants',
    }
    return render(request, 'enseignants/index.html', context)


@acces_requis("enseignants")
def initialiser_comptes(request):
    """Crée les comptes manquants pour tous les enseignants actifs."""
    if request.method != 'POST':
        return redirect('enseignants:index')
    enseignants_sans_compte = Enseignant.objects.filter(statut='actif', user__isnull=True)
    crees = []
    for enseignant in enseignants_sans_compte:
        user, pwd = _creer_ou_lier_compte(enseignant)
        if pwd:
            crees.append(f'{enseignant.nom_complet()} → {user.username}')
    if crees:
        messages.success(
            request,
            f'{len(crees)} compte(s) créé(s) : ' + ' — '.join(crees) +
            ' (mot de passe initial = matricule, à transmettre en mains propres)'
        )
    else:
        messages.info(request, 'Tous les enseignants actifs ont déjà un compte.')
    return redirect('enseignants:index')


@acces_requis("enseignants")
def enseignant_ajouter(request):
    form = EnseignantForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        enseignant = form.save()
        user, pwd = _creer_ou_lier_compte(enseignant)
        messages.success(
            request,
            f'Enseignant ajouté. Compte créé — Identifiant : {user.username} '
            f'(mot de passe initial = matricule, à transmettre en mains propres)'
        )
        return redirect('enseignants:detail', pk=enseignant.pk)
    return render(request, 'enseignants/form.html',
                  {'form': form, 'page_title': 'Nouvel enseignant', 'active': 'enseignants'})


@acces_requis("enseignants")
def enseignant_modifier(request, pk):
    enseignant = get_object_or_404(Enseignant, pk=pk)
    form = EnseignantForm(request.POST or None, request.FILES or None, instance=enseignant)
    if form.is_valid():
        form.save()
        messages.success(request, 'Enseignant modifié.')
        return redirect('enseignants:index')
    return render(request, 'enseignants/form.html',
                  {'form': form, 'enseignant': enseignant,
                   'page_title': f'Modifier — {enseignant.nom_complet()}', 'active': 'enseignants'})


@acces_requis("enseignants")
def enseignant_desactiver(request, pk):
    enseignant = get_object_or_404(Enseignant, pk=pk)
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut', 'inactif')
        enseignant.statut = nouveau_statut
        enseignant.save()
        messages.success(request, f'Statut de {enseignant.nom_complet()} mis à jour.')
    return redirect('enseignants:index')


@acces_requis("enseignants")
def enseignant_detail(request, pk):
    enseignant = get_object_or_404(Enseignant, pk=pk)
    cours = enseignant.cours.select_related('classe__ecole', 'matiere').order_by('jour', 'creneau__heure_debut')
    context = {
        'enseignant': enseignant,
        'cours': cours,
        'page_title': enseignant.nom_complet(),
        'active': 'enseignants',
    }
    return render(request, 'enseignants/detail.html', context)


# ──────────────────────────────────────────────
# MATIÈRES
# ──────────────────────────────────────────────

@acces_requis("enseignants")
def matieres_liste(request):
    matieres = Matiere.objects.all()
    return render(request, 'enseignants/matieres/liste.html',
                  {'matieres': matieres, 'page_title': 'Matières', 'active': 'matieres'})


@acces_requis("enseignants")
def matiere_ajouter(request):
    next_url = request.GET.get('next', '')
    form = MatiereForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Matière ajoutée.')
        return redirect(next_url or 'enseignants:matieres_liste')
    return render(request, 'enseignants/matieres/form.html',
                  {'form': form, 'page_title': 'Nouvelle matière', 'active': 'matieres'})


@acces_requis("enseignants")
def gerer_compte(request, pk):
    enseignant = get_object_or_404(Enseignant, pk=pk)
    if request.method != 'POST':
        return redirect('enseignants:detail', pk=pk)

    action = request.POST.get('action')

    if action == 'creer':
        user, pwd = _creer_ou_lier_compte(enseignant)
        if pwd:
            messages.success(
                request,
                f'Compte créé — Identifiant : {user.username} '
                f'(mot de passe initial = matricule, à transmettre en mains propres)'
            )
        else:
            messages.info(request, f'Ce compte existe déjà ({user.username}).')

    elif action == 'reinitialiser':
        if enseignant.user:
            enseignant.user.set_password(enseignant.matricule)
            enseignant.user.save()
            messages.success(
                request,
                f'Mot de passe réinitialisé pour {enseignant.user.username} '
                f'(nouveau mot de passe = matricule, à transmettre en mains propres)'
            )
        else:
            messages.error(request, 'Aucun compte lié à cet enseignant.')

    elif action == 'activer':
        if enseignant.user:
            enseignant.user.is_active = True
            enseignant.user.save()
            messages.success(request, 'Compte activé.')
    elif action == 'desactiver':
        if enseignant.user:
            enseignant.user.is_active = False
            enseignant.user.save()
            messages.success(request, 'Compte désactivé.')

    return redirect('enseignants:detail', pk=pk)


@acces_requis("enseignants")
def carte_professionnelle(request, pk):
    enseignant = get_object_or_404(Enseignant, pk=pk)
    annee = __import__('eleves.models', fromlist=['AnneeScolaire']).AnneeScolaire.objects.filter(en_cours=True).first()
    context = {
        'enseignant': enseignant,
        'annee': annee,
        'page_title': f'Carte — {enseignant.nom_complet()}',
        'active': 'enseignants',
    }
    return render(request, 'enseignants/carte_professionnelle.html', context)


@acces_requis("enseignants")
def matiere_modifier(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    form = MatiereForm(request.POST or None, instance=matiere)
    if form.is_valid():
        form.save()
        messages.success(request, 'Matière modifiée.')
        return redirect('enseignants:matieres_liste')
    return render(request, 'enseignants/matieres/form.html',
                  {'form': form, 'matiere': matiere,
                   'page_title': f'Modifier — {matiere.nom}', 'active': 'matieres'})
