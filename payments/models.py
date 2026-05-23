"""
Modèles pour la gestion des frais et paiements scolaires
Adapté au contexte béninois (Francs CFA - XOF)
"""

import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.models import Organisation


class FraisScolaire(models.Model):
    """Types de frais scolaires"""
    
    class TypeFrais(models.TextChoices):
        INSCRIPTION = 'inscription', _('Frais d\'inscription')
        SCOLARITE = 'scolarite', _('Frais de scolarité')
        EXAMEN = 'examen', _('Frais d\'examen')
        UNIFORME = 'uniforme', _('Uniforme')
        TRANSPORT = 'transport', _('Transport scolaire')
        RESTAURATION = 'restauration', _('Cantine / Restauration')
        FOURNITURES = 'fournitures', _('Fournitures scolaires')
        ASSURANCE = 'assurance', _('Assurance')
        CLUB = 'club', _('Activités parascolaires')
        AUTRE = 'autre', _('Autres frais')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='frais_scolaires')
    
    code = models.CharField(_('code'), max_length=20, unique=True)
    nom = models.CharField(_('nom'), max_length=200)
    type_frais = models.CharField(_('type de frais'), max_length=20, choices=TypeFrais.choices)
    description = models.TextField(_('description'), blank=True)
    
    # Montant
    montant = models.DecimalField(_('montant (XOF)'), max_digits=12, decimal_places=0, default=0)
    est_obligatoire = models.BooleanField(_('frais obligatoire'), default=True)
    
    # Applicabilité
    classes_concernees = models.JSONField(_('classes concernées'), blank=True, null=True, help_text="Liste des noms de classes")
    niveaux_concernes = models.JSONField(_('niveaux concernés'), blank=True, null=True)
    
    # Paiement
    est_paiement_unique = models.BooleanField(_('paiement unique'), default=False)
    nombre_echeances = models.PositiveIntegerField(_('nombre d\'échéances'), default=1)
    
    is_actif = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Frais scolaire')
        verbose_name_plural = _('Frais scolaires')
        ordering = ['type_frais', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.montant:,.0f} FCFA"


class Paiement(models.Model):
    """Paiements effectués par les élèves"""
    
    class ModePaiement(models.TextChoices):
        ESPECES = 'especes', _('Espèces')
        CHEQUE = 'cheque', _('Chèque')
        VIREMENT = 'virement', _('Virement bancaire')
        MOMO = 'momo', _('Mobile Money (MoMo)')
        OM = 'om', _('Orange Money')
        WAVE = 'wave', _('Wave')
        CARTE = 'carte', _('Carte bancaire')
        
    class StatutPaiement(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        PARTIEL = 'partiel', _('Paiement partiel')
        COMPLET = 'complet', _('Paiement complet')
        EN_RETARD = 'en_retard', _('En retard')
        ANNULE = 'annule', _('Annulé')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_paiement = models.CharField(_('numéro de paiement'), max_length=50, unique=True)
    
    # Relations
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='paiements', limit_choices_to={'role': 'eleve'})
    frais = models.ForeignKey(FraisScolaire, on_delete=models.CASCADE, related_name='paiements')
    classe = models.ForeignKey('core.Classe', on_delete=models.SET_NULL, null=True, blank=True, related_name='paiements')
    annee_scolaire = models.CharField(_('année scolaire'), max_length=9, default='2024-2025')
    
    # Montants
    montant_total = models.DecimalField(_('montant total (XOF)'), max_digits=12, decimal_places=0)
    montant_paye = models.DecimalField(_('montant payé (XOF)'), max_digits=12, decimal_places=0, default=0)
    montant_restant = models.DecimalField(_('montant restant (XOF)'), max_digits=12, decimal_places=0)
    
    # Paiement
    mode_paiement = models.CharField(_('mode de paiement'), max_length=20, choices=ModePaiement.choices)
    reference_paiement = models.CharField(_('référence'), max_length=100, blank=True)
    
    # Dates
    date_paiement = models.DateField(_('date de paiement'))
    date_echeance = models.DateField(_('date d\'échéance'), null=True, blank=True)
    
    # Statut
    statut = models.CharField(_('statut'), max_length=20, choices=StatutPaiement.choices, default=StatutPaiement.EN_ATTENTE)
    
    # Reçu
    reçu_genere = models.BooleanField(_('reçu généré'), default=False)
    date_reçu = models.DateTimeField(_('date du reçu'), null=True, blank=True)
    
    # Remise
    taux_remise = models.DecimalField(_('taux de remise (%)'), max_digits=5, decimal_places=2, default=0)
    montant_remise = models.DecimalField(_('montant remise (XOF)'), max_digits=12, decimal_places=0, default=0)
    motif_remise = models.TextField(_('motif de la remise'), blank=True)
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    # Métadonnées
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='paiements_crees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-date_paiement']
    
    def __str__(self):
        return f"{self.numero_paiement} - {self.eleve.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.numero_paiement:
            import random
            annee = self.annee_scolaire[:4]
            random_part = str(random.randint(10000, 99999))
            self.numero_paiement = f"PAI-{annee}-{random_part}"
        
        # Calculer le montant restant
        montant_apres_remise = self.montant_total - self.montant_remise
        self.montant_restant = montant_apres_remise - self.montant_paye
        
        # Mettre à jour le statut
        if self.montant_restant <= 0:
            self.statut = self.StatutPaiement.COMPLET
            self.montant_restant = 0
        elif self.montant_paye > 0:
            self.statut = self.StatutPaiement.PARTIEL
        
        super().save(*args, **kwargs)


