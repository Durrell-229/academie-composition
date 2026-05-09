"""
Modèles pour la gestion des certificats et diplômes
Adapté au système scolaire du Bénin (BEPC, Bac, etc.)
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from schools.models import Etablissement, Classe
from core.models import Matiere


class TypeCertificat(models.Model):
    """Types de certificats (BEPC, Bac, Attestations, etc.)"""
    
    class NiveauScolaire(models.TextChoices):
        PRIMAIRE = 'primaire', _('Enseignement Primaire')
        SECONDAIRE_1 = 'secondaire_1', _('1er Cycle Secondaire')
        SECONDAIRE_2 = 'secondaire_2', _('2nd Cycle Secondaire')
        UNIVERSITAIRE = 'universitaire', _('Universitaire')
        PROFESSIONNEL = 'professionnel', _('Formation Professionnelle')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='types_certificats')
    
    code = models.CharField(_('code'), max_length=20, unique=True)
    nom = models.CharField(_('nom'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    niveau_scolaire = models.CharField(_('niveau scolaire'), max_length=20, choices=NiveauScolaire.choices)
    
    # Configuration du certificat
    mention_reussite = models.CharField(_('mention de réussite'), max_length=50, default='ADMIS')
    mention_echec = models.CharField(_('mention d\'échec'), max_length=50, default='REFUSÉ')
    
    # Design
    template_fond = models.ImageField(_('template de fond'), upload_to='certificats/templates/', blank=True, null=True)
    couleur_principale = models.CharField(_('couleur principale'), max_length=7, default='#1e3a8a')
    couleur_secondaire = models.CharField(_('couleur secondaire'), max_length=7, default='#3b82f6')
    
    # Signataires
    titre_signataire_1 = models.CharField(_('titre signataire 1'), max_length=100, default='Le Directeur')
    titre_signataire_2 = models.CharField(_('titre signataire 2'), max_length=100, default='Le Chef des Travaux')
    
    # Statut
    is_actif = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Type de certificat')
        verbose_name_plural = _('Types de certificats')
        ordering = ['niveau_scolaire', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_niveau_scolaire_display()})"


class CertificatScolaire(models.Model):
    """Certificat délivré à un élève"""
    
    class StatutCertificat(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        ADMIS = 'admis', _('Admis')
        REFUSE = 'refuse', _('Refusé')
        MENTION_PASSABLE = 'passable', _('Passable')
        MENTION_ASSEZ_BIEN = 'assez_bien', _('Assez Bien')
        MENTION_BIEN = 'bien', _('Bien')
        MENTION_TRES_BIEN = 'tres_bien', _('Très Bien')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_certificat = models.CharField(_('numéro de certificat'), max_length=50, unique=True)
    
    # Relations
    type_certificat = models.ForeignKey(TypeCertificat, on_delete=models.CASCADE, related_name='certificats')
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='certificats')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificats_scolaires', limit_choices_to={'role': 'eleve'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='certificats')
    
    # Informations de l'examen
    examen = models.ForeignKey('ExamenSession', on_delete=models.CASCADE, related_name='certificats', null=True, blank=True)
    annee_scolaire = models.CharField(_('année scolaire'), max_length=9, default='2024-2025')
    session = models.CharField(_('session'), max_length=20, default='Session Principale')
    
    # Résultats
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, null=True, blank=True)
    note_maximale = models.DecimalField(_('note maximale'), max_digits=5, decimal_places=2, default=20.00)
    
    # Statut
    statut = models.CharField(_('statut'), max_length=20, choices=StatutCertificat.choices, default=StatutCertificat.EN_ATTENTE)
    est_delivre = models.BooleanField(_('délivré'), default=False)
    
    # Mention (pour les réussites)
    mention = models.CharField(_('mention'), max_length=50, blank=True)
    
    # Contenu personnalisé
    intitule_programme = models.CharField(_('intitulé du programme'), max_length=200, blank=True)
    appreciation_generale = models.TextField(_('appréciation générale'), blank=True)
    
    # QR Code et sécurité
    qr_code = models.ImageField(_('QR code'), upload_to='certificats/qr_codes/', blank=True, null=True)
    code_verification = models.CharField(_('code de vérification'), max_length=20, blank=True)
    
    # Signataires
    signataire_1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificats_signes_1', limit_choices_to={'role__in': ['admin', 'professeur']})
    signataire_2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificats_signes_2', limit_choices_to={'role__in': ['admin', 'professeur']})
    
    date_signature_1 = models.DateField(_('date de signature 1'), null=True, blank=True)
    date_signature_2 = models.DateField(_('date de signature 2'), null=True, blank=True)
    
    # Lieu et date de délivrance
    lieu_delivrance = models.CharField(_('lieu de délivrance'), max_length=100, default='Cotonou')
    date_delivrance = models.DateField(_('date de délivrance'), null=True, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    delivre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='certificats_delivres')
    
    class Meta:
        verbose_name = _('Certificat scolaire')
        verbose_name_plural = _('Certificats scolaires')
        ordering = ['-date_delivrance', 'eleve__last_name']
        unique_together = ['eleve', 'type_certificat', 'annee_scolaire']
    
    def __str__(self):
        return f"{self.numero_certificat} - {self.eleve.get_full_name()}"
    
    def generer_numero(self):
        """Générer un numéro de certificat unique"""
        import random
        annee = self.annee_scolaire[:4]
        etab_code = self.etablissement.code[:3].upper()
        random_part = str(random.randint(10000, 99999))
        return f"CERT-{annee}-{etab_code}-{random_part}"
    
    def save(self, *args, **kwargs):
        if not self.numero_certificat:
            self.numero_certificat = self.generer_numero()
        if not self.code_verification:
            import secrets
            self.code_verification = secrets.token_urlsafe(16)[:20]
        super().save(*args, **kwargs)


class ExamenSession(models.Model):
    """Session d'examen (BEPC, Bac, etc.)"""
    
    class TypeExamen(models.TextChoices):
        CEPE = 'cepe', _('CEPE - Certificat d\'Études Primaires')
        BEPC = 'bepc', _('BEPC - Brevet d\'Études du Premier Cycle')
        BACCALAUREAT = 'bac', _('Baccalauréat')
        CONCOURS = 'concours', _('Concours d\'entrée')
        EXAMEN_BLANC = 'examen_blanc', _('Examen Blanc')
        DEVOIR = 'devoir', _('Devoir de Contrôle')
    
    class SessionType(models.TextChoices):
        PRINCIPALE = 'principale', _('Session Principale')
        RATTRAPAGE = 'rattrapage', _('Session de Rattrapage')
        REMPLACEMENT = 'remplacement', _('Session de Remplacement')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='examens_sessions')
    
    type_examen = models.CharField(_('type d\'examen'), max_length=20, choices=TypeExamen.choices)
    session = models.CharField(_('session'), max_length=20, choices=SessionType.choices, default=SessionType.PRINCIPALE)
    annee_scolaire = models.CharField(_('année scolaire'), max_length=9, default='2024-2025')
    
    # Dates
    date_debut = models.DateField(_('date de début'))
    date_fin = models.DateField(_('date de fin'))
    date_publication_resultats = models.DateField(_('date de publication des résultats'), null=True, blank=True)
    
    # Configuration
    moyenne_admission = models.DecimalField(_('moyenne d\'admission'), max_digits=5, decimal_places=2, default=10.00)
    matieres = models.ManyToManyField(Matiere, related_name='examens_sessions')
    
    # Statistiques
    nombre_inscrits = models.PositiveIntegerField(_('nombre d\'inscrits'), default=0)
    nombre_admis = models.PositiveIntegerField(_('nombre d\'admis'), default=0)
    nombre_refuses = models.PositiveIntegerField(_('nombre de refusés'), default=0)
    taux_reussite = models.DecimalField(_('taux de réussite (%)'), max_digits=5, decimal_places=2, default=0.00)
    
    # Statut
    is_ouvert = models.BooleanField(_('ouvert aux inscriptions'), default=True)
    is_termine = models.BooleanField(_('terminé'), default=False)
    resultats_publies = models.BooleanField(_('résultats publiés'), default=False)
    
    # Description
    description = models.TextField(_('description'), blank=True)
    instructions = models.TextField(_('instructions'), blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Session d\'examen')
        verbose_name_plural = _('Sessions d\'examens')
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.get_type_examen_display()} - {self.get_session_display()} {self.annee_scolaire}"


