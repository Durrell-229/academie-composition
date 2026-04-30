import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from exams.models import Exam


class CompositionSession(models.Model):
    class Mode(models.TextChoices):
        EN_LIGNE = 'en_ligne', _('En Ligne')
        SUR_PAPIER = 'sur_papier', _('Sur Papier')

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours')
        SOUMIS = 'soumis', _('Soumis')
        EN_CORRECTION = 'en_correction', _('En correction')
        CORRIGE = 'corrige', _('Corrigé')
        EXCLU = 'exclu', _('Exclu (triche)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sessions')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='composition_sessions')
    mode = models.CharField(_('mode'), max_length=20, choices=Mode.choices, default=Mode.EN_LIGNE)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    started_at = models.DateTimeField(_('début'), blank=True, null=True)
    submitted_at = models.DateTimeField(_('soumission'), blank=True, null=True)
    time_spent_seconds = models.PositiveIntegerField(_('temps passé (secondes)'), default=0)
    qr_code = models.ImageField(_('QR Code'), upload_to='qr_codes/', blank=True, null=True)
    qr_token = models.CharField(_('token QR'), max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    cheat_count = models.PositiveIntegerField(_('nombre de triches'), default=0)
    cheat_logs = models.JSONField(_('logs de triche'), default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('session de composition')
        verbose_name_plural = _('sessions de composition')
        unique_together = ['exam', 'eleve']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.eleve.full_name} - {self.exam.titre}"

    def start(self):
        self.statut = self.Statut.EN_COURS
        self.started_at = timezone.now()
        self.save()

    def submit(self):
        self.statut = self.Statut.SOUMIS
        self.submitted_at = timezone.now()
        if self.started_at:
            self.time_spent_seconds = int((timezone.now() - self.started_at).total_seconds())
        self.save()


class StudentAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CompositionSession, on_delete=models.CASCADE, related_name='answers')
    question_number = models.PositiveIntegerField(_('numéro de question'))
    content = models.TextField(_('contenu de la réponse'))
    file = models.FileField(_('fichier joint'), upload_to='answers/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('réponse de l\'élève')
        verbose_name_plural = _('réponses des élèves')
        unique_together = ['session', 'question_number']
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number} - {self.session}"


class StudentSubmissionFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CompositionSession, on_delete=models.CASCADE, related_name='submission_files')
    fichier = models.ImageField(_('fichier'), upload_to='submissions/%Y/%m/')
    page_number = models.PositiveIntegerField(_('numéro de page'), default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('fichier de soumission')
        verbose_name_plural = _('fichiers de soumission')
        ordering = ['page_number']

    def __str__(self):
        return f"Page {self.page_number} - {self.session}"


class Resultat(models.Model):
    class Mention(models.TextChoices):
        EXCELLENT = 'excellent', _('Excellent')
        TRES_BIEN = 'tres_bien', _('Très Bien')
        BIEN = 'bien', _('Bien')
        ASSEZ_BIEN = 'assez_bien', _('Assez Bien')
        PASSABLE = 'passable', _('Passable')
        INSUFFISANT = 'insuffisant', _('Insuffisant')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(CompositionSession, on_delete=models.CASCADE, related_name='resultat')
    note = models.DecimalField(_('note'), max_digits=5, decimal_places=2)
    note_sur = models.DecimalField(_('note sur'), max_digits=5, decimal_places=2, default=20.00)
    mention = models.CharField(_('mention'), max_length=20, choices=Mention.choices, blank=True)
    appreciation = models.TextField(_('appréciation'), blank=True)
    details_correction = models.JSONField(_('détails de correction'), default=dict)
    classement = models.PositiveIntegerField(_('classement'), default=0)
    total_participants = models.PositiveIntegerField(_('total participants'), default=0)
    corrige_par_ia = models.BooleanField(_('corrigé par IA'), default=False)
    corrige_par_humain = models.BooleanField(_('corrigé par humain'), default=False)
    corrigeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='corrections_effectuees')
    corrige_at = models.DateTimeField(_('date de correction'), blank=True, null=True)
    bulletin_pdf = models.FileField(_('bulletin PDF'), upload_to='bulletins/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('résultat')
        verbose_name_plural = _('résultats')
        ordering = ['-note']

    def __str__(self):
        return f"{self.session.eleve.full_name} - {self.note}/{self.note_sur}"

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Resultat)
def trigger_bulletin_generation(sender, instance, created, **kwargs):
    """
    Génère automatiquement un bulletin après l'enregistrement d'un résultat.
    """
    if instance.note is not None and instance.note > 0:
        try:
            from bulletins.services import BulletinService
            from bulletins.models import Bulletin
            
            # Logique de création de bulletin à adapter selon votre besoin de groupement (trimestre/semestre)
            # Ici on crée ou met à jour un bulletin 'ANNUEL' par défaut comme exemple
            bulletin, _ = Bulletin.objects.get_or_create(
                eleve=instance.session.eleve,
                periode='AN',
                annee_scolaire="2025-2026",
                defaults={'classe': instance.session.eleve.classe}
            )
            # Mise à jour des données du bulletin et génération PDF
            bulletin.moyenne_generale = instance.note  # Simplification
            bulletin.save()
            BulletinService.generate_pdf_from_bulletin(bulletin)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Erreur génération bulletin: {e}")


class AntiCheatLog(models.Model):
    class TypeEvent(models.TextChoices):
        TAB_CHANGE = 'tab_change', _('Changement d\'onglet')
        FULLSCREEN_EXIT = 'fullscreen_exit', _('Sortie plein écran')
        CAMERA_OFF = 'camera_off', _('Caméra désactivée')
        MULTIPLE_FACES = 'multiple_faces', _('Plusieurs visages détectés')
        COPY_PASTE = 'copy_paste', _('Copier/Coller')
        RIGHT_CLICK = 'right_click', _('Clic droit')
        SUSPICIOUS_MOVEMENT = 'suspicious_movement', _('Mouvement suspect')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CompositionSession, on_delete=models.CASCADE, related_name='anti_cheat_logs')
    type_event = models.CharField(_('type d\'événement'), max_length=30, choices=TypeEvent.choices)
    description = models.TextField(_('description'), blank=True)
    screenshot = models.ImageField(_('capture d\'écran'), upload_to='cheat_screenshots/%Y/%m/', blank=True, null=True)
    timestamp = models.DateTimeField(_('horodatage'), default=timezone.now)

    class Meta:
        verbose_name = _('log anti-triche')
        verbose_name_plural = _('logs anti-triche')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_type_event_display()} - {self.session.eleve.full_name}"
