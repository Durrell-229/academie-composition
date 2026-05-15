"""
Vues pour la gestion des commissions et payouts automatiques FedaPay.
Accessible uniquement aux admins/superadmins.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import (
    ConfigurationCommission, PayoutCommission,
    PaiementAbonnement,
)
from .fedapay_service import FedaPayService

logger = logging.getLogger(__name__)


def _admin_requis(request):
    """Retourne True si l'utilisateur est admin ou superadmin."""
    role = getattr(request.user, 'role', '')
    return request.user.is_superuser or role in ('admin', 'directeur')


@login_required
def commission_dashboard(request):
    """Tableau de bord des commissions et payouts."""
    if not _admin_requis(request):
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('payments:abonnements')

    # Statistiques globales
    stats = PayoutCommission.objects.aggregate(
        total_envoye=Sum('montant', filter=Q(statut__in=['envoye', 'succes'])),
        total_echec=Count('id', filter=Q(statut='echec')),
        total_attente=Count('id', filter=Q(statut='en_attente')),
    )

    par_beneficiaire = []
    for role in ['admin', 'commercial', 'prestataire']:
        agg = PayoutCommission.objects.filter(beneficiaire=role).aggregate(
            total=Sum('montant', filter=Q(statut__in=['envoye', 'succes'])),
            nb=Count('id'),
        )
        par_beneficiaire.append({
            'role': role,
            'label': role.capitalize(),
            'total': agg['total'] or 0,
            'nb': agg['nb'],
        })

    # 20 derniers payouts
    derniers_payouts = PayoutCommission.objects.select_related(
        'paiement', 'paiement__eleve'
    ).order_by('-date_creation')[:20]

    # Paiements en attente de distribution
    paiements_sans_payouts = PaiementAbonnement.objects.filter(
        statut=PaiementAbonnement.StatutPaiement.SUCCES,
        payouts__isnull=True
    ).select_related('eleve', 'abonnement__plan')[:10]

    # Config commission active
    try:
        etablissement = request.user.etablissement
        config = ConfigurationCommission.objects.get(etablissement=etablissement)
    except Exception:
        config = None

    context = {
        'stats': stats,
        'par_beneficiaire': par_beneficiaire,
        'derniers_payouts': derniers_payouts,
        'paiements_sans_payouts': paiements_sans_payouts,
        'config': config,
    }
    return render(request, 'payments/commissions/dashboard.html', context)


@login_required
def config_commission(request):
    """Formulaire de configuration des taux et numéros de téléphone."""
    if not _admin_requis(request):
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('payments:abonnements')

    try:
        etablissement = request.user.etablissement
    except AttributeError:
        messages.error(request, "Aucun établissement associé à votre compte.")
        return redirect('payments:commission_dashboard')

    config, _ = ConfigurationCommission.objects.get_or_create(
        etablissement=etablissement,
        defaults={
            'taux_admin': 10,
            'taux_commercial': 20,
            'taux_prestataire': 70,
            'telephone_admin': '',
            'telephone_commercial': '',
            'telephone_prestataire': '',
        }
    )

    if request.method == 'POST':
        taux_admin = float(request.POST.get('taux_admin', 10))
        taux_commercial = float(request.POST.get('taux_commercial', 20))
        taux_prestataire = float(request.POST.get('taux_prestataire', 70))

        if abs(taux_admin + taux_commercial + taux_prestataire - 100) > 0.01:
            messages.error(request, "La somme des taux doit être égale à 100 %.")
            return render(request, 'payments/commissions/config.html', {'config': config})

        config.taux_admin = taux_admin
        config.taux_commercial = taux_commercial
        config.taux_prestataire = taux_prestataire
        config.telephone_admin = request.POST.get('telephone_admin', '').strip()
        config.telephone_commercial = request.POST.get('telephone_commercial', '').strip()
        config.telephone_prestataire = request.POST.get('telephone_prestataire', '').strip()
        config.save()

        messages.success(request, "Configuration enregistrée.")
        return redirect('payments:commission_dashboard')

    return render(request, 'payments/commissions/config.html', {'config': config})


@login_required
@require_POST
def relancer_payout(request, payout_id):
    """Relancer manuellement un payout en échec."""
    if not _admin_requis(request):
        return JsonResponse({'success': False, 'error': 'Accès refusé'}, status=403)

    payout = get_object_or_404(PayoutCommission, id=payout_id, statut=PayoutCommission.Statut.ECHEC)
    paiement = payout.paiement
    etablissement = paiement.abonnement.plan.etablissement

    service = FedaPayService(etablissement)
    payout.statut = PayoutCommission.Statut.EN_ATTENTE
    payout.message_erreur = ''
    payout.save()

    result = service._envoyer_payout_unique(payout.telephone, int(payout.montant), payout)
    return JsonResponse(result)


@login_required
@require_POST
def distribuer_commissions_manuellement(request, paiement_id):
    """Déclencher manuellement la distribution pour un paiement confirmé sans payouts."""
    if not _admin_requis(request):
        return JsonResponse({'success': False, 'error': 'Accès refusé'}, status=403)

    paiement = get_object_or_404(
        PaiementAbonnement, id=paiement_id, statut=PaiementAbonnement.StatutPaiement.SUCCES
    )
    if paiement.payouts.exists():
        return JsonResponse({'success': False, 'error': 'Payouts déjà effectués pour ce paiement'}, status=400)

    etablissement = paiement.abonnement.plan.etablissement
    service = FedaPayService(etablissement)
    result = service.envoyer_payouts(paiement)
    return JsonResponse(result)
