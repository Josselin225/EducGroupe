from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from eleves.models import ConnexionLog


class Command(BaseCommand):
    help = "Supprime les entrées du journal d'activité plus anciennes que N jours (90 par défaut)."

    def add_arguments(self, parser):
        parser.add_argument('--jours', type=int, default=90, help='Ancienneté en jours au-delà de laquelle purger.')

    def handle(self, *args, **options):
        jours = options['jours']
        seuil = timezone.now() - timedelta(days=jours)
        nb_supprimees, _ = ConnexionLog.objects.filter(date__lt=seuil).delete()
        self.stdout.write(self.style.SUCCESS(
            f"{nb_supprimees} entrée(s) de plus de {jours} jours supprimée(s) du journal d'activité."
        ))
