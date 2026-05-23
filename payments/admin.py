"""
Admin complet pour l'application Payments — Académie Numérique
Intègre : frais scolaires, paiements, abonnements FedaPay,
commissions, échelonnements, candidatures et documents.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count
from django.utils import timezone

from .models import (
    # Répartition correction unitaire
    PayoutCorrectionUnitaire,
    # Frais & paiements scolaires de base
    FraisScolaire,
    Paiement,
    EcheancierPaiement,
    TransactionPaiement,
    BourseScolaire,
    RapportFinancier,
    # Abonnements FedaPay
    PlanAbonnementScolaire,
    AbonnementEleve,
    PaiementAbonnement,
    ConfigurationFedaPay,
    PromotionAbonnement,
    # Commissions & payouts
    ConfigurationCommission,
    PayoutCommission,
    # Paiements unitaires
    PaiementCorrectionUnitaire,
    # Tarifs & candidatures
    ConfigTarifCandidature,
    PlanEchelonnement,
    TranchePaiement,
    DocumentRequis,
    DossierCandidature,
    SoumissionDocument,
)


# ═══════════════════════════════════════════════════════════════
# HELPERS : badges colorés réutilisables
# ═══════════════════════════════════════════════════════════════

STATUT_COLORS = {
    # Paiement
    'complet':      '#16a34a',
    'partiel':      '#ca8a04',
    'en_attente':   '#6b7280',
    'en_retard':    '#dc2626',
    'annule':       '#9ca3af',
    # Abonnement
    'actif':        '#16a34a',
    'expire':       '#dc2626',
    'resilie':      '#9ca3af',
    'suspendu':     '#f97316',
    'essai':        '#3b82f6',
    'attente':      '#6b7280',
    # Paiement abonnement / transaction
    'succes':       '#16a34a',
    'echec':        '#dc2626',
    'en_cours':     '#3b82f6',
    'rembourse':    '#8b5cf6',
    # Bourse
    'attribuee':    '#16a34a',
    'suspendue':    '#f97316',
    'terminee':     '#9ca3af',
    # Dossier
    'valide':       '#16a34a',
    'rejete':       '#dc2626',
    'soumis':       '#3b82f6',
    'incomplet':    '#ca8a04',
    # Payout
    'envoye':       '#3b82f6',
    # Tranche
    'paye':         '#16a34a',
    'solde':        '#16a34a',
    'abandonne':    '#9ca3af',
}


def badge(statut, label=None):
    """Retourne un badge HTML coloré pour un statut."""
    color = STATUT_COLORS.get(statut, '#6b7280')
    text = label or statut.replace('_', ' ').capitalize()
    return format_html(
        '<span style="background:{};color:#fff;padding:2px 8px;'
        'border-radius:12px;font-size:11px;font-weight:600">{}</span>',
        color, text
    )


def montant_fcfa(value):
    """Formate un montant en FCFA."""
    if value is None:
        return '—'
    return format_html('<strong>{:,.0f} FCFA</strong>', value)


# ═══════════════════════════════════════════════════════════════
# FRAIS SCOLAIRES
# ═══════════════════════════════════════════════════════════════

@admin.register(FraisScolaire)
class FraisScolaireAdmin(admin.ModelAdmin):
    list_display = [
        'nom', 'code', 'type_frais', 'afficher_montant',
        'est_obligatoire', 'nombre_echeances', 'is_actif',
    ]
    list_filter = ['type_frais', 'est_obligatoire', 'is_actif', 'etablissement']
    search_fields = ['nom', 'code', 'description']
    list_editable = ['is_actif']

    fieldsets = (
        (_('Identification'), {
            'fields': ('etablissement', 'code', 'nom', 'type_frais', 'description')
        }),
        (_('Montant & Paiement'), {
            'fields': ('montant', 'est_obligatoire', 'est_paiement_unique', 'nombre_echeances')
        }),
        (_('Applicabilité'), {
            'fields': ('classes_concernees', 'niveaux_concernes')
        }),
        (_('Statut'), {
            'fields': ('is_actif',)
        }),
    )

    @admin.display(description=_('Montant'))
    def afficher_montant(self, obj):
        return montant_fcfa(obj.montant)


# ═══════════════════════════════════════════════════════════════
# PAIEMENTS SCOLAIRES
# ═══════════════════════════════════════════════════════════════

class EcheancierInline(admin.TabularInline):
    model = EcheancierPaiement
    extra = 0
    fields = ['numero_echeance', 'montant', 'date_echeance', 'is_paye', 'date_paiement']
    readonly_fields = ['numero_echeance']


class TransactionInline(admin.TabularInline):
    model = TransactionPaiement
    extra = 0
    fields = ['type_transaction', 'montant', 'mode_paiement', 'reference_transaction', 'est_reussi', 'date_transaction']
    readonly_fields = ['date_transaction']


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = [
        'numero_paiement', 'eleve', 'frais',
        'afficher_montant_total', 'afficher_montant_paye',
        'afficher_reste', 'afficher_statut', 'mode_paiement', 'date_paiement',
    ]
    list_filter = ['statut', 'mode_paiement', 'annee_scolaire', 'classe']
    search_fields = ['numero_paiement', 'eleve__last_name', 'eleve__email', 'reference_paiement']
    readonly_fields = ['numero_paiement', 'montant_restant', 'statut', 'date_creation', 'date_modification']
    date_hierarchy = 'date_paiement'
    inlines = [EcheancierInline, TransactionInline]

    fieldsets = (
        (_('Référence'), {
            'fields': ('numero_paiement', 'eleve', 'classe', 'annee_scolaire', 'cree_par')
        }),
        (_('Frais'), {
            'fields': ('frais',)
        }),
        (_('Montants'), {
            'fields': ('montant_total', 'montant_paye', 'montant_restant',
                       'taux_remise', 'montant_remise', 'motif_remise')
        }),
        (_('Paiement'), {
            'fields': ('mode_paiement', 'reference_paiement', 'date_paiement', 'date_echeance')
        }),
        (_('Statut & Reçu'), {
            'fields': ('statut', 'reçu_genere', 'date_reçu', 'notes')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Total'))
    def afficher_montant_total(self, obj):
        return montant_fcfa(obj.montant_total)

    @admin.display(description=_('Payé'))
    def afficher_montant_paye(self, obj):
        return montant_fcfa(obj.montant_paye)

    @admin.display(description=_('Reste'))
    def afficher_reste(self, obj):
        color = '#dc2626' if obj.montant_restant > 0 else '#16a34a'
        return format_html('<span style="color:{};font-weight:600">{:,.0f} FCFA</span>',
                           color, obj.montant_restant)

    @admin.display(description=_('Statut'))
    def afficher_statut(self, obj):
        return badge(obj.statut, obj.get_statut_display())


@admin.register(EcheancierPaiement)
class EcheancierPaiementAdmin(admin.ModelAdmin):
    list_display = ['paiement', 'numero_echeance', 'afficher_montant', 'date_echeance', 'is_paye', 'date_paiement']
    list_filter = ['is_paye', 'date_echeance']
    search_fields = ['paiement__numero_paiement', 'paiement__eleve__email']

    @admin.display(description=_('Montant'))
    def afficher_montant(self, obj):
        return montant_fcfa(obj.montant)


@admin.register(TransactionPaiement)
class TransactionPaiementAdmin(admin.ModelAdmin):
    list_display = [
        'paiement', 'type_transaction', 'afficher_montant',
        'mode_paiement', 'operateur', 'afficher_statut_tx', 'date_transaction',
    ]
    list_filter = ['type_transaction', 'mode_paiement', 'est_reussi']
    search_fields = ['paiement__numero_paiement', 'reference_transaction']
    readonly_fields = ['date_transaction']

    @admin.display(description=_('Montant'))
    def afficher_montant(self, obj):
        return montant_fcfa(obj.montant)

    @admin.display(description=_('Résultat'), boolean=True)
    def afficher_statut_tx(self, obj):
        return obj.est_reussi


# ═══════════════════════════════════════════════════════════════
# BOURSES SCOLAIRES
# ═══════════════════════════════════════════════════════════════

@admin.register(BourseScolaire)
class BourseScolaireAdmin(admin.ModelAdmin):
    list_display = [
        'eleve', 'type_bourse', 'afficher_statut_bourse',
        'afficher_mensuel', 'duree_mois', 'afficher_total',
        'date_demande', 'date_decision',
    ]
    list_filter = ['type_bourse', 'statut']
    search_fields = ['eleve__email', 'eleve__first_name', 'eleve__last_name']
    date_hierarchy = 'date_demande'
    readonly_fields = ['date_demande']

    fieldsets = (
        (_('Élève & Type'), {
            'fields': ('eleve', 'type_bourse', 'statut')
        }),
        (_('Montants'), {
            'fields': ('montant_mensuel', 'duree_mois', 'montant_total')
        }),
        (_('Critères d\'éligibilité'), {
            'fields': ('moyenne_minimale', 'revenu_familial_max')
        }),
        (_('Demande'), {
            'fields': ('motivation', 'documents_demande', 'date_demande')
        }),
        (_('Décision'), {
            'fields': ('decision_comite', 'date_decision', 'date_debut', 'date_fin')
        }),
    )

    @admin.display(description=_('Statut'))
    def afficher_statut_bourse(self, obj):
        return badge(obj.statut, obj.get_statut_display())

    @admin.display(description=_('Mensuel'))
    def afficher_mensuel(self, obj):
        return montant_fcfa(obj.montant_mensuel)

    @admin.display(description=_('Total'))
    def afficher_total(self, obj):
        return montant_fcfa(obj.montant_total)


# ═══════════════════════════════════════════════════════════════
# RAPPORTS FINANCIERS
# ═══════════════════════════════════════════════════════════════

@admin.register(RapportFinancier)
class RapportFinancierAdmin(admin.ModelAdmin):
    list_display = [
        'etablissement', 'type_rapport', 'periode_debut', 'periode_fin',
        'afficher_encaisse', 'afficher_attendu', 'afficher_taux',
        'nombre_paiements', 'date_generation',
    ]
    list_filter = ['type_rapport', 'etablissement']
    search_fields = ['etablissement__nom']
    readonly_fields = ['date_generation', 'taux_recouvrement']
    date_hierarchy = 'periode_fin'

    fieldsets = (
        (_('Rapport'), {
            'fields': ('etablissement', 'type_rapport', 'periode_debut', 'periode_fin')
        }),
        (_('Statistiques'), {
            'fields': ('total_encaisse', 'total_attendu', 'total_impaye',
                       'taux_recouvrement', 'nombre_paiements',
                       'nombre_eleves_solvables', 'nombre_eleves_insolvables')
        }),
        (_('Détails & Document'), {
            'fields': ('details_par_type', 'fichier_rapport')
        }),
        (_('Génération'), {
            'fields': ('genere_par', 'date_generation'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Encaissé'))
    def afficher_encaisse(self, obj):
        return montant_fcfa(obj.total_encaisse)

    @admin.display(description=_('Attendu'))
    def afficher_attendu(self, obj):
        return montant_fcfa(obj.total_attendu)

    @admin.display(description=_('Recouvrement'))
    def afficher_taux(self, obj):
        color = '#16a34a' if obj.taux_recouvrement >= 80 else '#dc2626'
        return format_html('<strong style="color:{}">{:.1f}%</strong>', color, obj.taux_recouvrement)


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION FEDAPAY
# ═══════════════════════════════════════════════════════════════

@admin.register(ConfigurationFedaPay)
class ConfigurationFedaPayAdmin(admin.ModelAdmin):
    list_display = ['etablissement', 'nom_marchand', 'afficher_env', 'devise', 'is_actif', 'date_creation']
    list_filter = ['environnement', 'is_actif']
    search_fields = ['etablissement__nom', 'nom_marchand', 'email_marchand']

    fieldsets = (
        (_('Établissement'), {
            'fields': ('etablissement',)
        }),
        (_('Clés API FedaPay'), {
            'fields': ('environnement', 'cle_api_publique', 'cle_api_secrete'),
            'description': '⚠️ Clés sensibles — ne jamais partager en clair.'
        }),
        (_('Informations Marchand'), {
            'fields': ('nom_marchand', 'email_marchand', 'logo_url')
        }),
        (_('Webhook'), {
            'fields': ('webhook_secret', 'webhook_url'),
            'classes': ('collapse',)
        }),
        (_('Paramètres'), {
            'fields': ('devise', 'langue_par_defaut', 'is_actif')
        }),
    )

    @admin.display(description=_('Environnement'))
    def afficher_env(self, obj):
        color = '#dc2626' if obj.environnement == 'production' else '#3b82f6'
        return format_html('<span style="color:{};font-weight:700">{}</span>',
                           color, obj.get_environnement_display())


# ═══════════════════════════════════════════════════════════════
# PLANS D'ABONNEMENT
# ═══════════════════════════════════════════════════════════════

@admin.register(PlanAbonnementScolaire)
class PlanAbonnementScolaireAdmin(admin.ModelAdmin):
    list_display = [
        'nom', 'afficher_niveau', 'etablissement',
        'afficher_prix_mensuel', 'afficher_prix_annuel',
        'is_populaire', 'is_recommande', 'is_actif', 'ordre_affichage',
    ]
    list_filter = ['niveau', 'type_plan', 'is_populaire', 'is_recommande', 'is_actif', 'etablissement']
    search_fields = ['nom', 'slug', 'description_courte']
    prepopulated_fields = {'slug': ('nom',)}
    list_editable = ['is_actif', 'ordre_affichage']

    fieldsets = (
        (_('Identification'), {
            'fields': ('etablissement', 'nom', 'slug', 'niveau', 'type_plan', 'icone')
        }),
        (_('Tarification'), {
            'fields': ('prix_mensuel', 'prix_annuel', 'reduction_annuelle_pourcentage', 'duree_jours')
        }),
        (_('Contenu'), {
            'fields': ('description_courte', 'description_complete', 'features', 'limitations')
        }),
        (_('Mise en avant'), {
            'fields': ('is_populaire', 'is_recommande', 'badge_special', 'couleur', 'image_banniere', 'ordre_affichage')
        }),
        (_('Statut'), {
            'fields': ('is_actif', 'visible_sur_site')
        }),
    )

    @admin.display(description=_('Niveau'))
    def afficher_niveau(self, obj):
        colors = {
            'basique': '#6b7280', 'standard': '#3b82f6',
            'premium': '#f59e0b', 'elite': '#8b5cf6',
        }
        color = colors.get(obj.niveau, '#6b7280')
        return format_html('<span style="color:{};font-weight:700">{}</span>',
                           color, obj.get_niveau_display())

    @admin.display(description=_('Prix / mois'))
    def afficher_prix_mensuel(self, obj):
        return montant_fcfa(obj.prix_mensuel)

    @admin.display(description=_('Prix / an'))
    def afficher_prix_annuel(self, obj):
        return montant_fcfa(obj.prix_annuel_affiche)


# ═══════════════════════════════════════════════════════════════
# ABONNEMENTS ÉLÈVES
# ═══════════════════════════════════════════════════════════════

@admin.register(AbonnementEleve)
class AbonnementEleveAdmin(admin.ModelAdmin):
    list_display = [
        'numero_abonnement', 'eleve', 'plan',
        'afficher_statut_abonnement', 'afficher_jours',
        'afficher_total_paye', 'is_renouvellement_auto',
    ]
    list_filter = ['statut', 'plan__niveau', 'is_renouvellement_auto', 'etablissement']
    search_fields = ['numero_abonnement', 'eleve__first_name', 'eleve__last_name', 'eleve__email']
    readonly_fields = ['numero_abonnement', 'date_souscription', 'montant_paye_total', 'nombre_paiements']
    date_hierarchy = 'date_souscription'

    fieldsets = (
        (_('Identification'), {
            'fields': ('numero_abonnement', 'eleve', 'plan', 'etablissement', 'statut')
        }),
        (_('Période'), {
            'fields': ('date_debut', 'date_fin', 'date_prochain_paiement', 'is_renouvellement_auto')
        }),
        (_('Compteurs paiement'), {
            'fields': ('dernier_paiement', 'montant_paye_total', 'nombre_paiements')
        }),
        (_('FedaPay'), {
            'fields': ('fedapay_customer_id', 'fedapay_subscription_id'),
            'classes': ('collapse',)
        }),
        (_('Rappels envoyés'), {
            'fields': ('rappel_7j_envoye', 'rappel_3j_envoye', 'rappel_1j_envoye'),
            'classes': ('collapse',)
        }),
        (_('Résiliation'), {
            'fields': ('date_souscription', 'date_resiliation', 'motif_resiliation'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Statut'))
    def afficher_statut_abonnement(self, obj):
        return badge(obj.statut, obj.get_statut_display())

    @admin.display(description=_('Jours restants'))
    def afficher_jours(self, obj):
        j = obj.jours_restants
        color = '#16a34a' if j > 7 else ('#f97316' if j > 0 else '#dc2626')
        return format_html('<span style="color:{};font-weight:600">{} j</span>', color, j)

    @admin.display(description=_('Total payé'))
    def afficher_total_paye(self, obj):
        return montant_fcfa(obj.montant_paye_total)


# ═══════════════════════════════════════════════════════════════
# PAIEMENTS D'ABONNEMENT (FedaPay)
# ═══════════════════════════════════════════════════════════════

@admin.register(PaiementAbonnement)
class PaiementAbonnementAdmin(admin.ModelAdmin):
    list_display = [
        'reference_transaction', 'eleve',
        'afficher_montant_abo', 'mode_paiement',
        'operateur', 'afficher_statut_abo', 'date_creation',
    ]
    list_filter = ['statut', 'mode_paiement', 'operateur', 'date_creation']
    search_fields = ['reference_transaction', 'eleve__email', 'fedapay_transaction_id']
    readonly_fields = ['reference_transaction', 'date_creation', 'date_paiement', 'date_confirmation']
    date_hierarchy = 'date_creation'

    fieldsets = (
        (_('Référence'), {
            'fields': ('reference_transaction', 'abonnement', 'eleve', 'statut')
        }),
        (_('Montants'), {
            'fields': ('montant', 'frais_transaction', 'montant_total')
        }),
        (_('Paiement'), {
            'fields': ('mode_paiement', 'telephone_paiement', 'operateur')
        }),
        (_('FedaPay'), {
            'fields': ('fedapay_transaction_id', 'fedapay_url_paiement', 'fedapay_webhook_data'),
            'classes': ('collapse',)
        }),
        (_('Reçu'), {
            'fields': ('recu_pdf',)
        }),
        (_('Tentatives & Erreurs'), {
            'fields': ('nombre_tentatives', 'derniere_erreur'),
            'classes': ('collapse',)
        }),
        (_('Horodatage'), {
            'fields': ('date_creation', 'date_paiement', 'date_confirmation'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Montant'))
    def afficher_montant_abo(self, obj):
        return montant_fcfa(obj.montant)

    @admin.display(description=_('Statut'))
    def afficher_statut_abo(self, obj):
        return badge(obj.statut, obj.get_statut_display())


# ═══════════════════════════════════════════════════════════════
# PROMOTIONS
# ═══════════════════════════════════════════════════════════════

@admin.register(PromotionAbonnement)
class PromotionAbonnementAdmin(admin.ModelAdmin):
    list_display = [
        'nom', 'code_promo', 'type_reduction', 'afficher_valeur',
        'afficher_validite', 'nombre_utilisations', 'nombre_utilisations_max', 'is_actif',
    ]
    list_filter = ['type_reduction', 'is_actif']
    search_fields = ['nom', 'code_promo']
    filter_horizontal = ['plans_applicables']

    fieldsets = (
        (_('Informations'), {
            'fields': ('etablissement', 'nom', 'code_promo', 'description')
        }),
        (_('Réduction'), {
            'fields': ('type_reduction', 'valeur_reduction')
        }),
        (_('Validité'), {
            'fields': ('date_debut', 'date_fin', 'nombre_utilisations_max', 'nombre_utilisations')
        }),
        (_('Plans applicables'), {
            'fields': ('plans_applicables',)
        }),
        (_('Visuel'), {
            'fields': ('banniere', 'couleur_badge')
        }),
        (_('Statut'), {
            'fields': ('is_actif',)
        }),
    )

    @admin.display(description=_('Valeur réduction'))
    def afficher_valeur(self, obj):
        if obj.type_reduction == 'pourcentage':
            return format_html('<strong>-{:.0f}%</strong>', obj.valeur_reduction)
        elif obj.type_reduction == 'montant':
            return montant_fcfa(obj.valeur_reduction)
        return format_html('<strong>{} mois offert(s)</strong>', int(obj.valeur_reduction))

    @admin.display(description=_('Valide'), boolean=True)
    def afficher_validite(self, obj):
        return obj.est_valide


# ═══════════════════════════════════════════════════════════════
# COMMISSIONS & PAYOUTS
# ═══════════════════════════════════════════════════════════════

@admin.register(ConfigurationCommission)
class ConfigurationCommissionAdmin(admin.ModelAdmin):
    list_display = [
        'etablissement', 'afficher_taux_admin', 'afficher_taux_commercial',
        'afficher_taux_prestataire', 'afficher_total_taux', 'is_actif',
    ]
    list_filter = ['is_actif']
    search_fields = ['etablissement__nom']

    fieldsets = (
        (_('Établissement'), {
            'fields': ('etablissement', 'is_actif')
        }),
        (_('Taux de commission (total = 100 %)'), {
            'fields': ('taux_admin', 'taux_commercial', 'taux_prestataire'),
            'description': '⚠️ La somme des trois taux doit impérativement égaler 100 %.'
        }),
        (_('Numéros Mobile Money des bénéficiaires'), {
            'fields': ('telephone_admin', 'telephone_commercial', 'telephone_prestataire')
        }),
    )

    @admin.display(description=_('Admin (%)'))
    def afficher_taux_admin(self, obj):
        return format_html('<span style="color:#3b82f6;font-weight:600">{:.2f}%</span>', obj.taux_admin)

    @admin.display(description=_('Commercial (%)'))
    def afficher_taux_commercial(self, obj):
        return format_html('<span style="color:#f59e0b;font-weight:600">{:.2f}%</span>', obj.taux_commercial)

    @admin.display(description=_('Prestataire (%)'))
    def afficher_taux_prestataire(self, obj):
        return format_html('<span style="color:#8b5cf6;font-weight:600">{:.2f}%</span>', obj.taux_prestataire)

    @admin.display(description=_('Total'))
    def afficher_total_taux(self, obj):
        total = obj.total_taux
        color = '#16a34a' if abs(total - 100) < 0.01 else '#dc2626'
        return format_html('<strong style="color:{}">{:.2f}%</strong>', color, total)


@admin.register(PayoutCommission)
class PayoutCommissionAdmin(admin.ModelAdmin):
    list_display = [
        'paiement', 'afficher_beneficiaire', 'telephone',
        'afficher_montant_payout', 'taux_applique',
        'afficher_statut_payout', 'date_creation',
    ]
    list_filter = ['beneficiaire', 'statut', 'date_creation']
    search_fields = ['telephone', 'fedapay_payout_id', 'paiement__reference_transaction']
    readonly_fields = ['date_creation', 'date_traitement', 'reponse_api']
    date_hierarchy = 'date_creation'

    fieldsets = (
        (_('Paiement source'), {
            'fields': ('paiement',)
        }),
        (_('Bénéficiaire'), {
            'fields': ('beneficiaire', 'telephone', 'taux_applique', 'montant')
        }),
        (_('Statut & FedaPay'), {
            'fields': ('statut', 'fedapay_payout_id', 'reponse_api', 'message_erreur')
        }),
        (_('Horodatage'), {
            'fields': ('date_creation', 'date_traitement'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Bénéficiaire'))
    def afficher_beneficiaire(self, obj):
        colors = {'admin': '#3b82f6', 'commercial': '#f59e0b', 'prestataire': '#8b5cf6'}
        color = colors.get(obj.beneficiaire, '#6b7280')
        return format_html('<span style="color:{};font-weight:700">{}</span>',
                           color, obj.get_beneficiaire_display())

    @admin.display(description=_('Montant'))
    def afficher_montant_payout(self, obj):
        return montant_fcfa(obj.montant)

    @admin.display(description=_('Statut'))
    def afficher_statut_payout(self, obj):
        return badge(obj.statut, obj.get_statut_display())


# ═══════════════════════════════════════════════════════════════
# PAIEMENTS CORRECTION UNITAIRE
# ═══════════════════════════════════════════════════════════════

@admin.register(PaiementCorrectionUnitaire)
class PaiementCorrectionUnitaireAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'eleve', 'session',
        'afficher_montant_cor', 'afficher_statut_cor', 'date_creation',
    ]
    list_filter = ['statut', 'date_creation']
    search_fields = ['reference', 'eleve__email', 'fedapay_transaction_id']
    readonly_fields = ['reference', 'date_creation', 'date_paiement']
    date_hierarchy = 'date_creation'

    fieldsets = (
        (_('Référence'), {
            'fields': ('reference', 'eleve', 'session', 'statut')
        }),
        (_('Montant'), {
            'fields': ('montant',)
        }),
        (_('FedaPay'), {
            'fields': ('fedapay_transaction_id', 'fedapay_url_paiement', 'fedapay_webhook_data'),
            'classes': ('collapse',)
        }),
        (_('Horodatage'), {
            'fields': ('date_creation', 'date_paiement'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Montant'))
    def afficher_montant_cor(self, obj):
        return montant_fcfa(obj.montant)

    @admin.display(description=_('Statut'))
    def afficher_statut_cor(self, obj):
        return badge(obj.statut, obj.get_statut_display())


# ═══════════════════════════════════════════════════════════════
# TARIFS PAR TYPE DE CANDIDAT
# ═══════════════════════════════════════════════════════════════

@admin.register(ConfigTarifCandidature)
class ConfigTarifCandidatureAdmin(admin.ModelAdmin):
    list_display = [
        'afficher_type', 'etablissement',
        'afficher_mensuel', 'afficher_trimestriel', 'afficher_annuel',
        'afficher_correction_unit', 'paiement_echelonne_autorise', 'is_actif',
    ]
    list_filter = ['type_candidat', 'paiement_echelonne_autorise', 'is_actif']
    search_fields = ['etablissement__nom']

    fieldsets = (
        (_('Configuration'), {
            'fields': ('etablissement', 'type_candidat', 'is_actif')
        }),
        (_('Tarifs abonnement (XOF)'), {
            'fields': ('tarif_mensuel', 'tarif_trimestriel', 'tarif_annuel')
        }),
        (_('Tarifs à l\'unité (XOF)'), {
            'fields': ('tarif_correction_unitaire', 'tarif_qcm_unitaire')
        }),
        (_('Paiement échelonné'), {
            'fields': ('paiement_echelonne_autorise', 'nombre_tranches_max')
        }),
    )

    @admin.display(description=_('Type candidat'))
    def afficher_type(self, obj):
        color = '#3b82f6' if obj.type_candidat == 'academie' else '#f59e0b'
        return format_html('<span style="color:{};font-weight:700">{}</span>',
                           color, obj.get_type_candidat_display())

    @admin.display(description=_('Mensuel'))
    def afficher_mensuel(self, obj):
        return montant_fcfa(obj.tarif_mensuel)

    @admin.display(description=_('Trimestriel'))
    def afficher_trimestriel(self, obj):
        return montant_fcfa(obj.tarif_trimestriel)

    @admin.display(description=_('Annuel'))
    def afficher_annuel(self, obj):
        return montant_fcfa(obj.tarif_annuel)

    @admin.display(description=_('Correction / unité'))
    def afficher_correction_unit(self, obj):
        return montant_fcfa(obj.tarif_correction_unitaire)


# ═══════════════════════════════════════════════════════════════
# PLANS D'ÉCHELONNEMENT & TRANCHES
# ═══════════════════════════════════════════════════════════════

class TranchePaiementInline(admin.TabularInline):
    model = TranchePaiement
    extra = 0
    fields = ['numero', 'montant', 'date_echeance', 'statut', 'date_paiement', 'fedapay_transaction_id']
    readonly_fields = ['numero']


@admin.register(PlanEchelonnement)
class PlanEchelonnementAdmin(admin.ModelAdmin):
    list_display = [
        'abonnement', 'nombre_tranches',
        'afficher_montant_total_ech', 'afficher_par_tranche',
        'afficher_statut_ech', 'afficher_progression', 'date_creation',
    ]
    list_filter = ['statut', 'nombre_tranches']
    search_fields = ['abonnement__eleve__email', 'abonnement__numero_abonnement']
    readonly_fields = ['date_creation']
    inlines = [TranchePaiementInline]

    fieldsets = (
        (_('Abonnement'), {
            'fields': ('abonnement',)
        }),
        (_('Plan'), {
            'fields': ('nombre_tranches', 'montant_total', 'montant_par_tranche', 'statut')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Total'))
    def afficher_montant_total_ech(self, obj):
        return montant_fcfa(obj.montant_total)

    @admin.display(description=_('/ Tranche'))
    def afficher_par_tranche(self, obj):
        return montant_fcfa(obj.montant_par_tranche)

    @admin.display(description=_('Statut'))
    def afficher_statut_ech(self, obj):
        return badge(obj.statut, obj.get_statut_display())

    @admin.display(description=_('Progression'))
    def afficher_progression(self, obj):
        payees = obj.tranches_payees
        total = obj.nombre_tranches
        pct = int(payees / total * 100) if total else 0
        color = '#16a34a' if pct == 100 else '#3b82f6'
        return format_html(
            '<span style="color:{};font-weight:600">{}/{} ({} %)</span>',
            color, payees, total, pct
        )


@admin.register(TranchePaiement)
class TranchePaiementAdmin(admin.ModelAdmin):
    list_display = [
        'plan', 'numero', 'afficher_montant_tranche',
        'date_echeance', 'afficher_statut_tranche', 'date_paiement',
    ]
    list_filter = ['statut', 'date_echeance']
    search_fields = ['plan__abonnement__eleve__email', 'fedapay_transaction_id']
    readonly_fields = ['date_paiement']

    @admin.display(description=_('Montant'))
    def afficher_montant_tranche(self, obj):
        return montant_fcfa(obj.montant)

    @admin.display(description=_('Statut'))
    def afficher_statut_tranche(self, obj):
        s = obj.statut
        if obj.est_en_retard:
            s = 'en_retard'
        return badge(s, obj.get_statut_display())


# ═══════════════════════════════════════════════════════════════
# DOCUMENTS & DOSSIERS DE CANDIDATURE
# ═══════════════════════════════════════════════════════════════

@admin.register(DocumentRequis)
class DocumentRequisAdmin(admin.ModelAdmin):
    list_display = [
        'nom', 'type_candidat', 'est_obligatoire',
        'formats_acceptes', 'taille_max_mo', 'ordre', 'is_actif',
    ]
    list_filter = ['type_candidat', 'est_obligatoire', 'is_actif']
    search_fields = ['nom', 'description']
    list_editable = ['ordre', 'is_actif']

    fieldsets = (
        (_('Document'), {
            'fields': ('etablissement', 'nom', 'type_candidat', 'description')
        }),
        (_('Contraintes'), {
            'fields': ('est_obligatoire', 'formats_acceptes', 'taille_max_mo')
        }),
        (_('Affichage'), {
            'fields': ('ordre', 'is_actif')
        }),
    )


class SoumissionDocumentInline(admin.TabularInline):
    model = SoumissionDocument
    extra = 0
    fields = ['document_requis', 'fichier', 'statut', 'valide_par', 'date_soumission']
    readonly_fields = ['date_soumission']


@admin.register(DossierCandidature)
class DossierCandidatureAdmin(admin.ModelAdmin):
    list_display = [
        'eleve', 'afficher_statut_dossier', 'afficher_completude',
        'date_soumission', 'date_validation', 'valide_par',
    ]
    list_filter = ['statut']
    search_fields = ['eleve__email', 'eleve__first_name', 'eleve__last_name']
    readonly_fields = ['date_creation', 'date_modification']
    date_hierarchy = 'date_creation'
    inlines = [SoumissionDocumentInline]

    fieldsets = (
        (_('Élève'), {
            'fields': ('eleve', 'statut')
        }),
        (_('Décision'), {
            'fields': ('commentaire_admin', 'date_soumission', 'date_validation', 'valide_par')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Statut'))
    def afficher_statut_dossier(self, obj):
        return badge(obj.statut, obj.get_statut_display())

    @admin.display(description=_('Complet'), boolean=True)
    def afficher_completude(self, obj):
        return obj.est_complet


# ═══════════════════════════════════════════════════════════════
# RÉPARTITION AUTOMATIQUE — CORRECTION UNITAIRE
# ═══════════════════════════════════════════════════════════════

@admin.register(PayoutCorrectionUnitaire)
class PayoutCorrectionUnitaireAdmin(admin.ModelAdmin):
    list_display = [
        'paiement', 'afficher_beneficiaire_cor', 'telephone',
        'afficher_montant_pc', 'taux_applique',
        'afficher_statut_pc', 'date_creation',
    ]
    list_filter = ['beneficiaire', 'statut', 'date_creation']
    search_fields = ['telephone', 'fedapay_payout_id', 'paiement__reference']
    readonly_fields = ['date_creation', 'date_traitement', 'reponse_api']
    date_hierarchy = 'date_creation'

    fieldsets = (
        (_('Paiement source'), {'fields': ('paiement',)}),
        (_('Bénéficiaire'), {'fields': ('beneficiaire', 'telephone', 'taux_applique', 'montant')}),
        (_('Statut & FedaPay'), {'fields': ('statut', 'fedapay_payout_id', 'reponse_api', 'message_erreur')}),
        (_('Horodatage'), {'fields': ('date_creation', 'date_traitement'), 'classes': ('collapse',)}),
    )

    @admin.display(description=_('Bénéficiaire'))
    def afficher_beneficiaire_cor(self, obj):
        colors = {
            'dev1': '#8b5cf6', 'dev2': '#6366f1',
            'entretien': '#3b82f6', 'prof': '#16a34a',
        }
        color = colors.get(obj.beneficiaire, '#6b7280')
        return format_html('<span style="color:{};font-weight:700">{}</span>',
                           color, obj.get_beneficiaire_display())

    @admin.display(description=_('Montant'))
    def afficher_montant_pc(self, obj):
        return montant_fcfa(obj.montant)

    @admin.display(description=_('Statut'))
    def afficher_statut_pc(self, obj):
        return badge(obj.statut, obj.get_statut_display())


@admin.register(SoumissionDocument)
class SoumissionDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'document_requis', 'afficher_eleve',
        'afficher_statut_soumission', 'valide_par', 'date_soumission',
    ]
    list_filter = ['statut', 'document_requis']
    search_fields = ['dossier__eleve__email', 'nom_fichier_original']
    readonly_fields = ['date_soumission', 'date_validation']

    fieldsets = (
        (_('Dossier & Document'), {
            'fields': ('dossier', 'document_requis', 'fichier', 'nom_fichier_original')
        }),
        (_('Validation'), {
            'fields': ('statut', 'commentaire_admin', 'valide_par', 'date_validation')
        }),
        (_('Horodatage'), {
            'fields': ('date_soumission',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Élève'))
    def afficher_eleve(self, obj):
        return obj.dossier.eleve.get_full_name()

    @admin.display(description=_('Statut'))
    def afficher_statut_soumission(self, obj):
        return badge(obj.statut, obj.get_statut_display())
