"""
URLs pour le système d'abonnement FedaPay
"""

from django.urls import path
from . import views_abonnement, views_candidature

urlpatterns = [
    # Pages publiques
    path('abonnements/', views_abonnement.page_abonnements, name='abonnements'),
    
    # Processus de souscription
    path('souscrire/', views_abonnement.souscrire_abonnement, name='souscrire'),
    
    # Checkout FedaPay Embed (Checkout.js)
    path('checkout-fedapay/', views_abonnement.checkout_fedapay_embed, name='checkout_fedapay'),
    
    # API paiement
    path('api/initier-paiement/', views_abonnement.initier_paiement_fedapay, name='initier_paiement'),
    path('api/verifier-paiement/<str:paiement_id>/', views_abonnement.verifier_statut_paiement, name='verifier_paiement'),
    path('api/confirmer-paiement/', views_abonnement.confirmer_paiement_fedapay, name='confirmer_paiement'),
    
    # Webhook FedaPay
    path('webhook/fedapay/', views_abonnement.fedapay_webhook, name='fedapay_webhook'),
    
    # Callbacks
    path('paiement/succes/', views_abonnement.paiement_succes, name='paiement_succes'),
    path('paiement/echec/', views_abonnement.paiement_echec, name='paiement_echec'),
    
    # Gestion abonnements utilisateur
    path('mes-abonnements/', views_abonnement.mes_abonnements, name='mes_abonnements'),
    path('renouveler/<str:abonnement_id>/', views_abonnement.renouveler_abonnement, name='renouveler'),
    path('annuler/<str:abonnement_id>/', views_abonnement.annuler_abonnement, name='annuler'),
    
    # Admin - Configuration
    path('admin/config-fedapay/', views_abonnement.admin_config_fedapay, name='admin_config_fedapay'),
    path('admin/config-fedapay/save/', views_abonnement.admin_save_config_fedapay, name='admin_save_config_fedapay'),
    path('admin/plans-abonnement/', views_abonnement.admin_plans_abonnement, name='admin_plans_abonnement'),
    path('admin/plans-abonnement/create/', views_abonnement.admin_create_plan, name='admin_create_plan'),
    path('admin/plans-abonnement/<uuid:plan_id>/edit/', views_abonnement.admin_edit_plan, name='admin_edit_plan'),
    path('admin/plans-abonnement/<uuid:plan_id>/delete/', views_abonnement.admin_delete_plan, name='admin_delete_plan'),

    # Paywall — correction unitaire
    path('correction/initier/<uuid:session_id>/', views_abonnement.initier_paiement_correction, name='initier_paiement_correction'),
    path('correction/callback/<uuid:paiement_correction_id>/', views_abonnement.correction_paiement_callback, name='correction_paiement_callback'),

    # Frais scolaires (CRUD admin)
    path('admin/frais-scolaires/', views_abonnement.admin_frais_list, name='admin_frais_list'),
    path('admin/frais-scolaires/create/', views_abonnement.admin_frais_create, name='admin_frais_create'),
    path('admin/frais-scolaires/<uuid:frais_id>/edit/', views_abonnement.admin_frais_edit, name='admin_frais_edit'),
    path('admin/frais-scolaires/<uuid:frais_id>/delete/', views_abonnement.admin_frais_delete, name='admin_frais_delete'),

    # ─── ESPACE PAIEMENT & ÉCHELONNEMENT ───────────────────────────
    path('espace-paiement/', views_candidature.espace_paiement, name='espace_paiement'),
    path('souscrire-echelonne/', views_candidature.initier_souscription_echelonnee, name='souscrire_echelonne'),
    path('tranche/<uuid:tranche_id>/payer/', views_candidature.payer_tranche, name='payer_tranche'),
    path('tranche/<uuid:tranche_id>/verifier/', views_candidature.verifier_paiement_tranche, name='verifier_tranche'),

    # ─── DOSSIER DE CANDIDATURE ────────────────────────────────────
    path('mon-dossier/', views_candidature.mon_dossier, name='mon_dossier'),
    path('mon-dossier/soumettre/<uuid:document_id>/', views_candidature.soumettre_document, name='soumettre_document'),

    # ─── ADMIN : CONFIGURATION ─────────────────────────────────────
    path('admin/tarifs-candidature/', views_candidature.admin_config_tarifs, name='admin_config_tarifs'),
    path('admin/documents-requis/', views_candidature.admin_documents_requis, name='admin_documents_requis'),
    path('admin/dossiers/', views_candidature.admin_dossiers_candidature, name='admin_dossiers_candidature'),
    path('admin/dossiers/<uuid:dossier_id>/', views_candidature.admin_detail_dossier, name='admin_detail_dossier'),

    # ─── GESTION PAIEMENTS UNIFIÉE ─────────────────────────────────
    path('admin/gestion/', views_abonnement.admin_gestion_paiements, name='admin_gestion_paiements'),
    path('admin/gestion/abonnement/<uuid:abonnement_id>/toggle/', views_abonnement.admin_toggle_abonnement, name='admin_toggle_abonnement'),
    path('admin/gestion/payout-correction/<uuid:payout_id>/retry/', views_abonnement.admin_retry_payout_correction, name='admin_retry_payout_correction'),
]

# Note: Inclure ces URLs dans payments/urls.py principal avec:
# path('', include('payments.urls_abonnement'))
