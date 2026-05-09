from django.contrib import admin
from .models import (
    FraisScolaire, Paiement, EcheancierPaiement, TransactionPaiement, 
    BourseScolaire, RapportFinancier,
    PlanAbonnementScolaire, AbonnementEleve, PaiementAbonnement,
    ConfigurationFedaPay, PromotionAbonnement
)

# ═══════════════════════════════════════════════════════════════
# MODÈLES DE BASE
# ═══════════════════════════════════════════════════════════════

@admin.register(FraisScolaire)
class FraisScolaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_frais', 'montant', 'est_obligatoire', 'is_actif']
    list_filter = ['type_frais', 'est_obligatoire', 'is_actif']
    search_fields = ['nom', 'code']

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['numero_paiement', 'eleve', 'frais', 'montant_total', 'montant_paye', 'statut', 'date_paiement']
    list_filter = ['statut', 'mode_paiement', 'date_paiement']
    search_fields = ['numero_paiement', 'eleve__last_name']

@admin.register(TransactionPaiement)
class TransactionPaiementAdmin(admin.ModelAdmin):
    list_display = ['paiement', 'type_transaction', 'montant', 'mode_paiement', 'est_reussi', 'date_transaction']
    list_filter = ['type_transaction', 'mode_paiement', 'est_reussi']


# ═══════════════════════════════════════════════════════════════
# SYSTÈME D'ABONNEMENT
# ═══════════════════════════════════════════════════════════════

@admin.register(ConfigurationFedaPay)
class ConfigurationFedaPayAdmin(admin.ModelAdmin):
    list_display = ['etablissement', 'nom_marchand', 'environnement', 'is_actif', 'date_creation']
    list_filter = ['environnement', 'is_actif']
    search_fields = ['etablissement__nom', 'nom_marchand']
    fieldsets = (
        ('Configuration API', {
            'fields': ('etablissement', 'environnement', 'cle_api_publique', 'cle_api_secrete')
        }),
        ('Informations Marchand', {
            'fields': ('nom_marchand', 'email_marchand', 'logo_url')
        }),
        ('Webhook', {
            'fields': ('webhook_secret', 'webhook_url'),
            'classes': ('collapse',)
        }),
        ('Paramètres', {
            'fields': ('devise', 'langue_par_defaut', 'is_actif')
        }),
    )


@admin.register(PlanAbonnementScolaire)
class PlanAbonnementScolaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'niveau', 'etablissement', 'prix_mensuel', 'is_populaire', 'is_recommande', 'is_actif']
    list_filter = ['niveau', 'type_plan', 'is_populaire', 'is_actif', 'etablissement']
    search_fields = ['nom', 'slug', 'description_courte']
    prepopulated_fields = {'slug': ('nom',)}
    fieldsets = (
        ('Informations de base', {
            'fields': ('etablissement', 'nom', 'slug', 'niveau', 'type_plan', 'icone')
        }),
        ('Tarification', {
            'fields': ('prix_mensuel', 'prix_annuel', 'reduction_annuelle_pourcentage', 'duree_jours')
        }),
        ('Description', {
            'fields': ('description_courte', 'description_complete', 'features', 'limitations')
        }),
        ('Mise en avant', {
            'fields': ('is_populaire', 'is_recommande', 'badge_special', 'couleur', 'ordre_affichage')
        }),
        ('Statut', {
            'fields': ('is_actif', 'visible_sur_site', 'image_banniere')
        }),
    )


@admin.register(AbonnementEleve)
class AbonnementEleveAdmin(admin.ModelAdmin):
    list_display = ['numero_abonnement', 'eleve', 'plan', 'statut', 'jours_restants', 'is_renouvellement_auto']
    list_filter = ['statut', 'plan__niveau', 'is_renouvellement_auto']
    search_fields = ['numero_abonnement', 'eleve__first_name', 'eleve__last_name', 'eleve__email']
    readonly_fields = ['numero_abonnement', 'date_souscription']
    fieldsets = (
        ('Informations', {
            'fields': ('numero_abonnement', 'eleve', 'plan', 'etablissement', 'statut')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin', 'date_prochain_paiement')
        }),
        ('Paiement', {
            'fields': ('dernier_paiement', 'montant_paye_total', 'nombre_paiements', 'is_renouvellement_auto')
        }),
        ('FedaPay', {
            'fields': ('fedapay_customer_id', 'fedapay_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('rappel_7j_envoye', 'rappel_3j_envoye', 'rappel_1j_envoye'),
            'classes': ('collapse',)
        }),
        ('Historique', {
            'fields': ('date_souscription', 'date_resiliation', 'motif_resiliation'),
            'classes': ('collapse',)
        }),
    )
    
    def jours_restants(self, obj):
        return obj.jours_restants
    jours_restants.short_description = 'Jours restants'


@admin.register(PaiementAbonnement)
class PaiementAbonnementAdmin(admin.ModelAdmin):
    list_display = ['reference_transaction', 'eleve', 'montant', 'mode_paiement', 'statut', 'date_creation']
    list_filter = ['statut', 'mode_paiement', 'date_creation']
    search_fields = ['reference_transaction', 'eleve__email', 'fedapay_transaction_id']
    readonly_fields = ['date_creation']
    fieldsets = (
        ('Informations', {
            'fields': ('reference_transaction', 'abonnement', 'eleve', 'statut')
        }),
        ('Montant', {
            'fields': ('montant', 'frais_transaction', 'montant_total')
        }),
        ('Paiement', {
            'fields': ('mode_paiement', 'telephone_paiement', 'operateur')
        }),
        ('FedaPay', {
            'fields': ('fedapay_transaction_id', 'fedapay_url_paiement'),
            'classes': ('collapse',)
        }),
        ('Reçu', {
            'fields': ('recu_pdf',),
        }),
        ('Tentatives', {
            'fields': ('nombre_tentatives', 'derniere_erreur'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PromotionAbonnement)
class PromotionAbonnementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code_promo', 'type_reduction', 'valeur_reduction', 'est_valide', 'nombre_utilisations', 'is_actif']
    list_filter = ['type_reduction', 'is_actif', 'date_debut']
    search_fields = ['nom', 'code_promo']
    filter_horizontal = ['plans_applicables']
    fieldsets = (
        ('Informations', {
            'fields': ('etablissement', 'nom', 'code_promo', 'description')
        }),
        ('Réduction', {
            'fields': ('type_reduction', 'valeur_reduction')
        }),
        ('Limites', {
            'fields': ('date_debut', 'date_fin', 'nombre_utilisations_max', 'nombre_utilisations')
        }),
        ('Applicabilité', {
            'fields': ('plans_applicables',)
        }),
        ('Visuel', {
            'fields': ('banniere', 'couleur_badge')
        }),
        ('Statut', {
            'fields': ('is_actif',)
        }),
    )
    
    def est_valide(self, obj):
        return obj.est_valide
    est_valide.boolean = True
    est_valide.short_description = 'Valide'