class InscriptionExamen(models.Model):
    """Inscription d'un élève à une session d'examen"""
    
    class StatutInscription(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        CONFIRMEE = 'confirmee', _('Confirmée')
        ANNULEE = 'annulee', _('Annulée')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ExamenSession, on_delete=models.CASCADE, related_name='inscriptions')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscriptions_examens', limit_choices_to={'role': 'eleve'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='inscriptions_examens')
    
    # Informations d'inscription
    numero_inscription = models.CharField(_('numéro d\'inscription'), max_length=50, unique=True)
    date_inscription = models.DateField(_('date d\'inscription'), auto_now_add=True)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutInscription.choices, default=StatutInscription.EN_ATTENTE)
    
    # Résultats
    moyenne_obtenue = models.DecimalField(_('moyenne obtenue'), max_digits=5, decimal_places=2, null=True, blank=True)
    est_admis = models.BooleanField(_('admis'), null=True, blank=True)
    
    # Décision finale
    decision_jury = models.CharField(_('décision du jury'), max_length=50, blank=True)
    observations = models.TextField(_('observations'), blank=True)
    
    class Meta:
        verbose_name = _('Inscription à l\'examen')
        verbose_name_plural = _('Inscriptions aux examens')
        unique_together = ['session', 'eleve']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.session}"
    
    def save(self, *args, **kwargs):
        if not self.numero_inscription:
            import random
            annee = self.session.annee_scolaire[:4]
            type_code = self.session.type_examen[:3].upper()
            random_part = str(random.randint(100000, 999999))
            self.numero_inscription = f"{type_code}-{annee}-{random_part}"
        super().save(*args, **kwargs)


