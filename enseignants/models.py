from django.db import models
from django.contrib.auth.models import User

STATUT_CHOICES = [('actif', 'Actif'), ('inactif', 'Inactif'), ('conge', 'En congé')]

class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    coefficient = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom} (coef. {self.coefficient})"

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ['nom']


class Enseignant(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='enseignant')
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    date_naissance = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    specialite = models.CharField(max_length=100, blank=True)
    matieres = models.ManyToManyField(Matiere, related_name='enseignants', blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    photo = models.ImageField(upload_to='enseignants/photos/', blank=True, null=True)
    observations = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    def nom_complet(self):
        return f"{self.nom} {self.prenom}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.photo:
            self._resize_photo(self.photo.path, max_size=800)

    @staticmethod
    def _resize_photo(path, max_size=800):
        try:
            from PIL import Image
            img = Image.open(path)
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.LANCZOS)
                img.save(path, optimize=True, quality=85)
        except Exception:
            pass

    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        ordering = ['nom', 'prenom']
