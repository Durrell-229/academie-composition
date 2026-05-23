import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrateur')
        CONSEILLER = 'conseiller', _('Conseiller Pédagogique')
        PROFESSEUR = 'professeur', _('Professeur')
        ELEVE = 'eleve', _('Élève / Étudiant')

    class TypeCandidat(models.TextChoices):
        ACADEMIE = 'academie', _('Candidat Académie Numérique')
        LIBRE = 'libre', _('Candidat Libre')
        NON_DEFINI = 'non_defini', _('Non défini')

    class Niveau(models.TextChoices):
        PRIMAIRE = 'primaire', _('Primaire')
        SECONDAIRE = 'secondaire', _('Secondaire')
        UNIVERSITAIRE = 'universitaire', _('Universitaire')
        PROFESSIONNEL = 'professionnel', _('Formation Professionnelle')
        ENTREPRISE = 'entreprise', _('Entreprise')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('adresse email'), unique=True)
    first_name = models.CharField(_('prénom'), max_length=150)
    last_name = models.CharField(_('nom'), max_length=150)
    phone = models.CharField(_('téléphone'), max_length=30, blank=True)
    country = models.CharField(_('pays'), max_length=100, default='France')
    role = models.CharField(_('rôle'), max_length=20, choices=Role.choices, default=Role.ELEVE, db_index=True)
    niveau = models.CharField(_('niveau'), max_length=30, choices=Niveau.choices, default=Niveau.SECONDAIRE)
    classe = models.CharField(_('classe / promotion'), max_length=100, blank=True)
    matricule = models.CharField(_('matricule'), max_length=50, blank=True, unique=True, null=True)
    avatar = models.ImageField(_('photo de profil'), upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(_('biographie'), blank=True)
    sexe = models.CharField(_('sexe'), max_length=10, blank=True, default='',
                            choices=[('Masculin', 'Masculin'), ('Féminin', 'Féminin')])
    xp = models.PositiveIntegerField(_('XP'), default=0)
    type_candidat = models.CharField(
        _('type de candidat'),
        max_length=20,
        choices=TypeCandidat.choices,
        default=TypeCandidat.NON_DEFINI,
        blank=True,
        db_index=True,
    )

    # Laravel SSO fields
    laravel_id = models.PositiveIntegerField(_('ID Laravel'), null=True, blank=True, unique=True)
    laravel_token = models.TextField(_('Token Laravel'), blank=True, default='')

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    preferred_language = models.CharField(max_length=5, default='fr')
    dark_mode = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def generate_matricule(self):
        if not self.matricule:
            prefix = self.role[:3].upper()
            year = timezone.now().year
            count = User.objects.filter(role=self.role).count() + 1
            self.matricule = f"{prefix}-{year}-{count:05d}"

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.generate_matricule()
        
        # Accorder l'accès technique si le rôle est admin
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
            
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    school = models.CharField(max_length=200, blank=True)
    specialite = models.CharField(max_length=200, blank=True)
    total_points = models.IntegerField(default=0)
    badges = models.JSONField(default=list)
    completed_exams = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    rank = models.IntegerField(default=0)

    def __str__(self):
        return f"Profil de {self.user.full_name}"


class ProfilEleve(models.Model):
    """
    Extension du modèle User pour les informations scolaires et familiales
    d'un élève, nécessaires pour remplir les bulletins officiels béninois.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='profil_eleve',
        verbose_name=_('utilisateur'),
    )

    # ── Identité ──────────────────────────────────────────────────
    date_naissance = models.DateField(_('date de naissance'), null=True, blank=True)
    lieu_naissance = models.CharField(_('lieu de naissance'), max_length=200, blank=True)
    nationalite = models.CharField(_('nationalité'), max_length=100, blank=True, default='Béninoise')

    # ── Scolarité ─────────────────────────────────────────────────
    etablissement_origine = models.CharField(
        _('établissement d\'origine'), max_length=200, blank=True,
    )
    est_redoublant = models.BooleanField(_('redoublant'), default=False)
    nb_redoublements = models.PositiveSmallIntegerField(
        _('nombre de fois redoublé'), default=0,
    )

    # ── Père / Tuteur ──────────────────────────────────────────────
    nom_pere = models.CharField(_('nom et prénoms du père / tuteur'), max_length=200, blank=True)
    profession_pere = models.CharField(_('profession du père / tuteur'), max_length=200, blank=True)
    telephone_pere = models.CharField(_('téléphone du père / tuteur'), max_length=30, blank=True)

    # ── Mère / Tutrice ─────────────────────────────────────────────
    nom_mere = models.CharField(_('nom et prénoms de la mère / tutrice'), max_length=200, blank=True)
    profession_mere = models.CharField(_('profession de la mère / tutrice'), max_length=200, blank=True)
    telephone_mere = models.CharField(_('téléphone de la mère / tutrice'), max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('profil élève')
        verbose_name_plural = _('profils élèves')

    def __str__(self):
        return f"Profil élève — {self.user.full_name}"

    @classmethod
    def get_or_create_for(cls, user):
        """Récupère ou crée le profil élève d'un utilisateur."""
        obj, _ = cls.objects.get_or_create(user=user)
        return obj


class Referral(models.Model):
    """Système de parrainage entre utilisateurs."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parrain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parrainages', verbose_name='parrain')
    filleul = models.ForeignKey(User, on_delete=models.CASCADE, related_name='filleuls', verbose_name='filleul')
    code_parrainage = models.CharField(_('code de parrainage'), max_length=20, unique=True, blank=True)
    bonus_xp = models.IntegerField(_('bonus XP'), default=100)
    created_at = models.DateTimeField(_('date de parrainage'), auto_now_add=True)
    is_active = models.BooleanField(_('actif'), default=True)

    class Meta:
        verbose_name = _('parrainage')
        verbose_name_plural = _('parrainages')
        unique_together = ['parrain', 'filleul']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.parrain.full_name} → {self.filleul.full_name}"

    def save(self, *args, **kwargs):
        if not self.code_parrainage:
            self.code_parrainage = f"{self.parrain.matricule or self.parrain.email[:6]}-{self.filleul.id.hex[:6]}".upper()
        super().save(*args, **kwargs)


class MembreOrganisation(models.Model):
    """Appartenance d'un utilisateur à une ou plusieurs organisations."""

    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrateur')
        PROFESSEUR = 'professeur', _('Professeur')
        CONSEILLER = 'conseiller', _('Conseiller Pédagogique')
        ELEVE = 'eleve', _('Élève / Étudiant')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.CASCADE,
        related_name='membres',
    )
    role = models.CharField(_('rôle'), max_length=20, choices=Role.choices, default=Role.ELEVE)
    est_principal = models.BooleanField(
        _('organisation principale'),
        default=False,
        help_text=_('Organisation affichée par défaut pour cet utilisateur'),
    )
    date_adhesion = models.DateTimeField(_('date d\'adhésion'), auto_now_add=True)
    is_active = models.BooleanField(_('actif'), default=True)

    class Meta:
        verbose_name = _('membre organisation')
        verbose_name_plural = _('membres organisation')
        unique_together = ['user', 'organisation']
        ordering = ['-est_principal', '-date_adhesion']

    def __str__(self):
        return f"{self.user.full_name} — {self.organisation} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if self.est_principal:
            MembreOrganisation.objects.filter(user=self.user, est_principal=True).exclude(pk=self.pk).update(est_principal=False)
        super().save(*args, **kwargs)


class Leaderboard(models.Model):
    """Classement des utilisateurs."""
    class Periode(models.TextChoices):
        WEEKLY = 'weekly', _('Hebdomadaire')
        MONTHLY = 'monthly', _('Mensuel')
        TRIMESTRIEL = 'trimestriel', _('Trimestriel')
        ALLTIME = 'alltime', _('Tous les temps')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_leaderboard_entries')
    periode = models.CharField(_('période'), max_length=20, choices=Periode.choices, default=Periode.ALLTIME)
    rank = models.IntegerField(_('rang'), default=0)
    score = models.IntegerField(_('score'), default=0)
    updated_at = models.DateTimeField(_('dernière mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('classement')
        verbose_name_plural = _('classements')
        ordering = ['periode', 'rank']
        unique_together = ['user', 'periode']

    def __str__(self):
        return f"#{self.rank} - {self.user.full_name} ({self.get_periode_display()})"
