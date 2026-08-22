from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


def _get_ip(request):
    if request is None:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def _get_ua(request):
    if request is None:
        return ''
    return request.META.get('HTTP_USER_AGENT', '')[:300]


@receiver(user_logged_in)
def log_connexion(sender, request, user, **kwargs):
    from eleves.models import ConnexionLog
    ConnexionLog.objects.create(
        user=user,
        username_tente=user.username,
        type_event='connexion',
        ip=_get_ip(request),
        user_agent=_get_ua(request),
    )


@receiver(user_logged_out)
def log_deconnexion(sender, request, user, **kwargs):
    from eleves.models import ConnexionLog
    if user:
        ConnexionLog.objects.create(
            user=user,
            username_tente=user.username,
            type_event='deconnexion',
            ip=_get_ip(request),
            user_agent=_get_ua(request),
        )


@receiver(user_login_failed)
def log_echec(sender, credentials, request, **kwargs):
    from eleves.models import ConnexionLog
    ConnexionLog.objects.create(
        username_tente=credentials.get('username', '')[:150],
        type_event='echec',
        ip=_get_ip(request),
        user_agent=_get_ua(request),
    )
