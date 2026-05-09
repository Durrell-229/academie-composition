"""
Modèles pour la gestion académique complète
Gestion des promotions, inscriptions, et parcours académiques
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from schools.models import Etablissement, Classe, NiveauScolaire, AnneeScolaire


class Promotion(models.Model):
    """Promotion d'élèves (cohortes)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='promotions')
    nom = models.CharField(_('nom de la promotion'), max_length=100)  # Ex: Promotion 2024-2028
    code = models.CharField(_('code'), max_length=20, unique=True)
    
    annee_entree = models.CharField(_('année d\'entrée'), max_length=9)  # 2024-2025
    annee_sortie = models.CharField(_('année de sortie'), max_length=9)  # 2028-2029
    niveau_entree = models.ForeignKey(NiveauScolaire, on_delete=models.PROTECT, related_name='promotions_entree')
    niveau_sortie = models.ForeignKey(NiveauScolaire, on_delete=models.PROTECT, related_name='promotions_sortie')
    
    description = models.TextField(_('description'), blank=True)
    
    # Statistiques
    nombre_eleves = models.PositiveIntegerField(_('nombre d\'élèves'), default=0)
    nombre_diplomes = models.PositiveIntegerField(_('nombre de diplômés'), default=0)
    
    is_active = models.BooleanField(_('active'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Promotion')
        verbose_name_plural = _('Promotions')
        ordering = ['-annee_entree', 'nom']
        unique_together = ['etablissement', 'code']
    
    def __str__(self):
        return f"{self.nom} ({self.annee_entree} - {self.annee_sortie})"


class Inscription(models.Model):
    """Inscription d'un élève dans une classe"""
    
    class StatutInscription(models.TextChoices):
        INSCRITE = 'inscrite', _('Inscrite')
        EN_ATTENTE = 'en_attente', _('En attente')
        CONFIRMEE = 'confirmee', _('Confirmée')
        ANNULEE = 'annulee', _('Annulée')
        TRANSFEREE = 'transferee', _('Transférée')
        RADIATION = 'radiation', _('Radiation')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscriptions')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='inscriptions')
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True, related_name='inscriptions')
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='inscriptions')
    
    # Détails de l'inscription
    numero_inscription = models.CharField(_('numéro d\'inscription'), max_length=50, unique=True)
    date_inscription = models.DateField(_('date d\'inscription'), auto_now_add=True)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutInscription.choices, default=StatutInscription.INSCRITE)
    
    # Informations financières
    frais_inscription_payes = models.BooleanField(_('frais d\'inscription payés'), default=False)
    frais_scolarite_payes = models.BooleanField(_('frais de scolarité payés'), default=False)
    solde_du = models.DecimalField(_('solde dû'), max_digits=12, decimal_places=2, default=0)
    
    # Notes et progression
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, null=True, blank=True)
    rang_classe = models.PositiveIntegerField(_('rang dans la classe'), null=True, blank=True)
    appreciation = models.TextField(_('appréciation'), blank=True)
    
    # Statut académique
    est_redoublant = models.BooleanField(_('redoublant'), default=False)
    nombre_redoublements = models.PositiveIntegerField(_('nombre de redoublements'), default=0)
    est_boursier = models.BooleanField(_('boursier'), default=False)
    type_bourse = models.CharField(_('type de bourse'), max_length=50, blank=True)
    
    # Documents
    dossier_complet = models.BooleanField(_('dossier complet'), default=True)
    documents_manquants = models.TextField(_('documents manquants'), blank=True)
    
    # Observations
    observations = models.TextField(_('observations'), blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Inscription')
        verbose_name_plural = _('Inscriptions')
        unique_together = ['eleve', 'classe', 'annee_scolaire']
        ordering = ['-annee_scolaire__date_debut', 'eleve__last_name']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.classe.nom} ({self.annee_scolaire.nom})"
    
    def generer_numero_inscription(self):
        """Générer un numéro d'inscription unique"""
        from datetime import datetime
        annee = datetime.now().year
        etablissement_code = self.classe.etablissement.code[:3].upper()
        eleve_id = str(self.eleve.id.hex[:6]).upper()
        return f"INS-{annee}-{etablissement_code}-{eleve_id}"
    
    def save(self, *args, **kwargs):
        if not self.numero_inscription:
            self.numero_inscription = self.generer_numero_inscription()
        super().save(*args, **kwargs)


