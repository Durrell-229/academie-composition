"""
Utilitaires transversaux pour le module payments.

Règle fondamentale :
  - Si aucune ConfigurationFedaPay n'est présente pour l'établissement,
    ou si la configuration est inactive, TOUT le contenu est gratuit.
  - Si une configuration active existe, les paiements sont requis.
"""

import logging

logger = logging.getLogger(__name__)


def paiements_actifs(etablissement) -> bool:
    """
    Retourne True si le système de paiement est configuré et actif.
    Retourne False → mode gratuit, tout le contenu est accessible sans paiement.

    Utilisation typique :
        if not paiements_actifs(user.etablissement):
            # accès libre
    """
    if etablissement is None:
        return False
    try:
        config = etablissement.config_fedapay
        return bool(config and config.is_actif)
    except Exception:
        return False


def calculer_commissions(montant: int, config_commission) -> dict:
    """
    Calcule les parts admin / commercial / prestataire à partir du montant total.

    Args:
        montant: montant total en entier XOF
        config_commission: instance ConfigurationCommission

    Returns:
        dict {'admin': int, 'commercial': int, 'prestataire': int, 'total': int}
    """
    if config_commission is None:
        return {'admin': 0, 'commercial': 0, 'prestataire': montant, 'total': montant}

    parts = config_commission.calculer_parts(montant)
    parts['total'] = montant
    return parts


def get_config_commission(etablissement):
    """
    Retourne la ConfigurationCommission active d'un établissement, ou None.
    """
    if etablissement is None:
        return None
    try:
        from payments.models import ConfigurationCommission
        return ConfigurationCommission.objects.get(etablissement=etablissement, is_actif=True)
    except Exception:
        return None
