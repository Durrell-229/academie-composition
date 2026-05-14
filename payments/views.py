"""
Vues de base du module paiements
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


@login_required
def paiement_list(request):
    """
    Page d'accueil paiements : redirige vers les abonnements pour les élèves,
    sinon affiche le tableau de bord paiements.
    """
    user = request.user
    if getattr(user, 'role', '') == 'eleve':
        return redirect('payments:abonnements')
    return redirect('payments:abonnements')
