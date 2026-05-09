
# Mise à jour des modèles QCM pour le système éducatif béninois
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

class QCMBeninConfig(models.Model):
    """Configuration QCM selon le programme béninois"""
    
    class NiveauQCM(models.TextChoices):
        PRIMAIRE = 'primaire', _('Primaire')
        COLLEGE = 'college', _("Collège - Cycle d'Orientation")
        LYCEE = 'lycee', _('Lycée - Cycle Terminal')
        SUPERIEUR = 'superieur', _('Enseignement Supérieur')
        CONCOURS = 'concours', _('Concours et Examens')
    
    class TypeQCM(models.TextChoices):
        EVALUATION = 'evaluation', _('Évaluation Formative')
        EXAMEN = 'examen', _('Examen Sommatif')
        CONCOURS = 'concours', _('Concours National')
        REVISION = 'revision', _('Révision et Soutien')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True)
    niveau = models.CharField(_('niveau'), max_length=20, choices=NiveauQCM.choices)
    type_qcm = models.CharField(_('type'), max_length=20, choices=TypeQCM.choices)
    matiere = models.ForeignKey('core.Matiere', on_delete=models.CASCADE, related_name='qcm_benin')
    classe = models.ForeignKey('core.Classe', on_delete=models.CASCADE, related_name='qcm_benin')
    langue = models.CharField(_('langue'), max_length=10, choices=[
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
        ('ar', 'العربية')
    ], default='fr')
    
    # Paramètres spécifiques au programme béninois
    referentiel = models.JSONField(_('référentiel programme'), default=dict, help_text="Points du programme officiel béninois")
    objectifs_pedagogiques = models.JSONField(_('objectifs pédagogiques'), default=list)
    competences_visees = models.JSONField(_('compétences visées'), default=list)
    
    # Configuration IA
    prompt_ia = models.TextField(_('prompt IA personnalisé'), blank=True, help_text="Instructions spécifiques pour l'IA")
    style_questions = models.JSONField(_('style questions'), default=dict, help_text="Format et style des questions")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qcm_crees')
    
    class Meta:
        verbose_name = _('QCM Bénin')
        verbose_name_plural = _('QCMs Bénin')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.titre} - {self.classe.nom} ({self.get_niveau_display()})"

class QuestionBenin(models.Model):
    """Question QCM adaptée au programme béninois"""
    
    class TypeQuestion(models.TextChoices):
        QCM_SIMPLE = 'qcm', _('QCM Simple')
        QCM_MULTIPLE = 'qcm_multiple', _('QCM à Choix Multiples')
        VRAI_FAUX = 'vrai_faux', _('Vrai/Faux')
        ASSOCIATION = 'association', _('Association')
        ORDONNANCEMENT = 'ordonnancement', _('Ordonnancement')
        COMPLETION = 'completion', _('Texte à compléter')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qcm_config = models.ForeignKey(QCMBeninConfig, on_delete=models.CASCADE, related_name='questions')
    enonce = models.TextField(_('énoncé'))
    type_question = models.CharField(_('type'), max_length=20, choices=TypeQuestion.choices)
    numero = models.PositiveIntegerField(_('numéro'), default=1)
    
    # Références au programme
    chapitre = models.CharField(_('chapitre'), max_length=200, blank=True)
    lecon = models.CharField(_('leçon'), max_length=200, blank=True)
    competence = models.CharField(_('compétence'), max_length=300, blank=True)
    
    # Pédagogie
    difficulte = models.CharField(_('difficulté'), max_length=10, choices=[
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile')
    ], default='moyen')
    points = models.PositiveIntegerField(_('points'), default=1)
    temps_estime = models.PositiveIntegerField(_('temps estimé (secondes)'), default=60)
    
    # Explications pédagogiques
    explication = models.TextField(_('explication'), blank=True, help_text="Explication détaillée de la réponse")
    references = models.JSONField(_('références'), default=list, help_text="Références du programme ou manuels")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Question Bénin')
        verbose_name_plural = _('Questions Bénin')
        ordering = ['qcm_config', 'numero']
        unique_together = ['qcm_config', 'numero']
    
    def __str__(self):
        return f"Q{self.numero}: {self.enonce[:50]}..."

class ChoixBenin(models.Model):
    """Choix de réponse pour QCM béninois"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuestionBenin, on_delete=models.CASCADE, related_name='choix')
    texte = models.TextField(_('texte du choix'))
    est_correct = models.BooleanField(_('est correct'), default=False)
    ordre = models.PositiveIntegerField(_('ordre'), default=1)
    
    # Feedback pédagogique
    feedback_si_choisi = models.TextField(_('feedback si choisi'), blank=True, help_text="Explication si l'élève choisit cette option")
    
    class Meta:
        verbose_name = _('Choix QCM')
        verbose_name_plural = _('Choix QCM')
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.texte[:30]}... ({'✓' if self.est_correct else '✗'})"

class QCMSessionBenin(models.Model):
    """Session QCM pour élève béninois"""
    
    class Statut(models.TextChoices):
        COMMENCE = 'commence', _('Commencé')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')
        ABANDONNE = 'abandonne', _('Abandonné')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qcm_config = models.ForeignKey(QCMBeninConfig, on_delete=models.CASCADE, related_name='sessions')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qcm_sessions')
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.COMMENCE)
    
    # Timing
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    temps_total = models.PositiveIntegerField(_('temps total (secondes)'), help_text="Temps alloué pour le QCM")
    temps_restant = models.PositiveIntegerField(_('temps restant'), null=True, blank=True)
    
    # Résultats
    score = models.DecimalField(_('score'), max_digits=5, decimal_places=2, null=True, blank=True)
    pourcentage = models.PositiveIntegerField(_('pourcentage'), null=True, blank=True)
    note = models.DecimalField(_('note sur 20'), max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Analyse pédagogique
    reponses_correctes = models.PositiveIntegerField(_('réponses correctes'), default=0)
    reponses_incorrectes = models.PositiveIntegerField(_('réponses incorrectes'), default=0)
    reponses_non_repondues = models.PositiveIntegerField(_('non répondues'), default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Session QCM')
        verbose_name_plural = _('Sessions QCM')
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"QCM {self.qcm_config.titre} - {self.eleve.email}"

class ReponseQCMBenin(models.Model):
    """Réponse d'un élève à une question QCM"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(QCMSessionBenin, on_delete=models.CASCADE, related_name='reponses')
    question = models.ForeignKey(QuestionBenin, on_delete=models.CASCADE, related_name='reponses')
    
    # Réponse de l'élève
    reponse = models.JSONField(_('réponse'), help_text="Format selon le type de question")
    est_correct = models.BooleanField(_('est correct'), default=False)
    temps_reponse = models.PositiveIntegerField(_('temps de réponse (secondes)'), null=True, blank=True)
    
    # Feedback
    feedback_ia = models.TextField(_('feedback IA'), blank=True)
    points_obtenus = models.DecimalField(_('points obtenus'), max_digits=5, decimal_places=2, default=0)
    
    reponse_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Réponse QCM')
        verbose_name_plural = _('Réponses QCM')
        unique_together = ['session', 'question']
    
    def __str__(self):
        return f"Réponse de {self.session.eleve.email} à Q{self.question.numero}"