class MatiereClasse(models.Model):
    """Matières enseignées dans une classe"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='matieres')
    matiere = models.ForeignKey('core.Matiere', on_delete=models.CASCADE, related_name='classes_matieres')
    
    # Enseignement
    professeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='matieres_enseignees', limit_choices_to={'role': 'professeur'})
    coefficient = models.DecimalField(_('coefficient'), max_digits=5, decimal_places=2, default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(10.0)])
    
    # Horaires
    heures_semaine = models.PositiveIntegerField(_('heures par semaine'), default=2)
    salle = models.CharField(_('salle'), max_length=50, blank=True)
    
    # Progression
    chapitre_actuel = models.CharField(_('chapitre actuel'), max_length=200, blank=True)
    pourcentage_programme = models.PositiveIntegerField('% programme accompli', default=0, validators=[MaxValueValidator(100)])
    
    is_active = models.BooleanField(_('active'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Matière de classe')
        verbose_name_plural = _('Matières de classes')
        unique_together = ['classe', 'matiere']
        ordering = ['classe', 'matiere']
    
    def __str__(self):
        return f"{self.matiere.nom} - {self.classe.nom}"


class Evaluation(models.Model):
    """Évaluations (devoirs, examens, interros)"""
    
    class TypeEvaluation(models.TextChoices):
        DEVOIR = 'devoir', _('Devoir')
        INTERROGATION = 'interrogation', _('Interrogation')
        EXAMEN = 'examen', _('Examen')
        PARTIEL = 'partiel', _('Partiel')
        TP = 'tp', _('Travail Pratique')
        ORAL = 'oral', _('Oral')
        PROJET = 'projet', _('Projet')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matiere_classe = models.ForeignKey(MatiereClasse, on_delete=models.CASCADE, related_name='evaluations')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='evaluations')
    professeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='evaluations_crees')
    
    titre = models.CharField(_('titre'), max_length=200)
    type_evaluation = models.CharField(_('type d\'évaluation'), max_length=20, choices=TypeEvaluation.choices)
    description = models.TextField(_('description'), blank=True)
    
    # Dates et durée
    date_evaluation = models.DateTimeField(_('date de l\'évaluation'))
    duree = models.PositiveIntegerField(_('durée (minutes)'), default=60)
    
    # Barème
    note_maximale = models.DecimalField(_('note maximale'), max_digits=5, decimal_places=2, default=20.00)
    coefficient = models.DecimalField(_('coefficient'), max_digits=5, decimal_places=2, default=1.0)
    
    # Statut
    is_published = models.BooleanField(_('publiée'), default=False)
    is_terminee = models.BooleanField(_('terminée'), default=False)
    notes_communiquees = models.BooleanField(_('notes communiquées'), default=False)
    
    # Observations
    observations_professeur = models.TextField(_('observations du professeur'), blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Évaluation')
        verbose_name_plural = _('Évaluations')
        ordering = ['-date_evaluation']
    
    def __str__(self):
        return f"{self.titre} - {self.classe.nom}"


class Note(models.Model):
    """Notes des élèves"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='notes')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, related_name='notes')
    
    note = models.DecimalField(_('note'), max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    note_sur = models.DecimalField(_('note sur'), max_digits=5, decimal_places=2, default=20.00)
    
    # Appréciation
    appreciation = models.TextField(_('appréciation'), blank=True)
    observation = models.TextField(_('observation'), blank=True)
    
    # Statut
    est_absent = models.BooleanField(_('absent'), default=False)
    est_exclu = models.BooleanField(_('exclu'), default=False)
    note_reportee = models.BooleanField(_('note reportée'), default=False)
    
    # Date de saisie
    date_saisie = models.DateTimeField(_('date de saisie'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')
        unique_together = ['evaluation', 'eleve']
        ordering = ['evaluation', 'eleve__last_name']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.evaluation.titre}: {self.note}/{self.note_sur}"
    
    @property
    def note_sur_20(self):
        """Convertir la note sur 20"""
        if self.note_sur > 0:
            return round((self.note / self.note_sur) * 20, 2)
        return 0


class BulletinNotes(models.Model):
    """Bulletin de notes par période"""
    
    class TypeBulletin(models.TextChoices):
        TRIMESTRIEL = 'trimestriel', _('Trimestriel')
        SEMESTRIEL = 'semestriel', _('Semestriel')
        ANNUEL = 'annuel', _('Annuel')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, related_name='bulletins')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulletins_academiques')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='bulletins')
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='bulletins')
    
    periode = models.CharField(_('période'), max_length=50)  # Ex: 1er Trimestre, Semestre 1
    type_bulletin = models.CharField(_('type de bulletin'), max_length=20, choices=TypeBulletin.choices)
    
    # Notes
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2)
    moyenne_classe = models.DecimalField(_('moyenne de classe'), max_digits=5, decimal_places=2)
    rang = models.PositiveIntegerField(_('rang'))
    effectif_classe = models.PositiveIntegerField(_('effectif de la classe'))
    
    # Appreciations
    appreciation_generale = models.TextField(_('appréciation générale'))
    appreciation_conseil = models.TextField(_('appréciation du conseil de classe'), blank=True)
    
    # Comportement et assiduité
    comportement = models.CharField(_('comportement'), max_length=20, default='bon')
    nombre_absences = models.PositiveIntegerField(_('nombre d\'absences'), default=0)
    nombre_retards = models.PositiveIntegerField(_('nombre de retards'), default=0)
    
    # Statut
    est_valide = models.BooleanField(_('validé'), default=False)
    decision_conseil = models.CharField(_('décision du conseil'), max_length=50, blank=True)
    
    # Signature et validation
    date_emission = models.DateField(_('date d\'émission'), auto_now_add=True)
    signe_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bulletins_signes')
    
    class Meta:
        verbose_name = _('Bulletin de notes')
        verbose_name_plural = _('Bulletins de notes')
        unique_together = ['inscription', 'periode', 'annee_scolaire']
        ordering = ['-annee_scolaire__date_debut', 'periode']
    
    def __str__(self):
        return f"Bulletin {self.periode} - {self.eleve.get_full_name()}"