class EcheancierPaiement(models.Model):
    """Échéancier de paiement pour un frais"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE, related_name='echeanciers')
    
    numero_echeance = models.PositiveIntegerField(_('numéro d\'échéance'))
    montant = models.DecimalField(_('montant (XOF)'), max_digits=12, decimal_places=0)
    date_echeance = models.DateField(_('date d\'échéance'))
    
    is_paye = models.BooleanField(_('payé'), default=False)
    date_paiement = models.DateField(_('date de paiement effectif'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Échéance')
        verbose_name_plural = _('Échéances')
        ordering = ['numero_echeance']
        unique_together = ['paiement', 'numero_echeance']
    
    def __str__(self):
        return f"Échéance {self.numero_echeance} - {self.paiement}"


class TransactionPaiement(models.Model):
    """Historique des transactions de paiement"""
    
    class TypeTransaction(models.TextChoices):
        PAIEMENT = 'paiement', _('Paiement')
        REMBOURSEMENT = 'remboursement', _('Remboursement')
        AVANCE = 'avance', _('Avance')
        REGULARISATION = 'regularisation', _('Régularisation')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE, related_name='transactions')
    
    type_transaction = models.CharField(_('type'), max_length=20, choices=TypeTransaction.choices)
    montant = models.DecimalField(_('montant (XOF)'), max_digits=12, decimal_places=0)
    
    mode_paiement = models.CharField(_('mode de paiement'), max_length=20, choices=Paiement.ModePaiement.choices)
    reference_transaction = models.CharField(_('référence'), max_length=100, blank=True)
    
    date_transaction = models.DateTimeField(_('date de transaction'), auto_now_add=True)
    
    # Opérateur de paiement mobile
    operateur = models.CharField(_('opérateur'), max_length=50, blank=True)
    numero_telephone = models.CharField(_('numéro de téléphone'), max_length=20, blank=True)
    
    # Statut
    est_reussi = models.BooleanField(_('transaction réussie'), default=True)
    message_erreur = models.TextField(_('message d\'erreur'), blank=True)
    
    # Métadonnées
    ip_transaction = models.GenericIPAddressField(_('IP'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-date_transaction']
    
    def __str__(self):
        return f"{self.type_transaction} - {self.montant:,.0f} FCFA"


class BourseScolaire(models.Model):
    """Bourses scolaires pour les élèves méritants ou démunis"""
    
    class TypeBourse(models.TextChoices):
        EXCELLENCE = 'excellence', _('Bourse d\'excellence')
        MERITE = 'merite', _('Bourse au mérite')
        SOCIALE = 'sociale', _('Bourse sociale')
        SPORT = 'sport', _('Bourse sportive')
        CULTURE = 'culture', _('Bourse culturelle')
    
    class StatutBourse(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        ATTRIBUEE = 'attribuee', _('Attribuée')
        SUSPENDUE = 'suspendue', _('Suspendue')
        TERMINEE = 'terminee', _('Terminée')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bourses', limit_choices_to={'role': 'eleve'})
    
    type_bourse = models.CharField(_('type de bourse'), max_length=20, choices=TypeBourse.choices)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutBourse.choices, default=StatutBourse.EN_ATTENTE)
    
    # Montant
    montant_mensuel = models.DecimalField(_('montant mensuel (XOF)'), max_digits=12, decimal_places=0)
    duree_mois = models.PositiveIntegerField(_('durée (mois)'), default=12)
    montant_total = models.DecimalField(_('montant total (XOF)'), max_digits=12, decimal_places=0)
    
    # Critères
    moyenne_minimale = models.DecimalField(_('moyenne minimale requise'), max_digits=5, decimal_places=2, null=True, blank=True)
    revenu_familial_max = models.DecimalField(_('revenu familial max (XOF)'), max_digits=12, decimal_places=0, null=True, blank=True)
    
    # Documents
    documents_demande = models.JSONField(_('documents de la demande'), blank=True, null=True)
    
    # Commentaires
    motivation = models.TextField(_('motivation de la demande'))
    decision_comite = models.TextField(_('décision du comité'), blank=True)
    
    # Dates
    date_demande = models.DateField(_('date de demande'), auto_now_add=True)
    date_decision = models.DateField(_('date de décision'), null=True, blank=True)
    date_debut = models.DateField(_('date de début'), null=True, blank=True)
    date_fin = models.DateField(_('date de fin'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Bourse scolaire')
        verbose_name_plural = _('Bourses scolaires')
        ordering = ['-date_demande']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.get_type_bourse_display()}"


class RapportFinancier(models.Model):
    """Rapports financiers périodiques"""
    
    class TypeRapport(models.TextChoices):
        MENSUEL = 'mensuel', _('Mensuel')
        TRIMESTRIEL = 'trimestriel', _('Trimestriel')
        ANNUEL = 'annuel', _('Annuel')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='rapports_financiers')
    
    type_rapport = models.CharField(_('type de rapport'), max_length=20, choices=TypeRapport.choices)
    periode_debut = models.DateField(_('début de période'))
    periode_fin = models.DateField(_('fin de période'))
    
    # Statistiques
    total_encaisse = models.DecimalField(_('total encaissé (XOF)'), max_digits=15, decimal_places=0, default=0)
    total_attendu = models.DecimalField(_('total attendu (XOF)'), max_digits=15, decimal_places=0, default=0)
    total_impaye = models.DecimalField(_('total impayé (XOF)'), max_digits=15, decimal_places=0, default=0)
    taux_recouvrement = models.DecimalField(_('taux de recouvrement (%)'), max_digits=5, decimal_places=2, default=0)
    
    nombre_paiements = models.PositiveIntegerField(_('nombre de paiements'), default=0)
    nombre_eleves_solvables = models.PositiveIntegerField(_('élèves à jour'), default=0)
    nombre_eleves_insolvables = models.PositiveIntegerField(_('élèves en retard'), default=0)
    
    # Détails par type de frais
    details_par_type = models.JSONField(_('détails par type de frais'), blank=True, null=True)
    
    # Document
    fichier_rapport = models.FileField(_('rapport PDF'), upload_to='finance/rapports/', blank=True, null=True)
    
    # Génération
    genere_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='rapports_financiers_generes')
    date_generation = models.DateTimeField(_('date de génération'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Rapport financier')
        verbose_name_plural = _('Rapports financiers')
        ordering = ['-periode_fin']
    
    def __str__(self):
        return f"Rapport {self.get_type_rapport_display()} - {self.periode_fin}"


# ═══════════════════════════════════════════════════════════════
# SYSTÈME D'ABONNEMENT SCOLAIRE - FEDAPAY
# ═══════════════════════════════════════════════════════════════

class PlanAbonnementScolaire(models.Model):
    """
    Plans d'abonnement scolaire configurables par le super admin
    Inspiré de Discord, Coursera, Netflix
    """
    
    class TypePlan(models.TextChoices):
        MENSUEL = 'mensuel', _('Mensuel')
        TRIMESTRIEL = 'trimestriel', _('Trimestriel')
        ANNUEL = 'annuel', _('Annuel')
        
    class NiveauPlan(models.TextChoices):
        BASIQUE = 'basique', _('Basique')
        STANDARD = 'standard', _('Standard')
        PREMIUM = 'premium', _('Premium')
        ELITE = 'elite', _('Élite')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='plans_abonnement')
    
    # Informations de base
    nom = models.CharField(_('nom du plan'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    niveau = models.CharField(_('niveau'), max_length=20, choices=NiveauPlan.choices, default=NiveauPlan.STANDARD)
    type_plan = models.CharField(_('type'), max_length=20, choices=TypePlan.choices, default=TypePlan.MENSUEL)
    
    # Prix (XOF)
    prix_mensuel = models.DecimalField(_('prix mensuel (XOF)'), max_digits=12, decimal_places=0)
    prix_annuel = models.DecimalField(_('prix annuel (XOF)'), max_digits=12, decimal_places=0, null=True, blank=True)
    
    # Réduction
    reduction_annuelle_pourcentage = models.DecimalField(_('réduction annuelle (%)'), max_digits=5, decimal_places=2, default=0)
    
    # Visuel
    couleur = models.CharField(_('couleur'), max_length=7, default='#3b82f6')
    icone = models.CharField(_('icône'), max_length=50, default='🎓')
    image_banniere = models.ImageField(_('image bannière'), upload_to='abonnements/bannieres/', blank=True, null=True)
    
    # Features / Avantages
    features = models.JSONField(_('avantages'), default=list, help_text="Liste des avantages ex: ['Accès illimité aux cours', 'Certificats premium']")
    limitations = models.JSONField(_('limitations'), default=list, blank=True, help_text="Limitations pour ce plan")
    
    # Configuration
    duree_jours = models.PositiveIntegerField(_('durée (jours)'), default=30)
    ordre_affichage = models.PositiveIntegerField(_('ordre d\'affichage'), default=1)
    
    # Mise en avant
    is_populaire = models.BooleanField(_('plan populaire'), default=False, help_text="Affiche le badge 'Plus populaire'")
    is_recommande = models.BooleanField(_('recommandé'), default=False, help_text="Affiche le badge 'Recommandé'")
    badge_special = models.CharField(_('badge spécial'), max_length=50, blank=True, help_text="Ex: 'Offre limitée', '-20%'")
    
    # Description
    description_courte = models.CharField(_('description courte'), max_length=200, blank=True)
    description_complete = models.TextField(_('description complète'), blank=True)
    
    # Statut
    is_actif = models.BooleanField(_('actif'), default=True)
    visible_sur_site = models.BooleanField(_('visible sur site'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Plan d\'abonnement scolaire')
        verbose_name_plural = _('Plans d\'abonnement scolaires')
        ordering = ['ordre_affichage', 'prix_mensuel']
    
    def __str__(self):
        return f"{self.nom} - {self.get_type_plan_display()}"
    
    @property
    def prix_annuel_affiche(self):
        """Calculer le prix annuel avec réduction"""
        if self.prix_annuel:
            return self.prix_annuel
        if self.reduction_annuelle_pourcentage > 0:
            reduction = (self.prix_mensuel * 12) * (self.reduction_annuelle_pourcentage / 100)
            return (self.prix_mensuel * 12) - reduction
        return self.prix_mensuel * 12
    
    @property
    def economie_annuelle(self):
        """Calculer l'économie annuelle"""
        return (self.prix_mensuel * 12) - self.prix_annuel_affiche


