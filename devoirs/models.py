import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import Matiere, Classe


class Devoir(models.Model):
    """Composition nationale / Devoir programmé par l'admin."""

    class Statut(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        PROGRAMME_PUBLIE = 'programme_publie', _('Programme publié')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True, default='')
    annee_scolaire = models.CharField(_('année scolaire'), max_length=20, default='2025-2026')
    date_debut = models.DateField(_('date de début'))
    date_fin = models.DateField(_('date de fin'))
    horaires = models.JSONField(_('horaires'), default=dict, blank=True)
    coefficient_default = models.DecimalField(_('coefficient par défaut'), max_digits=4, decimal_places=2, default=1.00)
    coefficients_par_matiere = models.JSONField(_('coefficients par matière'), default=dict, blank=True)
    classes = models.ManyToManyField(Classe, related_name='devoirs', verbose_name=_('classes concernées'))
    matieres = models.ManyToManyField(Matiere, related_name='devoirs', verbose_name=_('matières concernées'))
    statut = models.CharField(_('statut'), max_length=30, choices=Statut.choices, default=Statut.BROUILLON)
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devoirs_crees')
    instructions = models.TextField(_('instructions'), blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('devoir national')
        verbose_name_plural = _('devoirs nationaux')
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.titre} ({self.annee_scolaire})"

    @property
    def is_active(self):
        now = timezone.now().date()
        return self.date_debut <= now <= self.date_fin and self.statut == self.Statut.EN_COURS


class DevoirMatiere(models.Model):
    """Épreuve d'une matière spécifique pour un devoir national."""

    class StatutEP(models.TextChoices):
        SOUMIS = 'soumis', _('Soumis par le prof')
        VALIDE = 'valide', _('Validé par l\'admin')
        REJETE = 'rejete', _('Rejeté')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='devoir_matieres')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='devoir_matieres')
    epreuve_file = models.FileField(_('épreuve'), upload_to='devoirs/epreuves/%Y/%m/')
    corrige_type_file = models.FileField(_('corrigé type'), upload_to='devoirs/corriges/%Y/%m/')
    epreuve_document_id = models.CharField(_('ID épreuve'), max_length=32, blank=True, editable=False,
                                           help_text='Identifiant unique pour le suivi IA')
    corrige_document_id = models.CharField(_('ID corrigé'), max_length=32, blank=True, editable=False,
                                           help_text='Identifiant unique pour le suivi IA')
    soumis_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='devoirs_soumis')
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='devoirs_valides')
    statut = models.CharField(_('statut'), max_length=20, choices=StatutEP.choices, default=StatutEP.SOUMIS)
    commentaire_admin = models.TextField(_('commentaire admin'), blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('épreuve de devoir')
        verbose_name_plural = _('épreuves de devoir')
        unique_together = ['devoir', 'matiere']

    def __str__(self):
        return f"{self.devoir.titre} — {self.matiere.nom}"

    def save(self, *args, **kwargs):
        if not self.epreuve_document_id:
            self.epreuve_document_id = f"EPREUVE-{self.devoir.id.hex[:8]}-{self.matiere.id.hex[:8]}".upper()
        if not self.corrige_document_id:
            self.corrige_document_id = f"CORRIGE-DEV-{self.devoir.id.hex[:8]}-{self.matiere.id.hex[:8]}".upper()
        super().save(*args, **kwargs)


class DevoirComposition(models.Model):
    """Participation d'un élève à un devoir national."""

    class StatutComp(models.TextChoices):
        INSCRIT = 'inscrit', _('Inscrit')
        ABSENT = 'absent', _('Absent')
        COMPOSE = 'compose', _('A composé')

    class Resultat(models.TextChoices):
        ADMIS = 'admis', _('Admis')
        AJOURNE = 'ajourne', _('Ajourné')
        REFUSE = 'refuse', _('Refusé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='compositions')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devoir_compositions')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='devoir_compositions')
    statut = models.CharField(_('statut'), max_length=20, choices=StatutComp.choices, default=StatutComp.INSCRIT)
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0.00, null=True, blank=True)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    resultat = models.CharField(_('résultat'), max_length=20, choices=Resultat.choices, default=Resultat.ADMIS, null=True, blank=True)
    details_notes = models.JSONField(_('détails des notes'), default=dict, blank=True)
    composed_at = models.DateTimeField(_('date de composition'), null=True, blank=True)

    class Meta:
        verbose_name = _('composition devoir')
        verbose_name_plural = _('compositions devoirs')
        unique_together = ['devoir', 'eleve']
        ordering = ['rang', '-moyenne_generale']

    def __str__(self):
        return f"{self.eleve.full_name} — {self.devoir.titre}"


