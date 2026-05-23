"""
Vues de base du module paiements
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


@login_required
def paiement_list(request):
    return redirect('payments:abonnements')
