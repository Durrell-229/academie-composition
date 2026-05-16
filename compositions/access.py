"""
Vérification d'accès aux corrections — source de vérité unique.

Règles (ordre de priorité) :
  1. UserSubscription PRO/ELITE active  → accès total
  2. AbonnementEleve actif (non expiré) → accès total
  3. PaiementCorrectionUnitaire 'succes' pour cette session → accès à cette correction
  4. Sinon                               → paywall

Appelé depuis :
  - compositions/tasks.py  (après correction IA)
  - compositions/views.py  (result_view + bulletin_composition_pdf)
  - payments webhook        (après paiement confirmé)
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

ACCES_LIBRE = 'libre'           # compte sans restriction (admin/prof)
ACCES_SUBSCRIPTION = 'subscription_pro'
ACCES_ABONNEMENT = 'abonnement_actif'
ACCES_CORRECTION = 'paiement_correction'
ACCES_REFUSE = None


def verifier_acces_correction(eleve, session) -> tuple[bool, str | None]:
    """
    Retourne (True, raison) si l'élève a le droit de voir la correction complète,
    (False, None) sinon.
    Ne lève jamais d'exception — toute erreur → refus.
    """
    try:
        # ── Comptes non-élèves : accès libre (profs, admins, directeurs) ──
        role = getattr(eleve, 'role', 'eleve')
        if role not in ('eleve', ''):
            return True, ACCES_LIBRE

        # ── 1. subscriptions.UserSubscription PRO/ELITE ──
        try:
            sub = eleve.subscription          # OneToOneField
            if (sub.is_active and not sub.is_expired
                    and sub.plan.level in ('PRO', 'ELITE')):
                logger.debug(f"Accès OK subscription {sub.plan.level} — élève {eleve.id}")
                return True, ACCES_SUBSCRIPTION
        except Exception:
            pass

        # ── 2. payments.AbonnementEleve actif ──
        try:
            from payments.models import AbonnementEleve
            if AbonnementEleve.objects.filter(
                eleve=eleve,
                statut=AbonnementEleve.StatutAbonnement.ACTIF,
                date_fin__gt=timezone.now(),
            ).exists():
                logger.debug(f"Accès OK AbonnementEleve — élève {eleve.id}")
                return True, ACCES_ABONNEMENT
        except Exception:
            pass

        # ── 3. Paiement ponctuel pour cette session ──
        try:
            from payments.models import PaiementCorrectionUnitaire
            if PaiementCorrectionUnitaire.objects.filter(
                eleve=eleve,
                session=session,
                statut=PaiementCorrectionUnitaire.Statut.SUCCES,
            ).exists():
                logger.debug(f"Accès OK PaiementCorrectionUnitaire — session {session.id}")
                return True, ACCES_CORRECTION
        except Exception:
            pass

        logger.info(f"Accès REFUSÉ — élève {eleve.id} session {session.id}")
        return False, ACCES_REFUSE

    except Exception as e:
        logger.error(f"Erreur inattendue verifier_acces_correction: {e}")
        return False, ACCES_REFUSE


def debloquer_correction(session):
    """
    Débloque la correction complète d'une session après paiement confirmé.
    Met à jour Resultat.correction_complete + statut session.
    """
    try:
        resultat = session.resultat
        resultat.correction_complete = True
        resultat.save(update_fields=['correction_complete'])

        session.statut = 'corrige'
        session.save(update_fields=['statut'])

        logger.info(f"Correction débloquée — session {session.id}")
        return True
    except Exception as e:
        logger.error(f"Erreur debloquer_correction session {session.id}: {e}")
        return False


def construire_apercu(correction_result: dict, note_sur: float = 20) -> dict:
    """
    Construit le dict aperçu (30 % des détails) à partir du résultat IA complet.
    Stocké dans Resultat.apercu_correction — jamais la correction complète.
    """
    details_all = correction_result.get('details', [])
    nb_total = len(details_all)
    nb_apercu = max(1, nb_total // 3)          # ~30 %
    details_apercu = details_all[:nb_apercu]

    return {
        'pourcentage_apercu': round(nb_apercu * 100 / nb_total) if nb_total else 30,
        'nb_details_apercu': nb_apercu,
        'nb_details_total': nb_total,
        'details': details_apercu,
        'points_forts': correction_result.get('points_forts_global', '')[:200],
        'note_sur': note_sur,
    }
