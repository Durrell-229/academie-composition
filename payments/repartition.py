"""
Répartition automatique des paiements de correction unitaire.

Répartition fixe à chaque paiement :
  - Développeur 1   : 5 %  (numéro codé en dur)
  - Développeur 2   : 5 %  (numéro codé en dur)
  - Entretien       : 40 % (numéro codé en dur)
  - Professeur      : 50 % (numéro saisi par l'admin sur chaque examen)

Si le numéro du professeur n'est pas renseigné sur l'examen, sa part
(50 %) est versée sur le numéro d'entretien à la place.
"""

import logging
import requests
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Numéros hardcodés ────────────────────────────────────────────────────────
_DEV1_PHONE      = '+2290190918413'
_DEV2_PHONE      = '+2290159290652'
_ENTRETIEN_PHONE = '+2290197650817'

_TAUX = {
    'dev1':      5,
    'dev2':      5,
    'entretien': 40,
    'prof':      50,
}


def _calculer_parts(montant_total: int, telephone_prof: str) -> list[dict]:
    """
    Retourne la liste des bénéficiaires avec leur montant XOF.
    Les arrondis sont absorbés par le prof (ou l'entretien si pas de prof).
    """
    dev1_m      = int(montant_total * _TAUX['dev1']      / 100)
    dev2_m      = int(montant_total * _TAUX['dev2']      / 100)
    entretien_m = int(montant_total * _TAUX['entretien'] / 100)
    prof_m      = montant_total - dev1_m - dev2_m - entretien_m  # absorbe les arrondis

    parts = [
        {'code': 'dev1',      'telephone': _DEV1_PHONE,      'montant': dev1_m,      'taux': _TAUX['dev1']},
        {'code': 'dev2',      'telephone': _DEV2_PHONE,      'montant': dev2_m,      'taux': _TAUX['dev2']},
        {'code': 'entretien', 'telephone': _ENTRETIEN_PHONE, 'montant': entretien_m, 'taux': _TAUX['entretien']},
    ]

    if telephone_prof and telephone_prof.strip():
        parts.append({'code': 'prof', 'telephone': telephone_prof.strip(), 'montant': prof_m, 'taux': _TAUX['prof']})
    else:
        # Pas de numéro prof → entretien récupère aussi la part prof
        parts[2]['montant'] += prof_m
        parts[2]['taux'] += _TAUX['prof']
        logger.warning("Aucun téléphone prof sur cet examen — part prof versée sur entretien.")

    return parts


def _envoyer_payout_fedapay(config, telephone: str, montant: int, description: str) -> dict:
    """
    Envoie un payout FedaPay (transfert Mobile Money sortant).
    Retourne {'success': bool, 'payout_id': str|None, 'raw': dict|None, 'error': str|None}
    """
    base_url = (
        "https://api.fedapay.com/v1"
        if config.environnement == 'production'
        else "https://sandbox-api.fedapay.com/v1"
    )
    headers = {
        'Authorization': f'Bearer {config.cle_api_secrete}',
        'Content-Type': 'application/json',
    }
    # Nettoyer le numéro : garder uniquement les chiffres après le code pays
    clean_phone = telephone.replace(' ', '').replace('-', '')
    # Supprimer le + et le code pays 229 → garder les 8 derniers chiffres
    if clean_phone.startswith('+229'):
        local = clean_phone[4:]
    elif clean_phone.startswith('229'):
        local = clean_phone[3:]
    else:
        local = clean_phone

    payload = {
        'sender': {
            'lastname': 'Academie',
            'firstname': 'Numerique',
            'email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@academie.com').split('<')[-1].rstrip('>'),
        },
        'beneficiary': {
            'lastname': 'Beneficiaire',
            'firstname': description[:30],
            'phone_number': {
                'number': local,
                'country': 'BJ',
            },
        },
        'amount': montant,
        'currency': {'iso': 'XOF'},
        'mode': 'mtn',
        'include': ['customer'],
    }

    try:
        resp = requests.post(f'{base_url}/payouts', headers=headers, json=payload, timeout=15)
        raw = resp.json() if resp.content else {}
        if resp.status_code in (200, 201):
            payout_id = str(raw.get('id', ''))
            # Envoyer le payout
            if payout_id:
                requests.put(
                    f'{base_url}/payouts/{payout_id}/send_now',
                    headers=headers, timeout=10
                )
            return {'success': True, 'payout_id': payout_id, 'raw': raw, 'error': None}
        else:
            return {'success': False, 'payout_id': None, 'raw': raw, 'error': resp.text}
    except Exception as exc:
        return {'success': False, 'payout_id': None, 'raw': None, 'error': str(exc)}


def repartir_correction(paiement_correction) -> bool:
    """
    Point d'entrée principal. Appelé juste après que le paiement correction
    est marqué SUCCES (dans le webhook FedaPay).

    Crée les lignes PayoutCorrectionUnitaire et tente les virements FedaPay.
    Retourne True si tous les payouts ont été initiés sans erreur fatale.
    """
    from .models import PayoutCorrectionUnitaire, ConfigurationFedaPay

    session = paiement_correction.session
    exam = session.exam
    montant_total = int(paiement_correction.montant)
    telephone_prof = getattr(exam, 'telephone_prof_beneficiaire', '') or ''

    # Config FedaPay active (nécessaire pour les payouts)
    config = ConfigurationFedaPay.objects.filter(is_actif=True).first()

    parts = _calculer_parts(montant_total, telephone_prof)
    tout_ok = True

    for part in parts:
        if part['montant'] <= 0:
            continue

        payout_obj = PayoutCorrectionUnitaire.objects.create(
            paiement=paiement_correction,
            beneficiaire=part['code'],
            telephone=part['telephone'],
            montant=part['montant'],
            taux_applique=part['taux'],
            statut=PayoutCorrectionUnitaire.Statut.EN_ATTENTE,
        )

        if config:
            result = _envoyer_payout_fedapay(
                config,
                telephone=part['telephone'],
                montant=part['montant'],
                description=f"Correction {exam.titre[:20]} — {part['code']}",
            )
            if result['success']:
                payout_obj.statut = PayoutCorrectionUnitaire.Statut.ENVOYE
                payout_obj.fedapay_payout_id = result['payout_id'] or ''
                payout_obj.reponse_api = result['raw']
                payout_obj.date_traitement = timezone.now()
                logger.info(
                    f"Payout {part['code']} {part['montant']} FCFA → {part['telephone']} : OK (id={result['payout_id']})"
                )
            else:
                payout_obj.statut = PayoutCorrectionUnitaire.Statut.ECHEC
                payout_obj.message_erreur = result['error'] or ''
                payout_obj.reponse_api = result['raw']
                tout_ok = False
                logger.error(
                    f"Payout {part['code']} ÉCHEC → {part['telephone']} : {result['error']}"
                )
            payout_obj.save(update_fields=[
                'statut', 'fedapay_payout_id', 'reponse_api',
                'message_erreur', 'date_traitement'
            ])
        else:
            logger.warning(
                f"FedaPay non configuré — payout {part['code']} {part['montant']} FCFA en attente (pas de config active)."
            )

    return tout_ok