class AbonnementEleve(models.Model):
    """
    Abonnement d'un élève - Suivi des paiements et accès
    """
    
    class StatutAbonnement(models.TextChoices):
        ESSAI_GRATUIT = 'essai', _('Essai gratuit')
        ACTIF = 'actif', _('Actif')
        EN_ATTENTE = 'attente', _('En attente de paiement')
        EXPIRE = 'expire', _('Expiré')
        RESILIE = 'resilie', _('Résilié')
        SUSPENDU = 'suspendu', _('Suspendu')
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_abonnement = models.CharField(_('numéro d\'abonnement'), max_length=50, unique=True)
    
    # Relations
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='abonnements', limit_choices_to={'role': 'eleve'})
    plan = models.ForeignKey(PlanAbonnementScolaire, on_delete=models.PROTECT, related_name='abonnements')
    etablissement = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='abonnements_eleves')
    
    # Période
    date_debut = models.DateTimeField(_('date de début'))
    date_fin = models.DateTimeField(_('date de fin'))
    date_prochain_paiement = models.DateTimeField(_('prochain paiement'), null=True, blank=True)
    
    # Statut
    statut = models.CharField(_('statut'), max_length=20, choices=StatutAbonnement.choices, default=StatutAbonnement.EN_ATTENTE)
    is_renouvellement_auto = models.BooleanField(_('renouvellement automatique'), default=True)
    
    # Paiement
    dernier_paiement = models.DateTimeField(_('dernier paiement'), null=True, blank=True)
    montant_paye_total = models.DecimalField(_('total payé (XOF)'), max_digits=15, decimal_places=0, default=0)
    nombre_paiements = models.PositiveIntegerField(_('nombre de paiements'), default=0)
    
    # FedaPay
    fedapay_customer_id = models.CharField(_('FedaPay Customer ID'), max_length=100, blank=True)
    fedapay_subscription_id = models.CharField(_('FedaPay Subscription ID'), max_length=100, blank=True)
    
    # Historique
    date_souscription = models.DateTimeField(_('date de souscription'), auto_now_add=True)
    date_resiliation = models.DateTimeField(_('date de résiliation'), null=True, blank=True)
    motif_resiliation = models.TextField(_('motif de résiliation'), blank=True)
    
    # Notifications
    rappel_7j_envoye = models.BooleanField(_('rappel 7j envoyé'), default=False)
    rappel_3j_envoye = models.BooleanField(_('rappel 3j envoyé'), default=False)
    rappel_1j_envoye = models.BooleanField(_('rappel 1j envoyé'), default=False)
    
    class Meta:
        verbose_name = _('Abonnement élève')
        verbose_name_plural = _('Abonnements élèves')
        ordering = ['-date_souscription']
        # Un élève peut renouveler le même plan après résiliation, mais pas en avoir deux actifs simultanément
        constraints = [
            models.UniqueConstraint(
                fields=['eleve', 'plan'],
                condition=models.Q(statut='actif'),
                name='unique_abonnement_actif'
            )
        ]
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.plan.nom} ({self.get_statut_display()})"
    
    @property
    def jours_restants(self):
        """Nombre de jours restants avant expiration"""
        from django.utils import timezone
        from datetime import datetime
        
        if self.date_fin:
            diff = self.date_fin - timezone.now()
            return max(0, diff.days)
        return 0
    
    @property
    def est_actif(self):
        """Vérifier si l'abonnement est actif"""
        from django.utils import timezone
        return self.statut == self.StatutAbonnement.ACTIF and self.date_fin > timezone.now()
    
    def save(self, *args, **kwargs):
        if not self.numero_abonnement:
            import random
            from django.utils import timezone as tz
            annee = tz.now().year
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            self.numero_abonnement = f"ABN-{annee}-{random_part}"
        super().save(*args, **kwargs)


