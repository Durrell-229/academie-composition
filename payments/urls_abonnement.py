"""
URLs pour le système d'abonnement FedaPay
"""

from django.urls import path
from . import views_abonnement

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

    # Frais scolaires (CRUD admin)
    path('admin/frais-scolaires/', views_abonnement.admin_frais_list, name='admin_frais_list'),
    path('admin/frais-scolaires/create/', views_abonnement.admin_frais_create, name='admin_frais_create'),
    path('admin/frais-scolaires/<uuid:frais_id>/edit/', views_abonnement.admin_frais_edit, name='admin_frais_edit'),
    path('admin/frais-scolaires/<uuid:frais_id>/delete/', views_abonnement.admin_frais_delete, name='admin_frais_delete'),
]

# Note: Inclure ces URLs dans payments/urls.py principal avec:
# path('', include('payments.urls_abonnement'))
