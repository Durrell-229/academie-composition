"""
URLs pour le module payments
"""

from django.urls import path, include
from . import views

app_name = 'payments'

urlpatterns = [
    # Page d'accueil paiements (redirige vers abonnements)
    path('dashboard/', views.paiement_list, name='paiement_list'),

    # URLs d'abonnement FedaPay (abonnements/, souscrire/, webhook/, etc.)
    path('', include('payments.urls_abonnement')),
]

# Note: Les URLs d'abonnement incluent:
# - /abonnements/ - Page des plans
# - /souscrire/ - Page de souscription
# - /api/initier-paiement/ - API paiement
# - /webhook/fedapay/ - Webhook FedaPay
# - /mes-abonnements/ - Gestion abonnements
# - /admin/config-fedapay/ - Configuration admin