class PaiementAbonnement(models.Model):
    """
    Paiement d'abonnement via FedaPay
    """
    
    class StatutPaiement(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours')
        SUCCES = 'succes', _('Succès')
        ECHEC = 'echec', _('Échec')
        REMBOURSE = 'rembourse', _('Remboursé')
        ANNULE = 'annule', _('Annulé')
    
    class ModePaiement(models.TextChoices):
        MOBILE_MONEY = 'mobile_money', _('Mobile Money')
        CARTE_BANCAIRE = 'carte', _('Carte Bancaire')
        VIREMENT = 'virement', _('Virement')
        ESPECES = 'especes', _('Espèces')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_transaction = models.CharField(_('référence'), max_length=100, unique=True)
    
    # Relations
    abonnement = models.ForeignKey(AbonnementEleve, on_delete=models.CASCADE, related_name='paiements')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='paiements_abonnement')
    
    # Montant
    montant = models.DecimalField(_('montant (XOF)'), max_digits=12, decimal_places=0)
    frais_transaction = models.DecimalField(_('frais (XOF)'), max_digits=10, decimal_places=0, default=0)
    montant_total = models.DecimalField(_('montant total (XOF)'), max_digits=12, decimal_places=0)
    
    # Paiement
    mode_paiement = models.CharField(_('mode'), max_length=20, choices=ModePaiement.choices, default=ModePaiement.MOBILE_MONEY)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutPaiement.choices, default=StatutPaiement.EN_ATTENTE)
    
    # FedaPay
    fedapay_transaction_id = models.CharField(_('FedaPay Transaction ID'), max_length=100, blank=True)
    fedapay_url_paiement = models.URLField(_('URL de paiement FedaPay'), blank=True)
    fedapay_webhook_data = models.JSONField(_('données webhook'), blank=True, null=True)
    
    # Details
    telephone_paiement = models.CharField(_('téléphone'), max_length=20, blank=True)
    operateur = models.CharField(_('opérateur'), max_length=20, blank=True)  # MTN, MOOV, etc.
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(_('date de paiement'), null=True, blank=True)
    date_confirmation = models.DateTimeField(_('date de confirmation'), null=True, blank=True)
    
    # Reçu
    recu_pdf = models.FileField(_('reçu PDF'), upload_to='abonnements/recus/', blank=True, null=True)
    
    # Tentatives
    nombre_tentatives = models.PositiveIntegerField(_('tentatives'), default=0)
    derniere_erreur = models.TextField(_('dernière erreur'), blank=True)
    
    class Meta:
        verbose_name = _('Paiement d\'abonnement')
        verbose_name_plural = _('Paiements d\'abonnement')
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.reference_transaction} - {self.montant:,.0f} FCFA"


