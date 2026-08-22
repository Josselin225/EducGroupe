from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
STATUT_CHOICES = [('actif', 'Actif'), ('inactif', 'Inactif'), ('transfere', 'Transféré')]
CYCLE_CHOICES = [('maternelle', 'Maternelle'), ('primaire', 'Primaire')]
TYPE_ECOLE_CHOICES = [
    ('maternelle', 'Maternelle'),
    ('primaire', 'Primaire'),
    ('mixte', 'Maternelle + Primaire'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True)
    poste = models.CharField(max_length=100, blank=True, verbose_name='Poste / Fonction')

    def __str__(self):
        return f"Profil de {self.user.username}"

    class Meta:
        verbose_name = "Profil utilisateur"


@receiver(post_save, sender=User)
def creer_profil(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def sauvegarder_profil(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class GroupeScolaire(models.Model):
    nom = models.CharField(max_length=200, default='Groupe Scolaire')
    sigle = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)
    logo = models.ImageField(upload_to='groupe/logo/', blank=True, null=True)
    devise = models.CharField(max_length=200, blank=True, help_text='Slogan ou devise')
    bp = models.CharField(max_length=50, blank=True, verbose_name='Boîte postale')
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, default="Côte d'Ivoire")
    support_nom = models.CharField(max_length=150, blank=True, verbose_name='Support technique — Nom')
    support_telephone = models.CharField(max_length=60, blank=True, verbose_name='Support technique — Téléphone')
    support_whatsapp = models.CharField(max_length=30, blank=True, verbose_name='Support technique — WhatsApp')
    support_email = models.EmailField(blank=True, verbose_name='Support technique — Email')

    def __str__(self):
        return self.nom

    def support_telephones(self):
        import re
        numeros = [t.strip() for t in re.split(r'[/,;]| et ', self.support_telephone) if t.strip()]
        return [n if n.startswith('+') else f'+225 {n}' for n in numeros]

    def support_whatsapp_lien(self):
        import re
        numero = re.sub(r'\D', '', self.support_whatsapp)
        if not numero:
            return ''
        if numero.startswith('225'):
            return numero
        return '225' + numero.lstrip('0')

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = "Groupe scolaire"


class AnneeScolaire(models.Model):
    libelle = models.CharField(max_length=20, unique=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    en_cours = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.en_cours:
            AnneeScolaire.objects.exclude(pk=self.pk).update(en_cours=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.libelle

    class Meta:
        verbose_name = "Année scolaire"
        verbose_name_plural = "Années scolaires"
        ordering = ['-date_debut']


class Ecole(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.TextField(blank=True)
    directeur = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    type_ecole = models.CharField(max_length=20, choices=TYPE_ECOLE_CHOICES, default='mixte')

    def __str__(self):
        return self.nom

    def nb_classes(self):
        return self.classes.count()

    def nb_eleves(self):
        return Eleve.objects.filter(classe__ecole=self, statut='actif').count()

    class Meta:
        verbose_name = "École"
        verbose_name_plural = "Écoles"
        ordering = ['nom']


class Niveau(models.Model):
    nom = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True, default='')
    cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, default='primaire')
    ordre = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Niveau"
        ordering = ['ordre']


class Classe(models.Model):
    nom = models.CharField(max_length=50)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='classes')
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='classes', null=True, blank=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='classes')
    capacite_max = models.PositiveSmallIntegerField(default=40)
    enseignant_principal = models.ForeignKey(
        'enseignants.Enseignant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='classes_principales',
        verbose_name='Enseignant principal',
        help_text='Maternelle/Primaire : enseignant qui enseigne toutes les matières'
    )

    def effectif(self):
        return self.eleves.filter(statut='actif').count()

    def __str__(self):
        ecole = f" - {self.ecole}" if self.ecole else ""
        return f"{self.nom}{ecole} ({self.annee_scolaire})"

    class Meta:
        verbose_name = "Classe"
        unique_together = ('nom', 'ecole', 'annee_scolaire')
        ordering = ['ecole', 'niveau__ordre', 'nom']


class Eleve(models.Model):
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100, blank=True)
    adresse = models.TextField(blank=True)
    telephone_parent = models.CharField(max_length=20, blank=True)
    nom_parent = models.CharField(max_length=200, blank=True)
    email_parent = models.EmailField(blank=True)
    photo = models.ImageField(upload_to='eleves/photos/', blank=True, null=True)
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, related_name='eleves')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif', db_index=True)
    date_inscription = models.DateField(auto_now_add=True)
    observations = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.matricule})"

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
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['nom', 'prenom']


class ConnexionLog(models.Model):
    TYPE_CHOICES = [
        ('connexion', 'Connexion réussie'),
        ('deconnexion', 'Déconnexion'),
        ('echec', 'Tentative échouée'),
        ('consultation', 'Consultation'),
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='connexion_logs')
    username_tente = models.CharField(max_length=150, blank=True)
    type_event = models.CharField(max_length=20, choices=TYPE_CHOICES)
    path = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.type_event} — {self.user or self.username_tente} — {self.date}"

    def navigateur_simplifie(self):
        ua = self.user_agent
        if not ua:
            return ''
        if 'Edg/' in ua:
            navigateur = 'Edge'
        elif 'OPR/' in ua or 'Opera' in ua:
            navigateur = 'Opera'
        elif 'Firefox/' in ua:
            navigateur = 'Firefox'
        elif 'Chrome/' in ua:
            navigateur = 'Chrome'
        elif 'Safari/' in ua:
            navigateur = 'Safari'
        else:
            navigateur = 'Autre'

        if 'Android' in ua:
            os_nom = 'Android'
        elif 'iPhone' in ua or 'iPad' in ua:
            os_nom = 'iOS'
        elif 'Windows' in ua:
            os_nom = 'Windows'
        elif 'Mac OS X' in ua:
            os_nom = 'macOS'
        elif 'Linux' in ua:
            os_nom = 'Linux'
        else:
            os_nom = ''

        return f"{navigateur} sur {os_nom}" if os_nom else navigateur

    class Meta:
        verbose_name = "Journal de connexion"
        verbose_name_plural = "Journal des connexions"
        ordering = ['-date']
