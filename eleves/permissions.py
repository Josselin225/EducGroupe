import logging
from functools import wraps
from django.shortcuts import redirect
from django.http import Http404
from django.contrib import messages

security_log = logging.getLogger('edugroupe.security')

ROLES = {
    'directeur':   'Directeur',
    'secretaire':  'Secrétaire',
    'enseignant':  'Enseignant',
    'comptable':   'Comptable',
}

# Droits par rôle : (lecture, écriture) par module
ACCES_MODULE = {
    'directeur':  ['*'],
    'secretaire': ['eleves', 'presences', 'paiements', 'rapports', 'annees', 'ecoles', 'classes', 'emploi_du_temps'],
    'enseignant': ['notes', 'presences', 'emploi_du_temps', 'eleves'],
    'comptable':  ['paiements', 'rapports'],
}

# Modules en lecture seule pour chaque rôle
LECTURE_SEULE = {
    'secretaire': ['rapports'],
    'enseignant': ['eleves'],
    'comptable':  ['rapports'],
}


def get_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return 'directeur'
    for role in ('directeur', 'secretaire', 'enseignant', 'comptable'):
        if user.groups.filter(name=ROLES[role]).exists():
            return role
    return 'secretaire'  # rôle par défaut


def acces_requis(*modules, ecriture=False):
    """Décorateur : vérifie que l'utilisateur a accès au module."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'/accounts/login/?next={request.path}')
            role = get_role(request.user)
            acces = ACCES_MODULE.get(role, [])
            lecture_seule = LECTURE_SEULE.get(role, [])
            for module in modules:
                if '*' not in acces and module not in acces:
                    security_log.warning(
                        f"ACCÈS REFUSÉ user={request.user.username} role={role} "
                        f"module={module} path={request.path}"
                    )
                    messages.error(request, "Vous n'avez pas accès à cette section.")
                    return redirect('/')
                if ecriture and module in lecture_seule:
                    messages.error(request, "Vous n'avez pas les droits de modification.")
                    return redirect('/')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Alias pratiques
def directeur_requis(view_func):
    return acces_requis('*')(view_func)


def peut_acceder(user, module):
    if not user.is_authenticated:
        return False
    role = get_role(user)
    acces = ACCES_MODULE.get(role, [])
    return '*' in acces or module in acces


def get_enseignant(user):
    """Retourne l'objet Enseignant lié à cet utilisateur, ou None."""
    try:
        return user.enseignant
    except Exception:
        return None


def get_classes_enseignant(user):
    """
    Pour un utilisateur avec le rôle 'enseignant', retourne la liste des IDs
    de classes dont il est l'enseignant principal.
    Retourne None si l'utilisateur n'est PAS enseignant (= aucune restriction).
    Retourne [] si l'utilisateur est enseignant mais n'a aucune classe.
    """
    if get_role(user) != 'enseignant':
        return None
    enseignant = get_enseignant(user)
    if enseignant is None:
        return []
    from eleves.models import Classe
    return list(
        Classe.objects.filter(enseignant_principal=enseignant)
        .values_list('pk', flat=True)
    )