class Discipline(models.Model):
    """Gestion disciplinaire"""
    
    class TypeSanction(models.TextChoices):
        AVERTISSEMENT = 'avertissement', _('Avertissement')
        BLAME = 'blame', _('Blâme')
        EXCLUSION_TEMPORAIRE = 'exclusion_temporaire', _('Exclusion temporaire')
        EXCLUSION_DEFINITIVE = 'exclusion_definitive', _('Exclusion définitive')
        TACHES = 'taches', _('Tâches disciplinaires')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disciplines')
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, related_name='disciplines')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='disciplines')
    
    # Incident
    date_incident = models.DateField(_('date de l\'incident'))
    motif = models.CharField(_('motif'), max_length=200)
    description = models.TextField(_('description de l\'incident'))
    
    # Sanction
    type_sanction = models.CharField(_('type de sanction'), max_length=30, choices=TypeSanction.choices)
    duree_sanction = models.PositiveIntegerField(_('durée de la sanction (jours)'), null=True, blank=True)
    description_sanction = models.TextField(_('description de la sanction'), blank=True)
    
    # Responsable
    signale_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='disciplines_signalees')
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='disciplines_validees')
    
    # Statut
    est_executee = models.BooleanField(_('sanction exécutée'), default=False)
    observations = models.TextField(_('observations'), blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Discipline')
        verbose_name_plural = _('Disciplines')
        ordering = ['-date_incident']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.motif} ({self.date_incident})"