class Certificat(models.Model):
    """Certificat administratif généré pour un élève."""

    class TypeCertificat(models.TextChoices):
        ADMISSION = 'admission', _('Admission')
        EXCELLENCE = 'excellence', _('Excellence')
        PARTICIPATION = 'participation', _('Participation')
        FIN_ANNEE = 'fin_annee', _('Fin d\'année')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificats')
    devoir = models.ForeignKey(Devoir, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificats')
    type_certificat = models.CharField(_('type'), max_length=20, choices=TypeCertificat.choices, default=TypeCertificat.ADMISSION)
    moyenne_obtenue = models.DecimalField(_('moyenne'), max_digits=5, decimal_places=2, default=0.00)
    mention = models.TextField(_('mention'), blank=True, default='')
    numero_certificat = models.CharField(_('numéro'), max_length=30, unique=True, blank=True)
    date_delivrance = models.DateField(_('date de délivrance'), auto_now_add=True)
    file_pdf = models.FileField(_('fichier PDF'), upload_to='certificats/%Y/%m/', blank=True, null=True)
    verification_token = models.UUIDField(_('token de vérification'), unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('certificat')
        verbose_name_plural = _('certificats')
        ordering = ['-created_at']

    def __str__(self):
        return f"Certificat {self.numero_certificat} — {self.eleve.full_name}"

    def save(self, *args, **kwargs):
        if not self.numero_certificat:
            year = timezone.now().year
            count = Certificat.objects.filter(date_delivrance__year=year).count() + 1
            self.numero_certificat = f"CERT-{year}-{count:05d}"
        super().save(*args, **kwargs)


class DevoirReponseEleve(models.Model):
    """Copie soumise par un élève pour une matière d'un devoir national."""

    class StatutReponse(models.TextChoices):
        SOUMIS = 'soumis', _('Soumis')
        EN_COURS_CORRECTION = 'en_cours_correction', _('En cours de correction IA')
        CORRIGE = 'corrige', _('Corrigé par IA')
        APPROUVE = 'approuve', _('Approuvé par admin')
        REJETE = 'rejete', _('Rejeté / à reprendre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir_matiere = models.ForeignKey(DevoirMatiere, on_delete=models.CASCADE, related_name='reponses')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devoir_reponses')
    copie_file = models.FileField(_('copie de l\'élève'), upload_to='devoirs/copies/%Y/%m/', blank=True, null=True)
    copie_text = models.TextField(_('texte de la copie'), blank=True, default='')
    copie_document_id = models.CharField(_('ID copie'), max_length=32, blank=True, editable=False,
                                         help_text='Identifiant unique pour le suivi IA')
    statut = models.CharField(_('statut'), max_length=30, choices=StatutReponse.choices, default=StatutReponse.SOUMIS)
    note_ia = models.DecimalField(_('note IA'), max_digits=5, decimal_places=2, null=True, blank=True)
    note_finale = models.DecimalField(_('note finale'), max_digits=5, decimal_places=2, null=True, blank=True)
    appreciation_ia = models.TextField(_('appréciation IA'), blank=True, default='')
    feedback_ia = models.JSONField(_('feedback détaillé IA'), default=dict, blank=True)
    soumis_par_admin = models.BooleanField(_('saisi par admin'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    corrige_at = models.DateTimeField(_('date de correction'), null=True, blank=True)
    approuve_at = models.DateTimeField(_('date d\'approbation'), null=True, blank=True)

    class Meta:
        verbose_name = _('réponse élève')
        verbose_name_plural = _('réponses élèves')
        unique_together = ['devoir_matiere', 'eleve']
        ordering = ['created_at']

    def __str__(self):
        return f"{self.eleve.full_name} — {self.devoir_matiere.matiere.nom}"

    def save(self, *args, **kwargs):
        if not self.copie_document_id:
            self.copie_document_id = f"COPIE-DEV-{self.devoir_matiere.id.hex[:8]}-{self.eleve.id.hex[:8]}".upper()
        super().save(*args, **kwargs)


class BulletinDevoir(models.Model):
    """Bulletin généré pour un élève sur un devoir national."""

    class StatutBulletin(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente d\'approbation')
        APPROUVE = 'approuve', _('Approuvé')
        REJETE = 'rejete', _('Rejeté')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='bulletins')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bulletins_devoir')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='bulletins_devoir')
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0.00)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    effectif_total = models.PositiveIntegerField(_('effectif total'), default=0)
    decision_conseil = models.CharField(_('décision du conseil'), max_length=100, blank=True, default='')
    statut = models.CharField(_('statut'), max_length=20, choices=StatutBulletin.choices, default=StatutBulletin.EN_ATTENTE)
    approuve_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bulletins_approuves')
    appreciation_ia = models.TextField(_('synthèse IA'), blank=True, default='')
    file_pdf = models.FileField(_('fichier PDF'), upload_to='bulletins_devoirs/%Y/%m/', blank=True, null=True)
    verification_token = models.UUIDField(_('token de vérification'), unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    approuve_at = models.DateTimeField(_('date d\'approbation'), null=True, blank=True)

    class Meta:
        verbose_name = _('bulletin de devoir')
        verbose_name_plural = _('bulletins de devoirs')
        unique_together = ['devoir', 'eleve']
        ordering = ['rang', '-moyenne_generale']

    def __str__(self):
        return f"Bulletin {self.devoir.titre} — {self.eleve.full_name}"


class BulletinDevoirLigne(models.Model):
    """Note par matière dans un bulletin de devoir national."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulletin = models.ForeignKey(BulletinDevoir, on_delete=models.CASCADE, related_name='lignes')
    matiere = models.CharField(_('matière'), max_length=100)
    coefficient = models.DecimalField(_('coefficient'), max_digits=4, decimal_places=2, default=1.00)
    note_devoir = models.DecimalField(_('note devoir'), max_digits=5, decimal_places=2, default=0.00)
    note_exam = models.DecimalField(_('note examen'), max_digits=5, decimal_places=2, default=0.00)
    moyenne = models.DecimalField(_('moyenne'), max_digits=5, decimal_places=2, default=0.00)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    appreciation = models.TextField(_('appréciation'), blank=True, default='')

    class Meta:
        verbose_name = _('ligne de bulletin')
        verbose_name_plural = _('lignes de bulletin')
        ordering = ['-moyenne']

    def __str__(self):
        return f"{self.matiere} — {self.moyenne}/20"
