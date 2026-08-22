from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE_MB = 3
MAX_FILE_SIZE_MB = 5

# Signatures de fichiers valides (magic bytes)
IMAGE_SIGNATURES = {
    b'\xff\xd8\xff': 'JPEG',
    b'\x89PNG\r\n\x1a\n': 'PNG',
    b'RIFF': 'WebP',      # WebP commence par RIFF....WEBP
    b'GIF87a': 'GIF',
    b'GIF89a': 'GIF',
}

DOCUMENT_SIGNATURES = {
    b'%PDF': 'PDF',
    b'\xff\xd8\xff': 'JPEG',
    b'\x89PNG': 'PNG',
}


def _lire_magic(fichier, n=8):
    """Lit les n premiers octets du fichier sans consommer le flux."""
    signature = fichier.read(n)
    fichier.seek(0)
    return signature


def valider_image(fichier):
    if not fichier:
        return
    if fichier.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f'La photo ne doit pas dépasser {MAX_IMAGE_SIZE_MB} Mo.')

    magic = _lire_magic(fichier)
    valide = any(magic.startswith(sig) for sig in IMAGE_SIGNATURES)

    # WebP : vaut RIFF....WEBP
    if magic.startswith(b'RIFF') and b'WEBP' not in fichier.read(12):
        valide = False
        fichier.seek(0)

    if not valide:
        raise ValidationError(
            'Fichier image non valide. Seuls les formats JPG, PNG, WebP et GIF sont acceptés.'
        )


def valider_justificatif(fichier):
    if not fichier:
        return
    if fichier.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f'Le fichier ne doit pas dépasser {MAX_FILE_SIZE_MB} Mo.')

    magic = _lire_magic(fichier)
    valide = any(magic.startswith(sig) for sig in DOCUMENT_SIGNATURES)
    if not valide:
        raise ValidationError('Type de fichier non accepté. Seuls JPG, PNG et PDF sont acceptés.')
