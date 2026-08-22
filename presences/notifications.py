from django.core.mail import send_mail
from django.conf import settings

_LABELS = {
    'absent': 'absent(e)',
    'retard': 'en retard',
    'excuse': 'absent(e) excusé(e)',
}


def notifier_absence(eleve, date, statut, motif=''):
    email = (getattr(eleve, 'email_parent', '') or '').strip()
    if not email or statut not in _LABELS:
        return
    label = _LABELS[statut]
    date_fr = date.strftime('%d/%m/%Y')
    sujet = f"[Les Palmiers] Présence de {eleve.prenom} {eleve.nom} — {date_fr}"
    corps = (
        f"Bonjour,\n\n"
        f"Nous vous informons que {eleve.prenom} {eleve.nom} "
        f"(Classe : {eleve.classe}) a été signalé(e) {label} le {date_fr}.\n"
    )
    if motif:
        corps += f"\nMotif : {motif}\n"
    corps += (
        "\nSi vous avez des questions, veuillez contacter l'établissement.\n\n"
        "Cordialement,\nGroupe Scolaire Les Palmiers"
    )
    try:
        send_mail(
            sujet, corps,
            settings.DEFAULT_FROM_EMAIL, [email],
            fail_silently=True,
        )
    except Exception:
        pass