class ConfigurationFedaPay(models.Model):
    """
    Configuration FedaPay par établissement (configurée par super admin)
    """
    
    class Environnement(models.TextChoices):
        SANDBOX = 'sandbox', _('Sandbox - Test')
        PRODUCTION = 'production', _('Production')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='config_fedapay')
    
    # Clés API
    environnement = models.CharField(_('environnement'), max_length=20, choices=Environnement.choices, default=Environnement.SANDBOX)
    cle_api_publique = models.CharField(_('clé API publique'), max_length=200)
    cle_api_secrete = models.CharField(_('clé API secrète'), max_length=200)
    
    # Configuration
    nom_marchand = models.CharField(_('nom du marchand'), max_length=100)
    email_marchand = models.EmailField(_('email du marchand'))
    logo_url = models.URLField(_('URL du logo'), blank=True)
    
    # Webhook
    webhook_secret = models.CharField(_('secret webhook'), max_length=100, blank=True, help_text="Secret pour valider les webhooks FedaPay")
    webhook_url = models.URLField(_('URL webhook'), blank=True)
    
    # Paramètres
    devise = models.CharField(_('devise'), max_length=3, default='XOF')
    langue_par_defaut = models.CharField(_('langue'), max_length=10, default='fr')
    
    # Statut
    is_actif = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Configuration FedaPay')
        verbose_name_plural = _('Configurations FedaPay')
    
    def __str__(self):
        return f"FedaPay {self.etablissement.nom} ({self.get_environnement_display()})"


class PromotionAbonnement(models.Model):
    """
    Promotions et codes promo pour les abonnements
    """
    
    class TypeReduction(models.TextChoices):
        POURCENTAGE = 'pourcentage', _('Pourcentage (%)')
        MONTANT_FIXE = 'montant', _('Montant fixe (XOF)')
        MOIS_GRATUIT = 'mois_gratuit', _('Mois gratuit')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='promotions_abonnement')
    
    # Informations
    nom = models.CharField(_('nom'), max_length=100)
    code_promo = models.CharField(_('code promo'), max_length=20, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    # Réduction
    type_reduction = models.CharField(_('type'), max_length=20, choices=TypeReduction.choices)
    valeur_reduction = models.DecimalField(_('valeur'), max_digits=10, decimal_places=2)
    
    # Limites
    date_debut = models.DateTimeField(_('date de début'))
    date_fin = models.DateTimeField(_('date de fin'))
    nombre_utilisations_max = models.PositiveIntegerField(_('utilisations max'), null=True, blank=True)
    nombre_utilisations = models.PositiveIntegerField(_('utilisations'), default=0)
    
    # Applicabilité
    plans_applicables = models.ManyToManyField(PlanAbonnementScolaire, related_name='promotions', blank=True)
    
    # Visuel
    banniere = models.ImageField(_('bannière'), upload_to='abonnements/promotions/', blank=True, null=True)
    couleur_badge = models.CharField(_('couleur badge'), max_length=7, default='#ef4444')
    
    # Statut
    is_actif = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('Promotion abonnement')
        verbose_name_plural = _('Promotions abonnement')
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.nom} ({self.code_promo})"
    
    @property
    def est_valide(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_actif and
            self.date_debut <= now <= self.date_fin and
            (self.nombre_utilisations_max is None or self.nombre_utilisations < self.nombre_utilisations_max)
        )


# ═══════════════════════════════════════════════════════════════
# SYSTÈME DE COMMISSIONS & PAYOUTS AUTOMATIQUES
# ═══════════════════════════════════════════════════════════════

