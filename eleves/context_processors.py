from django.core.cache import cache
from .models import GroupeScolaire, AnneeScolaire
from .permissions import get_role, peut_acceder, ROLES, get_classes_enseignant


def groupe_scolaire(request):
    groupe = cache.get('groupe_scolaire')
    if groupe is None:
        groupe = GroupeScolaire.get()
        cache.set('groupe_scolaire', groupe, 600)
    return {'groupe': groupe}


def notifications(request):
    if not request.user.is_authenticated:
        return {'notifications': []}

    from django.utils import timezone
    from presences.models import Presence
    from enseignants.models import Enseignant

    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    classes_ids = get_classes_enseignant(request.user)
    est_enseignant = classes_ids is not None
    aujourd_hui = timezone.localdate()

    alertes = []
    if not annee:
        alertes.append({
            'type': 'danger', 'icon': 'fa-calendar-times',
            'msg': 'Aucune année scolaire active — veuillez en activer une.',
            'url': '/annees/',
        })

    presences_qs = Presence.objects.filter(date=aujourd_hui, cours__isnull=True, statut='absent')
    if est_enseignant:
        presences_qs = presences_qs.filter(eleve__classe__in=classes_ids)
    absents_jour = presences_qs.count()
    if absents_jour > 0:
        alertes.append({
            'type': 'warning', 'icon': 'fa-user-times',
            'msg': f"{absents_jour} élève(s) absent(s) aujourd'hui.",
            'url': '/presences/',
        })

    if not est_enseignant and annee:
        from paiements.models import Facture
        nb_impayes = Facture.objects.filter(annee_scolaire=annee, statut__in=['en_attente', 'partiel']).count()
        if nb_impayes > 0:
            alertes.append({
                'type': 'info', 'icon': 'fa-file-invoice-dollar',
                'msg': f'{nb_impayes} facture(s) en attente ou partiellement payée(s).',
                'url': '/paiements/factures/?statut=en_attente',
            })

    if not est_enseignant:
        sans_compte = Enseignant.objects.filter(statut='actif', user__isnull=True).count()
        if sans_compte:
            alertes.append({
                'type': 'warning', 'icon': 'fa-user-lock',
                'msg': f'{sans_compte} enseignant(s) sans compte utilisateur.',
                'url': '/enseignants/',
            })

    return {'notifications': alertes}


def user_role(request):
    if not request.user.is_authenticated:
        return {'user_role': None, 'user_role_label': ''}
    role = get_role(request.user)
    return {
        'user_role': role,
        'user_role_label': ROLES.get(role, role.capitalize()),
    }
