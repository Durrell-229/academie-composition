import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.models import Matiere, Classe


class Exam(models.Model):
    class Type(models.TextChoices):
        COMPOSITION = 'composition', _('Composition')
        EXAMEN = 'examen', _('Examen')
        DEVOIR = 'devoir', _('Devoir')
        CONCOURS = 'concours', _('Concours')
        EVALUATION_PROF = 'eval_prof', _('Évaluation Professeur')

    class Statut(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        PUBLIE = 'publie', _('Publié')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')
        ANNULE = 'annule', _('Annulé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True)
    type_exam = models.CharField(_('type'), max_length=20, choices=Type.choices, default=Type.COMPOSITION)
    matiere = models.ForeignKey(Matiere, on_delete=models.SET_NULL, null=True, related_name='exams')
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams')
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exams_crees')
    duree_minutes = models.PositiveIntegerField(_('durée (minutes)'), default=60)
    date_debut = models.DateTimeField(_('date de début'))
    date_fin = models.DateTimeField(_('date de fin'))
    note_maximale = models.DecimalField(_('note maximale'), max_digits=5, decimal_places=2, default=20.00)
    coefficient = models.DecimalField(_('coefficient'), max_digits=4, decimal_places=2, default=1.00)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    approval_status = models.CharField(_('statut approbation'), max_length=20, choices=[('pending', 'En attente'), ('approved', 'Approuvé'), ('rejected', 'Rejeté')], default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams_approved')
    est_public = models.BooleanField(_('public'), default=False)
    instructions = models.TextField(_('instructions'), blank=True)
    anti_cheat_active = models.BooleanField(_('anti-triche actif'), default=True)
    camera_required = models.BooleanField(_('caméra obligatoire'), default=True)
    fullscreen_required = models.BooleanField(_('plein écran obligatoire'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('épreuve')
        verbose_name_plural = _('épreuves')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titre} ({self.get_type_exam_display()})"

    @property
    def is_en_cours(self):
        now = timezone.now()
        return self.date_debut <= now <= self.date_fin and self.statut == self.Statut.EN_COURS

    @property
    def is_passe(self):
        return timezone.now() > self.date_fin


class ExamFile(models.Model):
    class TypeFichier(models.TextChoices):
        EPREUVE = 'epreuve', _('Épreuve')
        CORRIGE_TYPE = 'corrige_type', _('Corrigé Type')
        ANNEXE = 'annexe', _('Annexe')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='files')
    type_fichier = models.CharField(_('type de fichier'), max_length=20, choices=TypeFichier.choices)
    fichier = models.FileField(_('fichier'), upload_to='exams/%Y/%m/')
    nom_original = models.CharField(_('nom original'), max_length=255)
    document_id = models.CharField(_('ID document'), max_length=32, blank=True, editable=False,
                                   help_text='Identifiant unique pour le suivi IA')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('fichier d\'épreuve')
        verbose_name_plural = _('fichiers d\'épreuve')

    def __str__(self):
        return f"{self.nom_original} ({self.get_type_fichier_display()})"

    def save(self, *args, **kwargs):
        if not self.document_id:
            self.document_id = f"CORRIGE-{self.exam.id.hex[:8]}-{uuid.uuid4().hex[:8]}".upper()
        super().save(*args, **kwargs)


class ExamAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='assignments')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_assignments', blank=True, null=True)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='exam_assignments', blank=True, null=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assignments_crees')
    assigned_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    class Meta:
        unique_together = [['exam', 'eleve'], ['exam', 'classe']]
        verbose_name = _('attribution d\'épreuve')
        verbose_name_plural = _('attributions d\'épreuves')

    def __str__(self):
        target = self.eleve or self.classe
        return f"{self.exam.titre} -> {target}"


# ═══════════════════════════════════════════════════════════════════════════
# EXAMEN NATIONAL — BEPC, CEP, BACCALAURÉAT
# ═══════════════════════════════════════════════════════════════════════════

class ExamenNational(models.Model):
    """Examen national officiel (BEPC, CEP, Baccalauréat) avec plusieurs matières."""

    class TypeExamen(models.TextChoices):
        BEPC = 'bepc', 'BEPC'
        CEP = 'cep', 'CEP'
        BAC_A1 = 'bac_a1', 'Baccalauréat A1'
        BAC_A2 = 'bac_a2', 'Baccalauréat A2'
        BAC_B = 'bac_b', 'Baccalauréat B'
        BAC_C = 'bac_c', 'Baccalauréat C'
        BAC_D = 'bac_d', 'Baccalauréat D'
        BAC_E = 'bac_e', 'Baccalauréat E'
        BAC_G1 = 'bac_g1', 'Baccalauréat G1'
        BAC_G2 = 'bac_g2', 'Baccalauréat G2'
        BAC_G3 = 'bac_g3', 'Baccalauréat G3'

    class Statut(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        PROGRAMME_PUBLIE = 'programme_publie', _('Programme publié')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom'), max_length=200)
    type_examen = models.CharField(_('type d\'examen'), max_length=20, choices=TypeExamen.choices)
    annee_scolaire = models.CharField(_('année scolaire'), max_length=20, default='2025-2026')
    date_debut = models.DateField(_('date de début'))
    date_fin = models.DateField(_('date de fin'))
    horaires = models.JSONField(_('horaires'), default=dict, blank=True)
    coefficient_default = models.DecimalField(_('coefficient par défaut'), max_digits=4, decimal_places=2, default=1.00)
    coefficients_par_matiere = models.JSONField(_('coefficients par matière'), default=dict, blank=True)
    classes = models.ManyToManyField(Classe, related_name='examens_nationaux', verbose_name=_('classes concernées'))
    matieres = models.ManyToManyField(Matiere, related_name='examens_nationaux', verbose_name=_('matières concernées'))
    statut = models.CharField(_('statut'), max_length=30, choices=Statut.choices, default=Statut.BROUILLON)
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='examens_nationaux_crees')
    instructions = models.TextField(_('instructions'), blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('examen national')
        verbose_name_plural = _('examens nationaux')
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.get_type_examen_display()} — {self.annee_scolaire}"

    @property
    def is_active(self):
        now = timezone.now().date()
        return self.date_debut <= now <= self.date_fin and self.statut == self.Statut.EN_COURS


class ExamenNationalMatiere(models.Model):
    """Épreuve d'une matière spécifique pour un examen national."""

    class StatutEP(models.TextChoices):
        SOUMIS = 'soumis', _('Soumis par le prof')
        VALIDE = 'valide', _('Validé par l\'admin')
        REJETE = 'rejete', _('Rejeté')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    examen = models.ForeignKey(ExamenNational, on_delete=models.CASCADE, related_name='examen_matieres')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='examen_matieres')
    epreuve_file = models.FileField(_('épreuve'), upload_to='examens_nationaux/epreuves/%Y/%m/')
    corrige_type_file = models.FileField(_('corrigé type'), upload_to='examens_nationaux/corriges/%Y/%m/')
    epreuve_document_id = models.CharField(_('ID épreuve'), max_length=32, blank=True, editable=False,
                                           help_text='Identifiant unique pour le suivi IA')
    corrige_document_id = models.CharField(_('ID corrigé'), max_length=32, blank=True, editable=False,
                                           help_text='Identifiant unique pour le suivi IA')
    soumis_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='examens_soumis')
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='examens_valides')
    statut = models.CharField(_('statut'), max_length=20, choices=StatutEP.choices, default=StatutEP.SOUMIS)
    commentaire_admin = models.TextField(_('commentaire admin'), blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('épreuve d\'examen national')
        verbose_name_plural = _('épreuves d\'examens nationaux')
        unique_together = ['examen', 'matiere']

    def __str__(self):
        return f"{self.examen} — {self.matiere.nom}"

    def save(self, *args, **kwargs):
        if not self.epreuve_document_id:
            self.epreuve_document_id = f"EPREUVE-EN-{self.examen.id.hex[:8]}-{self.matiere.id.hex[:8]}".upper()
        if not self.corrige_document_id:
            self.corrige_document_id = f"CORRIGE-EN-{self.examen.id.hex[:8]}-{self.matiere.id.hex[:8]}".upper()
        super().save(*args, **kwargs)


class ExamenComposition(models.Model):
    """Participation d'un élève à un examen national."""

    class StatutComp(models.TextChoices):
        INSCRIT = 'inscrit', _('Inscrit')
        ABSENT = 'absent', _('Absent')
        COMPOSE = 'compose', _('A composé')

    class Resultat(models.TextChoices):
        ADMIS = 'admis', _('Admis')
        AJOURNE = 'ajourne', _('Ajourné')
        REFUSE = 'refuse', _('Refusé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    examen = models.ForeignKey(ExamenNational, on_delete=models.CASCADE, related_name='compositions')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='examen_compositions')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='examen_compositions')
    statut = models.CharField(_('statut'), max_length=20, choices=StatutComp.choices, default=StatutComp.INSCRIT)
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0.00, null=True, blank=True)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    resultat = models.CharField(_('résultat'), max_length=20, choices=Resultat.choices, default=Resultat.ADMIS, null=True, blank=True)
    details_notes = models.JSONField(_('détails des notes'), default=dict, blank=True)
    composed_at = models.DateTimeField(_('date de composition'), null=True, blank=True)

    class Meta:
        verbose_name = _('composition examen national')
        verbose_name_plural = _('compositions examens nationaux')
        unique_together = ['examen', 'eleve']
        ordering = ['rang', '-moyenne_generale']

    def __str__(self):
        return f"{self.eleve.full_name} — {self.examen}"


class ExamenReponseEleve(models.Model):
    """Copie soumise par un élève pour une matière d'un examen national."""

    class StatutReponse(models.TextChoices):
        SOUMIS = 'soumis', _('Soumis')
        EN_COURS_CORRECTION = 'en_cours_correction', _('En cours de correction IA')
        CORRIGE = 'corrige', _('Corrigé par IA')
        APPROUVE = 'approuve', _('Approuvé par admin')
        REJETE = 'rejete', _('Rejeté / à reprendre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    examen_matiere = models.ForeignKey(ExamenNationalMatiere, on_delete=models.CASCADE, related_name='reponses')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='examen_reponses')
    copie_file = models.FileField(_('copie de l\'élève'), upload_to='examens_nationaux/copies/%Y/%m/', blank=True, null=True)
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
        verbose_name = _('réponse élve examen')
        verbose_name_plural = _('réponses élèves examens')
        unique_together = ['examen_matiere', 'eleve']
        ordering = ['created_at']

    def __str__(self):
        return f"{self.eleve.full_name} — {self.examen_matiere.matiere.nom}"

    def save(self, *args, **kwargs):
        if not self.copie_document_id:
            self.copie_document_id = f"COPIE-EN-{self.examen_matiere.id.hex[:8]}-{self.eleve.id.hex[:8]}".upper()
        super().save(*args, **kwargs)


class ExamenBulletin(models.Model):
    """Bulletin généré pour un élève sur un examen national."""

    class StatutBulletin(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente d\'approbation')
        APPROUVE = 'approuve', _('Approuvé')
        REJETE = 'rejete', _('Rejeté')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    examen = models.ForeignKey(ExamenNational, on_delete=models.CASCADE, related_name='bulletins')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='examens_bulletins')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='examens_bulletins')
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0.00)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    effectif_total = models.PositiveIntegerField(_('effectif total'), default=0)
    decision_conseil = models.CharField(_('décision du conseil'), max_length=100, blank=True, default='')
    statut = models.CharField(_('statut'), max_length=20, choices=StatutBulletin.choices, default=StatutBulletin.EN_ATTENTE)
    approuve_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='examens_bulletins_approuves')
    appreciation_ia = models.TextField(_('synthèse IA'), blank=True, default='')
    file_pdf = models.FileField(_('fichier PDF'), upload_to='bulletins_examens/%Y/%m/', blank=True, null=True)
    verification_token = models.UUIDField(_('token de vérification'), unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    approuve_at = models.DateTimeField(_('date d\'approbation'), null=True, blank=True)

    class Meta:
        verbose_name = _('bulletin d\'examen national')
        verbose_name_plural = _('bulletins d\'examens nationaux')
        unique_together = ['examen', 'eleve']
        ordering = ['rang', '-moyenne_generale']

    def __str__(self):
        return f"Bulletin {self.examen} — {self.eleve.full_name}"


class ExamenBulletinLigne(models.Model):
    """Note par matière dans un bulletin d'examen national."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulletin = models.ForeignKey(ExamenBulletin, on_delete=models.CASCADE, related_name='lignes')
    matiere = models.CharField(_('matière'), max_length=100)
    coefficient = models.DecimalField(_('coefficient'), max_digits=4, decimal_places=2, default=1.00)
    note_devoir = models.DecimalField(_('note devoir'), max_digits=5, decimal_places=2, default=0.00)
    note_exam = models.DecimalField(_('note examen'), max_digits=5, decimal_places=2, default=0.00)
    moyenne = models.DecimalField(_('moyenne'), max_digits=5, decimal_places=2, default=0.00)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    appreciation = models.TextField(_('appréciation'), blank=True, default='')

    class Meta:
        verbose_name = _('ligne de bulletin examen')
        verbose_name_plural = _('lignes de bulletin examens')
        ordering = ['-moyenne']

    def __str__(self):
        return f"{self.matiere} — {self.moyenne}/20"
