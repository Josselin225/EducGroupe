from django.apps import AppConfig


class ElevesConfig(AppConfig):
    name = 'eleves'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(creer_groupes_roles, sender=self)
        import eleves.signals  # noqa: F401 — connects auth signals


def creer_groupes_roles(sender, **kwargs):
    from django.contrib.auth.models import Group
    roles = ['Directeur', 'Secrétaire', 'Enseignant', 'Comptable']
    for nom in roles:
        Group.objects.get_or_create(name=nom)