class CopieExamenPhysique(models.Model):
    """Gestion des copies physiques d'examen (pour correction IA OCR)"""
    
    class StatutCorrection(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours de correction')
        CORRIGEE = 'corrigee', _('Corrigée')
        VERIFIEE = 'verifiee', _('Vérifiée')
        ANNULEE = 'annulee', _('Annulée')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inscription = models.ForeignKey(InscriptionExamen, on_delete=models.CASCADE, related_name='copies')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='copies_examens')
    
    # Image de la copie
    image_copie = models.ImageField(_('image de la copie'), upload_to='examens/copies/')
    images_supplementaires = models.JSONField(_('images supplémentaires'), blank=True, null=True)
    
    # OCR et correction IA
    texte_extrait = models.TextField(_('texte extrait (OCR)'), blank=True)
    correction_ia = models.JSONField(_('correction IA'), blank=True, null=True)
    note_suggeree_ia = models.DecimalField(_('note suggérée par l\'IA'), max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Correction finale
    note_finale = models.DecimalField(_('note finale'), max_digits=5, decimal_places=2, null=True, blank=True)
    appreciation = models.TextField(_('appréciation'), blank=True)
    annotations_correcteur = models.TextField(_('annotations du correcteur'), blank=True)
    
    # Statut
    statut = models.CharField(_('statut'), max_length=20, choices=StatutCorrection.choices, default=StatutCorrection.EN_ATTENTE)
    
    # Correcteurs
    corrige_par_ia = models.BooleanField(_('corrigé par IA'), default=False)
    verifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='copies_verifiees', limit_choices_to={'role': 'professeur'})
    
    # Dates
    date_soumission = models.DateTimeField(_('date de soumission'), auto_now_add=True)
    date_correction_ia = models.DateTimeField(_('date correction IA'), null=True, blank=True)
    date_verification = models.DateTimeField(_('date de vérification'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Copie d\'examen physique')
        verbose_name_plural = _('Copies d\'examens physiques')
        unique_together = ['inscription', 'matiere']
    
    def __str__(self):
        return f"Copie {self.inscription.eleve.get_full_name()} - {self.matiere.nom}"


class HistoriqueCertificat(models.Model):
    """Historique des vérifications de certificats"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificat = models.ForeignKey(CertificatScolaire, on_delete=models.CASCADE, related_name='historique_verifications')
    
    # Informations de vérification
    code_verification = models.CharField(_('code de vérification utilisé'), max_length=20)
    resultat_verification = models.BooleanField(_('résultat de la vérification'))
    
    # Informations du vérificateur
    ip_verificateur = models.GenericIPAddressField(_('IP du vérificateur'), null=True, blank=True)
    date_verification = models.DateTimeField(_('date de vérification'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Historique de vérification')
        verbose_name_plural = _('Historiques de vérifications')
        ordering = ['-date_verification']
    
    def __str__(self):
        return f"Vérification {self.certificat.numero_certificat} - {self.date_verification}"