class ConfigurationCommission(models.Model):
    """
    Taux de commission et numéros de téléphone pour chaque bénéficiaire.
    Un seul enregistrement par établissement (OneToOne).
    Flux : Client paie → webhook → calcul parts → payout automatique
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.OneToOneField(
        Organisation, on_delete=models.CASCADE, related_name='config_commission'
    )

    # Taux (doivent totaliser 100 %)
    taux_admin = models.DecimalField(_('taux admin (%)'), max_digits=5, decimal_places=2, default=10)
    taux_commercial = models.DecimalField(_('taux commercial (%)'), max_digits=5, decimal_places=2, default=20)
    taux_prestataire = models.DecimalField(_('taux prestataire (%)'), max_digits=5, decimal_places=2, default=70)

    # Numéros Mobile Money des bénéficiaires
    telephone_admin = models.CharField(_('téléphone admin'), max_length=20)
    telephone_commercial = models.CharField(_('téléphone commercial'), max_length=20)
    telephone_prestataire = models.CharField(_('téléphone prestataire'), max_length=20)

    is_actif = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Configuration commission')
        verbose_name_plural = _('Configurations commission')

    def __str__(self):
        return f"Commissions {self.etablissement.nom} ({self.taux_admin}% / {self.taux_commercial}% / {self.taux_prestataire}%)"

    @property
    def total_taux(self):
        return float(self.taux_admin) + float(self.taux_commercial) + float(self.taux_prestataire)

    def clean(self):
        from django.core.exceptions import ValidationError
        total = float(self.taux_admin) + float(self.taux_commercial) + float(self.taux_prestataire)
        if abs(total - 100) > 0.01:
            raise ValidationError(
                f"La somme des taux doit être égale à 100 % (actuellement {total:.2f} %)."
            )

    def calculer_parts(self, montant_total: int) -> dict:
        """Retourne un dict avec la part de chaque bénéficiaire en entier XOF."""
        admin = int(montant_total * self.taux_admin / 100)
        commercial = int(montant_total * self.taux_commercial / 100)
        prestataire = montant_total - admin - commercial  # absorbe les arrondis
        return {
            'admin': admin,
            'commercial': commercial,
            'prestataire': prestataire,
        }


class PayoutCommission(models.Model):
    """
    Trace chaque virement envoyé à un bénéficiaire après paiement confirmé.
    Un paiement génère 3 lignes : admin, commercial, prestataire.
    """

    class Beneficiaire(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        COMMERCIAL = 'commercial', _('Commercial')
        PRESTATAIRE = 'prestataire', _('Prestataire')

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        ENVOYE = 'envoye', _('Envoyé')
        SUCCES = 'succes', _('Succès')
        ECHEC = 'echec', _('Échec')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paiement = models.ForeignKey(
        PaiementAbonnement, on_delete=models.CASCADE, related_name='payouts'
    )
    beneficiaire = models.CharField(_('bénéficiaire'), max_length=20, choices=Beneficiaire.choices)
    telephone = models.CharField(_('téléphone'), max_length=20)
    montant = models.DecimalField(_('montant (XOF)'), max_digits=12, decimal_places=0)
    taux_applique = models.DecimalField(_('taux appliqué (%)'), max_digits=5, decimal_places=2)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    fedapay_payout_id = models.CharField(_('FedaPay Payout ID'), max_length=100, blank=True)
    reponse_api = models.JSONField(_('réponse API'), blank=True, null=True)
    message_erreur = models.TextField(_('erreur'), blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(_('date de traitement'), blank=True, null=True)

    class Meta:
        verbose_name = _('Payout commission')
        verbose_name_plural = _('Payouts commissions')
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_beneficiaire_display()} — {self.montant:,.0f} FCFA ({self.get_statut_display()})"


class PaiementCorrectionUnitaire(models.Model):
    """
    Paiement ponctuel pour débloquer la correction IA d'UNE composition.
    Créé quand un élève sans abonnement actif clique sur "Payer maintenant"
    depuis la page paywall.
    """

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours')
        SUCCES = 'succes', _('Succès')
        ECHEC = 'echec', _('Échec')
        ANNULE = 'annule', _('Annulé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(_('référence'), max_length=100, unique=True)
    eleve = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='paiements_corrections'
    )
    session = models.ForeignKey(
        'compositions.CompositionSession', on_delete=models.CASCADE, related_name='paiements_correction'
    )
    montant = models.DecimalField(_('montant (XOF)'), max_digits=10, decimal_places=0)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    fedapay_transaction_id = models.CharField(_('FedaPay Transaction ID'), max_length=100, blank=True)
    fedapay_url_paiement = models.URLField(_('URL de paiement'), blank=True)
    fedapay_webhook_data = models.JSONField(_('données webhook'), blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(_('date de paiement'), blank=True, null=True)

    class Meta:
        verbose_name = _('Paiement correction unitaire')
        verbose_name_plural = _('Paiements correction unitaire')
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.reference} — {self.montant:,.0f} FCFA ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            import random
            self.reference = f"COR-{timezone.now().year}-{''.join([str(random.randint(0,9)) for _ in range(6)])}"
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════
# RÉPARTITION AUTOMATIQUE — PAIEMENTS CORRECTION UNITAIRE
# ═══════════════════════════════════════════════════════════════

class PayoutCorrectionUnitaire(models.Model):
    """
    Trace chaque virement envoyé suite à un paiement de correction unitaire.
    Un paiement → 4 lignes : dev1 (5%), dev2 (5%), entretien (40%), prof (50%).
    """

    class Beneficiaire(models.TextChoices):
        DEV1 = 'dev1', 'Développeur 1'
        DEV2 = 'dev2', 'Développeur 2'
        ENTRETIEN = 'entretien', 'Entretien plateforme'
        PROF = 'prof', 'Professeur'

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        ENVOYE = 'envoye', 'Envoyé'
        SUCCES = 'succes', 'Succès'
        ECHEC = 'echec', 'Échec'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paiement = models.ForeignKey(
        PaiementCorrectionUnitaire, on_delete=models.CASCADE,
        related_name='payouts'
    )
    beneficiaire = models.CharField(max_length=20, choices=Beneficiaire.choices)
    telephone = models.CharField(max_length=20)
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    taux_applique = models.DecimalField(max_digits=5, decimal_places=2)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    fedapay_payout_id = models.CharField(max_length=100, blank=True)
    reponse_api = models.JSONField(blank=True, null=True)
    message_erreur = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Payout correction unitaire'
        verbose_name_plural = 'Payouts correction unitaire'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_beneficiaire_display()} — {self.montant:,.0f} FCFA ({self.get_statut_display()})"


# ═══════════════════════════════════════════════════════════════
# TARIFS PAR TYPE DE CANDIDAT (définis par l'admin)
# ═══════════════════════════════════════════════════════════════

class ConfigTarifCandidature(models.Model):
    """
    L'admin définit les prix d'abonnement selon le type de candidat :
    - Candidat Académie Numérique (inscrit à l'académie)
    - Candidat Libre (externe, présente aux examens de son côté)
    """

    class TypeCandidat(models.TextChoices):
        ACADEMIE = 'academie', _('Candidat Académie Numérique')
        LIBRE = 'libre', _('Candidat Libre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(
        Organisation, on_delete=models.CASCADE,
        related_name='tarifs_candidature', null=True, blank=True,
        help_text="Laisser vide pour un tarif global (tous établissements)"
    )
    type_candidat = models.CharField(
        _('type de candidat'), max_length=20, choices=TypeCandidat.choices
    )

    # Tarifs abonnement
    tarif_mensuel = models.DecimalField(_('mensuel (XOF)'), max_digits=12, decimal_places=0, default=0)
    tarif_trimestriel = models.DecimalField(_('trimestriel (XOF)'), max_digits=12, decimal_places=0, default=0)
    tarif_annuel = models.DecimalField(_('annuel (XOF)'), max_digits=12, decimal_places=0, default=0)

    # Tarifs à l'unité (accès service par service)
    tarif_correction_unitaire = models.DecimalField(
        _('correction unitaire (XOF)'), max_digits=10, decimal_places=0, default=0,
        help_text="Prix pour corriger une copie sans abonnement"
    )
    tarif_qcm_unitaire = models.DecimalField(
        _('QCM unitaire (XOF)'), max_digits=10, decimal_places=0, default=0,
        help_text="Prix pour passer un QCM sans abonnement"
    )

    # Paiement échelonné
    paiement_echelonne_autorise = models.BooleanField(_('paiement par tranches autorisé'), default=True)
    nombre_tranches_max = models.PositiveIntegerField(_('nombre de tranches max'), default=3)

    is_actif = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Tarif par type de candidat')
        verbose_name_plural = _('Tarifs par type de candidat')
        unique_together = ['etablissement', 'type_candidat']
        ordering = ['type_candidat']

    def __str__(self):
        etab = self.etablissement.nom if self.etablissement else 'Global'
        return f"Tarifs {self.get_type_candidat_display()} — {etab}"

    @property
    def tarif_par_periode(self):
        return {
            'mensuel': int(self.tarif_mensuel),
            'trimestriel': int(self.tarif_trimestriel),
            'annuel': int(self.tarif_annuel),
        }


# ═══════════════════════════════════════════════════════════════
# PAIEMENT PAR TRANCHES (échelonnement)
# ═══════════════════════════════════════════════════════════════

class PlanEchelonnement(models.Model):
    """Plan de paiement échelonné lié à un abonnement élève."""

    class Statut(models.TextChoices):
        ACTIF = 'actif', _('En cours')
        SOLDE = 'solde', _('Soldé')
        ABANDONNE = 'abandonne', _('Abandonné')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    abonnement = models.OneToOneField(
        AbonnementEleve, on_delete=models.CASCADE, related_name='plan_echelonnement'
    )
    nombre_tranches = models.PositiveIntegerField(_('nombre de tranches'))
    montant_total = models.DecimalField(_('montant total (XOF)'), max_digits=12, decimal_places=0)
    montant_par_tranche = models.DecimalField(_('montant par tranche (XOF)'), max_digits=12, decimal_places=0)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.ACTIF)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Plan d\'échelonnement')
        verbose_name_plural = _('Plans d\'échelonnement')

    def __str__(self):
        return f"{self.abonnement.eleve.get_full_name()} — {self.nombre_tranches} tranches"

    @property
    def tranches_payees(self):
        return self.tranches.filter(statut=TranchePaiement.Statut.PAYE).count()

    @property
    def prochaine_tranche_impayee(self):
        return self.tranches.filter(
            statut__in=[TranchePaiement.Statut.EN_ATTENTE, TranchePaiement.Statut.EN_RETARD]
        ).order_by('numero').first()


class TranchePaiement(models.Model):
    """Une tranche individuelle d'un plan d'échelonnement."""

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('Paiement initié')
        PAYE = 'paye', _('Payé')
        EN_RETARD = 'en_retard', _('En retard')
        ANNULE = 'annule', _('Annulé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(PlanEchelonnement, on_delete=models.CASCADE, related_name='tranches')
    numero = models.PositiveIntegerField(_('numéro de tranche'))
    montant = models.DecimalField(_('montant (XOF)'), max_digits=12, decimal_places=0)
    date_echeance = models.DateField(_('date d\'échéance'))
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)

    # Lien vers le paiement FedaPay réel
    fedapay_transaction_id = models.CharField(_('FedaPay transaction ID'), max_length=100, blank=True)
    fedapay_url_paiement = models.URLField(_('URL de paiement'), blank=True)
    date_paiement = models.DateTimeField(_('date de paiement effectif'), null=True, blank=True)

    class Meta:
        verbose_name = _('Tranche de paiement')
        verbose_name_plural = _('Tranches de paiement')
        ordering = ['numero']
        unique_together = ['plan', 'numero']

    def __str__(self):
        return f"Tranche {self.numero}/{self.plan.nombre_tranches} — {self.montant:,.0f} FCFA ({self.get_statut_display()})"

    @property
    def est_en_retard(self):
        from datetime import date
        return self.statut == self.Statut.EN_ATTENTE and self.date_echeance < date.today()


# ═══════════════════════════════════════════════════════════════
# DOSSIER DE CANDIDATURE & DOCUMENTS
# ═══════════════════════════════════════════════════════════════

class DocumentRequis(models.Model):
    """
    Document requis pour l'inscription aux examens.
    Défini par l'admin par type de candidat.
    """

    class TypeCandidat(models.TextChoices):
        ACADEMIE = 'academie', _('Candidat Académie Numérique')
        LIBRE = 'libre', _('Candidat Libre')
        TOUS = 'tous', _('Tous les candidats')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(
        Organisation, on_delete=models.CASCADE,
        related_name='documents_requis', null=True, blank=True
    )
    type_candidat = models.CharField(
        _('pour quel type'), max_length=20, choices=TypeCandidat.choices, default=TypeCandidat.TOUS
    )
    nom = models.CharField(_('nom du document'), max_length=200)
    description = models.TextField(_('description / instructions'), blank=True)
    est_obligatoire = models.BooleanField(_('obligatoire'), default=True)
    formats_acceptes = models.CharField(
        _('formats acceptés'), max_length=100, default='PDF, JPG, PNG',
        help_text="Ex: PDF, JPG, PNG"
    )
    taille_max_mo = models.PositiveIntegerField(_('taille max (Mo)'), default=5)
    is_actif = models.BooleanField(_('actif'), default=True)
    ordre = models.PositiveIntegerField(_('ordre d\'affichage'), default=1)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Document requis')
        verbose_name_plural = _('Documents requis')
        ordering = ['ordre', 'nom']

    def __str__(self):
        obligatoire = '* ' if self.est_obligatoire else ''
        return f"{obligatoire}{self.nom} ({self.get_type_candidat_display()})"


class DossierCandidature(models.Model):
    """Dossier de candidature d'un élève pour les examens."""

    class Statut(models.TextChoices):
        INCOMPLET = 'incomplet', _('Incomplet')
        SOUMIS = 'soumis', _('Soumis — en attente de validation')
        VALIDE = 'valide', _('Validé')
        REJETE = 'rejete', _('Rejeté — corrections requises')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dossier_candidature'
    )
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.INCOMPLET)
    commentaire_admin = models.TextField(_('commentaire de l\'admin'), blank=True)
    date_soumission = models.DateTimeField(_('date de soumission'), null=True, blank=True)
    date_validation = models.DateTimeField(_('date de validation'), null=True, blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dossiers_valides'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Dossier de candidature')
        verbose_name_plural = _('Dossiers de candidature')
        ordering = ['-date_modification']

    def __str__(self):
        return f"Dossier {self.eleve.get_full_name()} — {self.get_statut_display()}"

    @property
    def est_complet(self):
        """Vérifie si tous les documents obligatoires ont été soumis."""
        type_c = getattr(self.eleve, 'type_candidat', 'non_defini')
        docs_requis = DocumentRequis.objects.filter(
            est_obligatoire=True, is_actif=True
        ).filter(
            models.Q(type_candidat='tous') | models.Q(type_candidat=type_c)
        )
        soumis_ids = set(
            self.soumissions.filter(
                statut__in=['en_attente', 'valide']
            ).values_list('document_requis_id', flat=True)
        )
        return all(str(d.id) in soumis_ids for d in docs_requis)


class SoumissionDocument(models.Model):
    """Document soumis par un élève dans son dossier."""

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente de validation')
        VALIDE = 'valide', _('Validé')
        REJETE = 'rejete', _('Rejeté')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dossier = models.ForeignKey(DossierCandidature, on_delete=models.CASCADE, related_name='soumissions')
    document_requis = models.ForeignKey(DocumentRequis, on_delete=models.CASCADE, related_name='soumissions')
    fichier = models.FileField(_('fichier'), upload_to='candidatures/documents/%Y/%m/')
    nom_fichier_original = models.CharField(_('nom original'), max_length=255, blank=True)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    commentaire_admin = models.TextField(_('commentaire admin'), blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents_valides'
    )
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(_('date de validation'), null=True, blank=True)

    class Meta:
        verbose_name = _('Document soumis')
        verbose_name_plural = _('Documents soumis')
        unique_together = ['dossier', 'document_requis']
        ordering = ['-date_soumission']

    def __str__(self):
        return f"{self.document_requis.nom} — {self.dossier.eleve.get_full_name()}"
