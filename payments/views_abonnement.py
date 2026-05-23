"""
Vues pour le système d'abonnement avec FedaPay
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_http_methods

from .models import (
    PlanAbonnementScolaire, AbonnementEleve, PaiementAbonnement,
    ConfigurationFedaPay, PromotionAbonnement, FraisScolaire,
    PaiementCorrectionUnitaire,
)
from core.models import Organisation as Etablissement, Classe
from .fedapay_service import FedaPayService, FedaPayCheckout


def _get_org_plateforme():
    """Retourne (ou crée) l'organisation globale unique de la plateforme."""
    org, _ = Etablissement.objects.get_or_create(
        code='PLATEFORME',
        defaults={'nom': 'Académie Numérique', 'pays': 'Bénin', 'devise': 'XOF', 'is_active': True}
    )
    return org
from .tasks import traiter_paiement_fedapay
from .utils import paiements_actifs
from core.redis_tasks import get_task_result

logger = logging.getLogger(__name__)


def page_abonnements(request):
    """
    Page d'affichage des plans d'abonnement avec slider
    """
    plans = PlanAbonnementScolaire.objects.filter(
        is_actif=True, 
        visible_sur_site=True
    ).order_by('ordre_affichage')
    
    # Vérifier si l'utilisateur a déjà un abonnement actif
    abonnement_actif = None
    if request.user.is_authenticated and request.user.role == 'eleve':
        try:
            abonnement_actif = AbonnementEleve.objects.filter(
                eleve=request.user,
                statut=AbonnementEleve.StatutAbonnement.ACTIF
            ).select_related('plan').first()
        except:
            pass
    
    # Promotions actives
    promotions = PromotionAbonnement.objects.filter(
        is_actif=True,
        date_debut__lte=timezone.now(),
        date_fin__gte=timezone.now()
    )
    
    context = {
        'plans': plans,
        'abonnement_actif': abonnement_actif,
        'promotions': promotions,
        'SITE_URL': settings.SITE_URL,
    }
    
    return render(request, 'payments/abonnements_page.html', context)


@login_required
def souscrire_abonnement(request):
    """
    Page de souscription à un plan
    """
    plan_slug = request.GET.get('plan')
    code_promo = request.GET.get('code', '')
    
    if not plan_slug:
        messages.error(request, "Veuillez sélectionner un plan.")
        return redirect('payments:abonnements')
    
    plan = get_object_or_404(PlanAbonnementScolaire, slug=plan_slug, is_actif=True)

    # Vérifier la config FedaPay via l'établissement du plan
    etablissement = plan.etablissement

    # MODE GRATUIT : si aucune configuration FedaPay n'est active,
    # activer l'abonnement directement sans paiement.
    if not paiements_actifs(etablissement):
        abonnement, created = AbonnementEleve.objects.get_or_create(
            eleve=request.user,
            plan=plan,
            defaults={
                'etablissement': _get_org_plateforme(),
                'statut': AbonnementEleve.StatutAbonnement.ACTIF,
                'date_debut': timezone.now(),
                'date_fin': timezone.now() + __import__('datetime').timedelta(days=plan.duree_jours),
            }
        )
        if not created and abonnement.statut != AbonnementEleve.StatutAbonnement.ACTIF:
            abonnement.statut = AbonnementEleve.StatutAbonnement.ACTIF
            abonnement.date_debut = timezone.now()
            abonnement.date_fin = timezone.now() + __import__('datetime').timedelta(days=plan.duree_jours)
            abonnement.save(update_fields=['statut', 'date_debut', 'date_fin'])
        messages.success(request, f"Accès gratuit activé — plan {plan.nom}. Aucun paiement requis.")
        return redirect('payments:mes_abonnements')

    config = getattr(etablissement, 'config_fedapay', None)
    if config is None:
        messages.warning(request, "Le paiement FedaPay n'est pas encore configuré pour cet établissement.")
    elif not config.is_actif:
        messages.error(request, "Le système de paiement est temporairement indisponible.")
        return redirect('payments:abonnements')
    
    # Calculer le prix avec promotion
    prix_final = plan.prix_mensuel
    promotion_appliquee = None
    
    if code_promo:
        try:
            promo = PromotionAbonnement.objects.get(
                code_promo=code_promo.upper(),
                is_actif=True,
                date_debut__lte=timezone.now(),
                date_fin__gte=timezone.now()
            )
            if promo.est_valide and (not promo.plans_applicables.exists() or plan in promo.plans_applicables.all()):
                promotion_appliquee = promo
                if promo.type_reduction == 'pourcentage':
                    prix_final = prix_final * (1 - promo.valeur_reduction / 100)
                elif promo.type_reduction == 'montant':
                    prix_final = max(0, prix_final - promo.valeur_reduction)
                # 'mois_gratuit' sera géré différemment
        except PromotionAbonnement.DoesNotExist:
            pass
    
    context = {
        'plan': plan,
        'prix_final': int(prix_final),
        'promotion': promotion_appliquee,
        'code_promo': code_promo,
        'config_fedapay': config,
        'etablissement': etablissement,
    }
    
    return render(request, 'payments/souscrire_abonnement.html', context)


@login_required
@require_http_methods(["POST"])
def initier_paiement_fedapay(request):
    """
    Initier un paiement via FedaPay
    """
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')
        type_abonnement = data.get('type', 'mensuel')  # mensuel ou annuel
        code_promo = data.get('code_promo', '')
        telephone = data.get('telephone', '')
        
        plan = get_object_or_404(PlanAbonnementScolaire, id=plan_id, is_actif=True)
        etablissement = plan.etablissement

        if not etablissement:
            return JsonResponse({'success': False, 'error': 'Établissement non trouvé'})
        
        # Calculer le montant
        if type_abonnement == 'annuel':
            montant = plan.prix_annuel_affiche
        else:
            montant = plan.prix_mensuel
        
        # Appliquer promotion
        if code_promo:
            try:
                promo = PromotionAbonnement.objects.get(
                    code_promo=code_promo.upper(),
                    is_actif=True
                )
                if promo.est_valide:
                    if promo.type_reduction == 'pourcentage':
                        montant = montant * (1 - promo.valeur_reduction / 100)
                    elif promo.type_reduction == 'montant':
                        montant = max(0, montant - promo.valeur_reduction)
                    promo.nombre_utilisations += 1
                    promo.save()
            except:
                pass
        
        # Créer l'abonnement
        abonnement = AbonnementEleve.objects.create(
            eleve=request.user,
            plan=plan,
            etablissement=etablissement,
            statut=AbonnementEleve.StatutAbonnement.EN_ATTENTE,
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(days=plan.duree_jours),
            date_prochain_paiement=timezone.now() + timedelta(days=plan.duree_jours) if plan.type_plan != 'annuel' else None
        )
        
        # Vérifier la config FedaPay avant de créer quoi que ce soit
        config = getattr(etablissement, 'config_fedapay', None)
        if not config or not config.is_actif:
            return JsonResponse({'success': False, 'error': 'Le système de paiement n\'est pas configuré pour cet établissement.'})

        # Créer le paiement
        paiement = PaiementAbonnement.objects.create(
            abonnement=abonnement,
            eleve=request.user,
            montant=int(montant),
            montant_total=int(montant),
            mode_paiement=PaiementAbonnement.ModePaiement.MOBILE_MONEY,
            statut=PaiementAbonnement.StatutPaiement.EN_ATTENTE,
            telephone_paiement=telephone,
            reference_transaction=f"ABN-{abonnement.numero_abonnement}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )

        # Appeler FedaPay SYNCHRONEMENT — on a besoin de l'URL de paiement maintenant
        fedapay = FedaPayService(etablissement)

        customer_id = abonnement.fedapay_customer_id
        if not customer_id:
            customer_id = fedapay.creer_customer(request.user)
            if customer_id:
                abonnement.fedapay_customer_id = customer_id
                abonnement.save(update_fields=['fedapay_customer_id'])

        callback_url = f"{settings.SITE_URL}/payments/paiement/succes/"
        result = fedapay.creer_transaction(paiement, customer_id, callback_url)

        if not result or not result.get('payment_url'):
            paiement.statut = PaiementAbonnement.StatutPaiement.ECHEC
            paiement.derniere_erreur = 'Impossible d\'obtenir l\'URL de paiement FedaPay'
            paiement.save(update_fields=['statut', 'derniere_erreur'])
            return JsonResponse({'success': False, 'error': 'Impossible d\'initier le paiement. Veuillez réessayer.'})

        paiement.statut = PaiementAbonnement.StatutPaiement.EN_COURS
        paiement.save(update_fields=['statut'])

        return JsonResponse({
            'success': True,
            'paiement_id': str(paiement.id),
            'payment_url': result['payment_url'],
            'transaction_id': result['transaction_id'],
        })
        
    except Exception as e:
        logger.error(f"Erreur initiation paiement: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def verifier_statut_paiement(request, paiement_id):
    """
    Vérifier le statut d'un paiement en cours
    """
    try:
        paiement = get_object_or_404(PaiementAbonnement, id=paiement_id, eleve=request.user)
        
        # Vérifier si le paiement a un task_id et vérifier son statut
        # Si la transaction FedaPay est complète
        if paiement.fedapay_transaction_id:
            service = FedaPayService(paiement.abonnement.etablissement)
            status = service.verifier_transaction(paiement.fedapay_transaction_id)
            
            if status and status['status'] == 'approved':
                return JsonResponse({
                    'success': True,
                    'status': 'completed',
                    'redirect_url': '/payments/paiement/succes/'
                })
        
        return JsonResponse({
            'success': True,
            'status': paiement.statut,
            'payment_url': paiement.fedapay_url_paiement
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def fedapay_webhook(request):
    """
    Webhook FedaPay : traite les paiements d'abonnement et de tranches.
    """
    import hmac as hmac_module
    import hashlib
    from django.db import transaction as db_transaction

    try:
        payload = request.body
        signature = request.headers.get('X-FedaPay-Signature', '')
        data = json.loads(payload)

        event_type = data.get('name', '')
        transaction_data = data.get('data', {})
        metadata = transaction_data.get('metadata', {})
        fedapay_transaction_id = str(transaction_data.get('id', ''))
        statut_fedapay = transaction_data.get('status', '')

        # ── Identifier le paiement via l'ID de transaction FedaPay ──
        from .models import PaiementAbonnement, TranchePaiement, AbonnementEleve, PlanEchelonnement

        paiement = PaiementAbonnement.objects.filter(
            fedapay_transaction_id=fedapay_transaction_id
        ).select_related('abonnement__etablissement').first()

        tranche = TranchePaiement.objects.filter(
            fedapay_transaction_id=fedapay_transaction_id
        ).select_related('plan__abonnement__etablissement').first()

        etablissement = None
        if paiement:
            etablissement = paiement.abonnement.etablissement
        elif tranche:
            etablissement = tranche.plan.abonnement.etablissement

        # ── Vérifier la signature si un secret est configuré ──
        if etablissement:
            config = getattr(etablissement, 'config_fedapay', None)
            if config and config.webhook_secret and signature:
                expected = hmac_module.new(
                    config.webhook_secret.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                if not hmac_module.compare_digest(expected, signature):
                    logger.warning(f"Signature webhook invalide pour établissement {etablissement.id}")
                    return HttpResponse(status=401)

        # ── Identifier aussi les paiements de correction unitaire ──
        from .models import PaiementCorrectionUnitaire
        paiement_correction = PaiementCorrectionUnitaire.objects.filter(
            fedapay_transaction_id=fedapay_transaction_id
        ).select_related('session__eleve', 'session__exam').first()

        if paiement_correction and not etablissement:
            config_global = ConfigurationFedaPay.objects.filter(is_actif=True).first()
            if config_global and config_global.webhook_secret and signature:
                import hmac as _hmac
                expected = _hmac.new(
                    config_global.webhook_secret.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                if not _hmac.compare_digest(expected, signature):
                    logger.warning("Signature webhook invalide pour paiement correction unitaire")
                    return HttpResponse(status=401)

        # ── Traitement si paiement approuvé ──
        if statut_fedapay == 'approved':
            with db_transaction.atomic():

                # Cas 0 : paiement de correction unitaire (paywall)
                if paiement_correction and paiement_correction.statut != PaiementCorrectionUnitaire.Statut.SUCCES:
                    paiement_correction.statut = PaiementCorrectionUnitaire.Statut.SUCCES
                    paiement_correction.fedapay_webhook_data = data
                    paiement_correction.date_paiement = timezone.now()
                    paiement_correction.save(update_fields=['statut', 'fedapay_webhook_data', 'date_paiement'])

                    from compositions.access import debloquer_correction
                    debloquer_correction(paiement_correction.session)

                    # Répartition automatique des fonds
                    try:
                        from .repartition import repartir_correction
                        repartir_correction(paiement_correction)
                    except Exception as rep_err:
                        logger.error(f"Erreur répartition correction {paiement_correction.id}: {rep_err}")

                    from notifications.utils import send_notification
                    try:
                        send_notification(
                            user=paiement_correction.eleve,
                            title="Correction débloquée !",
                            message=f"Votre correction pour '{paiement_correction.session.exam.titre}' est maintenant accessible.",
                            type='BULLETIN',
                        )
                    except Exception:
                        pass
                    logger.info(f"Correction {paiement_correction.session.id} débloquée via webhook.")

                # Cas 1 : paiement d'abonnement classique
                if paiement and paiement.statut != PaiementAbonnement.StatutPaiement.SUCCES:
                    paiement.statut = PaiementAbonnement.StatutPaiement.SUCCES
                    paiement.fedapay_webhook_data = data
                    paiement.date_paiement = timezone.now()
                    paiement.date_confirmation = timezone.now()
                    paiement.save(update_fields=['statut', 'fedapay_webhook_data', 'date_paiement', 'date_confirmation'])

                    abonnement = paiement.abonnement
                    abonnement.statut = AbonnementEleve.StatutAbonnement.ACTIF
                    abonnement.dernier_paiement = timezone.now()
                    abonnement.montant_paye_total += paiement.montant
                    abonnement.nombre_paiements += 1
                    abonnement.save(update_fields=['statut', 'dernier_paiement', 'montant_paye_total', 'nombre_paiements'])
                    logger.info(f"Abonnement {abonnement.id} activé via webhook.")

                # Cas 2 : paiement d'une tranche échelonnée
                if tranche and tranche.statut != TranchePaiement.Statut.PAYE:
                    tranche.statut = TranchePaiement.Statut.PAYE
                    tranche.date_paiement = timezone.now()
                    tranche.save(update_fields=['statut', 'date_paiement'])

                    abonnement = tranche.plan.abonnement
                    # Activer à la première tranche payée
                    if tranche.numero == 1 and abonnement.statut != AbonnementEleve.StatutAbonnement.ACTIF:
                        abonnement.statut = AbonnementEleve.StatutAbonnement.ACTIF
                    abonnement.dernier_paiement = timezone.now()
                    abonnement.montant_paye_total += tranche.montant
                    abonnement.nombre_paiements += 1
                    abonnement.save(update_fields=['statut', 'dernier_paiement', 'montant_paye_total', 'nombre_paiements'])

                    # Marquer le plan comme soldé si toutes les tranches sont payées
                    plan_ech = tranche.plan
                    if plan_ech.tranches.filter(statut=TranchePaiement.Statut.PAYE).count() == plan_ech.nombre_tranches:
                        plan_ech.statut = PlanEchelonnement.Statut.SOLDE
                        plan_ech.save(update_fields=['statut'])
                    logger.info(f"Tranche {tranche.numero} payée via webhook.")

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Erreur webhook FedaPay: {e}", exc_info=True)
        return HttpResponse(status=500)


@login_required
def paiement_succes(request):
    """
    Page de confirmation après paiement réussi
    """
    return render(request, 'payments/paiement_succes.html', {
        'message': 'Votre abonnement est maintenant actif !',
        'icon': '🎉'
    })


@login_required
def paiement_echec(request):
    """
    Page d'échec de paiement
    """
    return render(request, 'payments/paiement_echec.html', {
        'message': 'Le paiement n\'a pas pu être complété.',
        'icon': '❌'
    })


@login_required
def mes_abonnements(request):
    """
    Page de gestion des abonnements de l'élève
    """
    abonnements = AbonnementEleve.objects.filter(
        eleve=request.user
    ).select_related('plan', 'etablissement').order_by('-date_souscription')
    
    abonnement_actif = abonnements.filter(
        statut=AbonnementEleve.StatutAbonnement.ACTIF
    ).first()
    
    context = {
        'abonnements': abonnements,
        'abonnement_actif': abonnement_actif,
    }
    
    return render(request, 'payments/mes_abonnements.html', context)


@login_required
def renouveler_abonnement(request, abonnement_id):
    """
    Renouveler un abonnement expirant
    """
    abonnement = get_object_or_404(
        AbonnementEleve, 
        id=abonnement_id, 
        eleve=request.user
    )
    
    # Rediriger vers la page de souscription avec le même plan
    return redirect(f'/payments/souscrire/?plan={abonnement.plan.slug}')


@login_required
def annuler_abonnement(request, abonnement_id):
    """
    Annuler le renouvellement automatique
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        abonnement = get_object_or_404(
            AbonnementEleve,
            id=abonnement_id,
            eleve=request.user
        )
        
        abonnement.is_renouvellement_auto = False
        abonnement.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Le renouvellement automatique a été désactivé.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ═══════════════════════════════════════════════════════════════
# VUES ADMIN - Configuration
# ═══════════════════════════════════════════════════════════════

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_config_fedapay(request):
    """
    Configuration FedaPay par établissement (Super Admin)
    """
    etablissements = [_get_org_plateforme()]

    configs = []
    for etab in etablissements:
        config, created = ConfigurationFedaPay.objects.get_or_create(
            etablissement=etab,
            defaults={
                'nom_marchand': etab.nom,
                'email_marchand': 'contact@exemple.com',
                'environnement': 'sandbox',
                'cle_api_publique': '',
                'cle_api_secrete': '',
            }
        )
        configs.append({
            'etablissement': etab,
            'config': config,
            'is_new': created
        })
    
    context = {
        'configs': configs,
        'environnements': ConfigurationFedaPay.Environnement.choices,
    }
    
    return render(request, 'payments/admin_config_fedapay.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_save_config_fedapay(request):
    """
    Sauvegarder la configuration FedaPay
    """
    try:
        config_id = request.POST.get('config_id')
        config = get_object_or_404(ConfigurationFedaPay, id=config_id)
        
        config.environnement = request.POST.get('environnement', 'sandbox')
        config.cle_api_publique = request.POST.get('cle_api_publique', '')
        config.cle_api_secrete = request.POST.get('cle_api_secrete', '')
        config.nom_marchand = request.POST.get('nom_marchand', '')
        config.email_marchand = request.POST.get('email_marchand', '')
        config.logo_url = request.POST.get('logo_url', '')
        config.webhook_secret = request.POST.get('webhook_secret', '')
        config.webhook_url = request.POST.get('webhook_url', '')
        config.is_actif = request.POST.get('is_actif') == 'on'
        
        config.save()
        
        messages.success(request, 'Configuration FedaPay sauvegardée avec succès.')
        return redirect('payments:admin_config_fedapay')
        
    except Exception as e:
        messages.error(request, f'Erreur: {e}')
        return redirect('payments:admin_config_fedapay')


@staff_member_required
def admin_edit_plan(request, plan_id):
    """Modifier un plan d'abonnement existant"""
    plan = get_object_or_404(PlanAbonnementScolaire, id=plan_id)
    etablissements = [_get_org_plateforme()]

    if request.method == 'POST':
        try:
            plan.etablissement = _get_org_plateforme()
            plan.nom = request.POST.get('nom')
            plan.slug = request.POST.get('slug')
            plan.niveau = request.POST.get('niveau', 'standard')
            plan.type_plan = request.POST.get('type_plan', 'mensuel')
            plan.prix_mensuel = request.POST.get('prix_mensuel', 0)
            plan.prix_annuel = request.POST.get('prix_annuel') or None
            plan.reduction_annuelle_pourcentage = request.POST.get('reduction', 0)
            plan.description_courte = request.POST.get('description_courte', '')
            plan.description_complete = request.POST.get('description_complete', '')
            plan.duree_jours = request.POST.get('duree_jours', 30)
            plan.ordre_affichage = request.POST.get('ordre', 1)
            plan.couleur = request.POST.get('couleur', '#3b82f6')
            plan.icone = request.POST.get('icone', '🎓')
            plan.is_populaire = request.POST.get('is_populaire') == 'on'
            plan.is_recommande = request.POST.get('is_recommande') == 'on'
            plan.is_actif = request.POST.get('is_actif') == 'on'
            plan.badge_special = request.POST.get('badge_special', '')
            features_raw = request.POST.get('features_text', '')
            plan.features = [f.strip() for f in features_raw.splitlines() if f.strip()]
            plan.save()
            messages.success(request, f'Plan "{plan.nom}" mis à jour avec succès.')
            return redirect('payments:admin_plans_abonnement')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')

    context = {
        'plan': plan,
        'etablissements': etablissements,
        'niveaux': PlanAbonnementScolaire.NiveauPlan.choices,
        'types': PlanAbonnementScolaire.TypePlan.choices,
        'features_text': '\n'.join(plan.features) if plan.features else '',
    }
    return render(request, 'payments/admin_edit_plan.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_delete_plan(request, plan_id):
    """Supprimer un plan (uniquement si aucun abonnement actif)"""
    plan = get_object_or_404(PlanAbonnementScolaire, id=plan_id)
    if plan.abonnements.filter(statut=AbonnementEleve.StatutAbonnement.ACTIF).exists():
        messages.error(request, f'Impossible de supprimer "{plan.nom}" : des abonnements actifs y sont liés.')
    else:
        nom = plan.nom
        plan.delete()
        messages.success(request, f'Plan "{nom}" supprimé.')
    return redirect('payments:admin_plans_abonnement')


@staff_member_required
def admin_plans_abonnement(request):
    """
    Gestion des plans d'abonnement (Super Admin)
    """
    plans = PlanAbonnementScolaire.objects.all().select_related('etablissement')
    etablissements = [_get_org_plateforme()]
    
    context = {
        'plans': plans,
        'etablissements': etablissements,
        'niveaux': PlanAbonnementScolaire.NiveauPlan.choices,
        'types': PlanAbonnementScolaire.TypePlan.choices,
    }
    
    return render(request, 'payments/admin_plans_abonnement.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_create_plan(request):
    """
    Créer un nouveau plan d'abonnement
    """
    try:
        plan = PlanAbonnementScolaire.objects.create(
            etablissement=_get_org_plateforme(),
            nom=request.POST.get('nom'),
            slug=request.POST.get('slug'),
            niveau=request.POST.get('niveau', 'standard'),
            type_plan=request.POST.get('type_plan', 'mensuel'),
            prix_mensuel=request.POST.get('prix_mensuel', 0),
            prix_annuel=request.POST.get('prix_annuel') or None,
            reduction_annuelle_pourcentage=request.POST.get('reduction', 0),
            description_courte=request.POST.get('description_courte', ''),
            description_complete=request.POST.get('description_complete', ''),
            duree_jours=request.POST.get('duree_jours', 30),
            ordre_affichage=request.POST.get('ordre', 1),
            couleur=request.POST.get('couleur', '#3b82f6'),
            icone=request.POST.get('icone', '🎓'),
            is_populaire=request.POST.get('is_populaire') == 'on',
            is_recommande=request.POST.get('is_recommande') == 'on',
            features=request.POST.getlist('features[]') or [],
        )
        
        messages.success(request, f'Plan "{plan.nom}" créé avec succès.')
        return redirect('payments:admin_plans_abonnement')
        
    except Exception as e:
        messages.error(request, f'Erreur: {e}')
        return redirect('payments:admin_plans_abonnement')


# ═══════════════════════════════════════════════════════════════
# CHECKOUT FEDAPAY EMBED
# ═══════════════════════════════════════════════════════════════

@login_required
def checkout_fedapay_embed(request):
    """
    Page de checkout avec FedaPay Checkout.js embed
    """
    plan_slug = request.GET.get('plan')
    code_promo = request.GET.get('code', '')
    type_abonnement = request.GET.get('type', 'annuel')  # mensuel ou annuel
    
    if not plan_slug:
        messages.error(request, "Veuillez sélectionner un plan.")
        return redirect('payments:abonnements')
    
    plan = get_object_or_404(PlanAbonnementScolaire, slug=plan_slug, is_actif=True)
    eleve = request.user

    # Vérifier la config FedaPay via l'établissement du plan
    etablissement = plan.etablissement
    if not hasattr(etablissement, 'config_fedapay'):
        messages.warning(request, "Le paiement FedaPay n'est pas encore configuré.")
        config = None
    else:
        config = etablissement.config_fedapay
        if not config.is_actif:
            messages.error(request, "Le système de paiement est temporairement indisponible.")
            return redirect('payments:abonnements')
    
    # Calculer le montant
    if type_abonnement == 'annuel':
        montant = plan.prix_annuel_affiche
    else:
        montant = plan.prix_mensuel
    
    # Appliquer promotion
    promotion_appliquee = None
    if code_promo:
        try:
            promo = PromotionAbonnement.objects.get(
                code_promo=code_promo.upper(),
                is_actif=True,
                date_debut__lte=timezone.now(),
                date_fin__gte=timezone.now()
            )
            if promo.est_valide and (not promo.plans_applicables.exists() or plan in promo.plans_applicables.all()):
                promotion_appliquee = promo
                if promo.type_reduction == 'pourcentage':
                    montant = montant * (1 - promo.valeur_reduction / 100)
                elif promo.type_reduction == 'montant':
                    montant = max(0, montant - promo.valeur_reduction)
        except PromotionAbonnement.DoesNotExist:
            pass
    
    # Créer l'abonnement en attente
    abonnement = AbonnementEleve.objects.create(
        eleve=eleve,
        plan=plan,
        etablissement=etablissement,
        statut=AbonnementEleve.StatutAbonnement.EN_ATTENTE,
        date_debut=timezone.now(),
        date_fin=timezone.now() + timedelta(days=plan.duree_jours),
    )

    
    # Préparer le contexte
    context = {
        'plan': plan,
        'eleve': eleve,
        'montant': int(montant),
        'promotion': promotion_appliquee,
        'config_fedapay': config,
        'abonnement': abonnement,
        'callback_url': f"{settings.SITE_URL}/payments/fedapay/callback/",
        'telephone': eleve.phone or '',
    }
    
    return render(request, 'payments/fedapay_checkout_embed.html', context)


@login_required
@require_http_methods(["POST"])
def confirmer_paiement_fedapay(request):
    """
    API pour confirmer le paiement après succès FedaPay
    """
    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        abonnement_id = data.get('abonnement_id')
        
        abonnement = get_object_or_404(AbonnementEleve, id=abonnement_id, eleve=request.user)
        
        # Créer le paiement
        paiement = PaiementAbonnement.objects.create(
            abonnement=abonnement,
            eleve=request.user,
            montant=data.get('montant', 0),
            montant_total=data.get('montant', 0),
            mode_paiement=PaiementAbonnement.ModePaiement.MOBILE_MONEY,
            statut=PaiementAbonnement.StatutPaiement.SUCCES,
            fedapay_transaction_id=transaction_id,
            reference_transaction=f"ABN-{abonnement.numero_abonnement}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            date_paiement=timezone.now(),
            date_confirmation=timezone.now(),
        )
        
        # Activer l'abonnement
        abonnement.statut = AbonnementEleve.StatutAbonnement.ACTIF
        abonnement.dernier_paiement = timezone.now()
        abonnement.montant_paye_total += paiement.montant
        abonnement.nombre_paiements += 1
        abonnement.save()
        
        # Envoyer le reçu par email (tâche asynchrone)
        from .tasks import envoyer_recu_abonnement
        envoyer_recu_abonnement.delay(str(paiement.id))
        
        # Notification
        from notifications.utils import send_notification
        send_notification(
            user=request.user,
            title="🎉 Paiement confirmé !",
            message=f"Votre abonnement {abonnement.plan.nom} est maintenant actif."
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Paiement confirmé avec succès',
            'abonnement_id': str(abonnement.id),
            'paiement_id': str(paiement.id)
        })
        
    except Exception as e:
        logger.error(f"Erreur confirmation paiement: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ═══════════════════════════════════════════════════════════════
# CRUD FRAIS SCOLAIRES (ADMIN)
# ═══════════════════════════════════════════════════════════════

@staff_member_required
def admin_frais_list(request):
    """Liste des frais scolaires avec filtres par établissement"""
    etablissement_id = request.GET.get('etablissement')
    frais_qs = FraisScolaire.objects.select_related('etablissement')

    etablissements = [_get_org_plateforme()]

    if etablissement_id:
        frais_qs = frais_qs.filter(etablissement_id=etablissement_id)

    context = {
        'frais_list': frais_qs.order_by('type_frais', 'nom'),
        'etablissements': etablissements,
        'etablissement_filtre': etablissement_id,
        'types_frais': FraisScolaire.TypeFrais.choices,
    }
    return render(request, 'payments/admin_frais_list.html', context)


@staff_member_required
def admin_frais_create(request):
    """Créer un nouveau frais scolaire"""
    etablissements = [_get_org_plateforme()]
    classes = Classe.objects.all()

    if request.method == 'POST':
        try:
            etab_id = request.POST.get('etablissement')
            frais = FraisScolaire.objects.create(
                etablissement_id=etab_id,
                code=request.POST.get('code'),
                nom=request.POST.get('nom'),
                type_frais=request.POST.get('type_frais'),
                description=request.POST.get('description', ''),
                montant=request.POST.get('montant', 0),
                est_obligatoire=request.POST.get('est_obligatoire') == 'on',
                est_paiement_unique=request.POST.get('est_paiement_unique') == 'on',
                nombre_echeances=request.POST.get('nombre_echeances', 1),
                is_actif=request.POST.get('is_actif') == 'on',
            )
            classes_noms = request.POST.getlist('classes_concernees')
            frais.classes_concernees = classes_noms if classes_noms else None
            frais.save(update_fields=['classes_concernees'])
            messages.success(request, f'Frais "{frais.nom}" créé avec succès.')
            return redirect('payments:admin_frais_list')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')

    context = {
        'etablissements': etablissements,
        'classes': classes,
        'types_frais': FraisScolaire.TypeFrais.choices,
        'action': 'Créer',
        'frais': None,
    }
    return render(request, 'payments/admin_frais_form.html', context)


@staff_member_required
def admin_frais_edit(request, frais_id):
    """Modifier un frais scolaire existant"""
    frais = get_object_or_404(FraisScolaire, id=frais_id)
    etablissements = [_get_org_plateforme()]
    classes = Classe.objects.all()

    if request.method == 'POST':
        try:
            frais.etablissement_id = request.POST.get('etablissement')
            frais.code = request.POST.get('code')
            frais.nom = request.POST.get('nom')
            frais.type_frais = request.POST.get('type_frais')
            frais.description = request.POST.get('description', '')
            frais.montant = request.POST.get('montant', 0)
            frais.est_obligatoire = request.POST.get('est_obligatoire') == 'on'
            frais.est_paiement_unique = request.POST.get('est_paiement_unique') == 'on'
            frais.nombre_echeances = request.POST.get('nombre_echeances', 1)
            frais.is_actif = request.POST.get('is_actif') == 'on'
            classes_noms = request.POST.getlist('classes_concernees')
            frais.classes_concernees = classes_noms if classes_noms else None
            frais.save()
            messages.success(request, f'Frais "{frais.nom}" mis à jour.')
            return redirect('payments:admin_frais_list')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')

    context = {
        'frais': frais,
        'etablissements': etablissements,
        'classes': classes,
        'types_frais': FraisScolaire.TypeFrais.choices,
        'selected_classes': frais.classes_concernees or [],
        'action': 'Modifier',
    }
    return render(request, 'payments/admin_frais_form.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_frais_delete(request, frais_id):
    """Supprimer un frais scolaire"""
    frais = get_object_or_404(FraisScolaire, id=frais_id)
    if frais.paiements.exists():
        messages.error(request, f'Impossible de supprimer "{frais.nom}" : des paiements y sont liés.')
    else:
        nom = frais.nom
        frais.delete()
        messages.success(request, f'Frais "{nom}" supprimé.')
    return redirect('payments:admin_frais_list')


# ═══════════════════════════════════════════════════════════════
# PAYWALL — PAIEMENT CORRECTION UNITAIRE
# ═══════════════════════════════════════════════════════════════

@login_required
@require_http_methods(["POST"])
@login_required
@require_http_methods(["POST"])
def initier_paiement_correction(request, session_id):
    """
    Initie un paiement FedaPay pour débloquer la correction d'une composition.
    Retourne JSON : {'payment_url': '...'} ou {'error': '...'}.
    """
    from compositions.models import CompositionSession
    from .models import PaiementCorrectionUnitaire
    import uuid as _uuid

    try:
        session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
        montant = getattr(settings, 'PRIX_CORRECTION_UNITAIRE', 500)
        reference = f"CORR-{session.id.hex[:8].upper()}-{_uuid.uuid4().hex[:6].upper()}"

        # Créer ou récupérer un paiement en attente pour cette session
        paiement_obj, _ = PaiementCorrectionUnitaire.objects.get_or_create(
            session=session,
            eleve=request.user,
            statut='en_attente',
            defaults={
                'reference': reference,
                'montant': montant,
            }
        )

        # Tenter FedaPay si une config globale est disponible
        try:
            config = ConfigurationFedaPay.objects.filter(is_actif=True).first()
            if config:
                import requests as _requests
                base_url = (
                    "https://api.fedapay.com/v1"
                    if config.environnement == 'production'
                    else "https://sandbox-api.fedapay.com/v1"
                )
                headers = {
                    'Authorization': f'Bearer {config.cle_api_secrete}',
                    'Content-Type': 'application/json',
                }
                from django.urls import reverse
                callback_url = request.build_absolute_uri(
                    reverse('payments:correction_paiement_callback', args=[str(paiement_obj.id)])
                )
                payload = {
                    'description': f'Correction composition — {session.exam.titre}',
                    'amount': {'total': int(montant), 'currency': 'XOF'},
                    'callback_url': callback_url,
                    'metadata': {
                        'paiement_correction_id': str(paiement_obj.id),
                        'session_id': str(session.id),
                        'eleve_id': str(request.user.id),
                    },
                }
                resp = _requests.post(f'{base_url}/transactions', headers=headers, json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    payment_url = data.get('url') or data.get('payment_url')
                    paiement_obj.fedapay_transaction_id = str(data.get('id', ''))
                    paiement_obj.fedapay_url_paiement = payment_url or ''
                    paiement_obj.statut = 'en_cours'
                    paiement_obj.save()
                    if payment_url:
                        return JsonResponse({'payment_url': payment_url})
        except Exception as fedapay_err:
            logger.warning(f"FedaPay correction non disponible: {fedapay_err}")

        # Fallback : page d'abonnement (FedaPay non configuré ou erreur)
        fallback_url = request.build_absolute_uri('/payments/abonnements/')
        return JsonResponse({'payment_url': fallback_url})

    except Exception as e:
        logger.error(f"Erreur initier_paiement_correction: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def correction_paiement_callback(request, paiement_correction_id):
    """
    Callback FedaPay après paiement correction unitaire (redirection navigateur).
    Vérifie le statut de la transaction et débloque si approuvé.
    """
    from .models import PaiementCorrectionUnitaire
    from compositions.access import debloquer_correction, verifier_acces_correction

    try:
        paiement_obj = get_object_or_404(PaiementCorrectionUnitaire, id=paiement_correction_id, eleve=request.user)
        session = paiement_obj.session

        # Si le webhook a déjà traité le paiement
        if paiement_obj.statut == PaiementCorrectionUnitaire.Statut.SUCCES:
            messages.success(request, "Correction débloquée ! Vous pouvez consulter votre résultat.")
            return redirect('compositions:result_detail', session_id=session.id)

        # Vérification active via l'API FedaPay
        if paiement_obj.fedapay_transaction_id:
            config = ConfigurationFedaPay.objects.filter(is_actif=True).first()
            if config:
                service = FedaPayService.__new__(FedaPayService)
                service.etablissement = None
                service.config = config
                status = service.verifier_transaction(paiement_obj.fedapay_transaction_id)
                if status and status.get('status') == 'approved':
                    paiement_obj.statut = PaiementCorrectionUnitaire.Statut.SUCCES
                    paiement_obj.date_paiement = timezone.now()
                    paiement_obj.save(update_fields=['statut', 'date_paiement'])
                    debloquer_correction(session)
                    messages.success(request, "Paiement confirmé ! Correction débloquée.")
                    return redirect('compositions:result_detail', session_id=session.id)

        messages.warning(request, "Paiement en cours de traitement. Revenez dans quelques instants.")
        return redirect('compositions:result_detail', session_id=session.id)

    except Exception as e:
        logger.error(f"Erreur callback correction: {e}")
        messages.error(request, "Erreur lors de la vérification du paiement.")
        return redirect('payments:abonnements')


# ═══════════════════════════════════════════════════════════════════════
# GESTION PAIEMENTS ADMIN — page unifiée (remplace Django admin)
# ═══════════════════════════════════════════════════════════════════════

@staff_member_required
def admin_gestion_paiements(request):
    """
    Page de gestion paiements : abonnements, paiements, payouts corrections.
    Onglets : abonnements | paiements | répartition | actions rapides
    """
    from django.db.models import Sum as _Sum, Count as _Count
    now = timezone.now()
    tab = request.GET.get('tab', 'abonnements')

    # ── Abonnements ─────────────────────────────────────────────────
    abo_qs = AbonnementEleve.objects.select_related('eleve', 'plan').order_by('-date_souscription')
    statut_filtre = request.GET.get('statut_abo', '')
    if statut_filtre:
        abo_qs = abo_qs.filter(statut=statut_filtre)
    abonnements = list(abo_qs[:50])

    abo_stats = {
        'actifs':   AbonnementEleve.objects.filter(statut='actif', date_fin__gt=now).count(),
        'expires':  AbonnementEleve.objects.filter(statut='expire').count(),
        'attente':  AbonnementEleve.objects.filter(statut='attente').count(),
    }

    # ── Paiements abonnements ────────────────────────────────────────
    pay_abo_qs = PaiementAbonnement.objects.select_related('eleve', 'abonnement__plan').order_by('-date_creation')
    statut_pay = request.GET.get('statut_pay', '')
    if statut_pay:
        pay_abo_qs = pay_abo_qs.filter(statut=statut_pay)
    paiements_abo = list(pay_abo_qs[:50])

    rev_abo_total = PaiementAbonnement.objects.filter(statut='succes').aggregate(s=_Sum('montant'))['s'] or 0

    # ── Paiements corrections ────────────────────────────────────────
    pay_cor_qs = PaiementCorrectionUnitaire.objects.select_related(
        'session__eleve', 'session__exam'
    ).order_by('-date_creation')
    statut_cor = request.GET.get('statut_cor', '')
    if statut_cor:
        pay_cor_qs = pay_cor_qs.filter(statut=statut_cor)
    paiements_corrections = list(pay_cor_qs[:50])

    rev_cor_total = PaiementCorrectionUnitaire.objects.filter(statut='succes').aggregate(s=_Sum('montant'))['s'] or 0

    # ── Payouts corrections (répartition) ───────────────────────────
    from .models import PayoutCorrectionUnitaire
    payout_qs = PayoutCorrectionUnitaire.objects.select_related(
        'paiement__session__exam'
    ).order_by('-date_creation')
    statut_payout = request.GET.get('statut_payout', '')
    if statut_payout:
        payout_qs = payout_qs.filter(statut=statut_payout)
    payouts_corrections = list(payout_qs[:60])

    payout_stats = {
        'attente':  PayoutCorrectionUnitaire.objects.filter(statut='en_attente').count(),
        'envoye':   PayoutCorrectionUnitaire.objects.filter(statut='envoye').count(),
        'echec':    PayoutCorrectionUnitaire.objects.filter(statut='echec').count(),
        'distribue': PayoutCorrectionUnitaire.objects.filter(
            statut__in=['envoye', 'succes']
        ).aggregate(s=_Sum('montant'))['s'] or 0,
    }

    context = {
        'tab': tab,
        'abonnements': abonnements,
        'abo_stats': abo_stats,
        'statut_filtre': statut_filtre,
        'paiements_abo': paiements_abo,
        'statut_pay': statut_pay,
        'rev_abo_total': rev_abo_total,
        'paiements_corrections': paiements_corrections,
        'statut_cor': statut_cor,
        'rev_cor_total': rev_cor_total,
        'payouts_corrections': payouts_corrections,
        'statut_payout': statut_payout,
        'payout_stats': payout_stats,
        'prix_correction': getattr(settings, 'PRIX_CORRECTION_UNITAIRE', 500),
    }
    return render(request, 'payments/admin_gestion_paiements.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_toggle_abonnement(request, abonnement_id):
    """Active ou suspend manuellement un abonnement."""
    abo = get_object_or_404(AbonnementEleve, id=abonnement_id)
    action = request.POST.get('action', '')
    if action == 'activer':
        abo.statut = 'actif'
        abo.save(update_fields=['statut'])
        messages.success(request, f"Abonnement de {abo.eleve.get_full_name()} activé.")
    elif action == 'suspendre':
        abo.statut = 'suspendu'
        abo.save(update_fields=['statut'])
        messages.success(request, f"Abonnement de {abo.eleve.get_full_name()} suspendu.")
    return redirect(f"{request.META.get('HTTP_REFERER', '/payments/admin/gestion/')}#abonnements")


@staff_member_required
@require_http_methods(["POST"])
def admin_retry_payout_correction(request, payout_id):
    """Relance un payout correction en échec."""
    from .models import PayoutCorrectionUnitaire
    from .repartition import _envoyer_payout_fedapay
    payout = get_object_or_404(PayoutCorrectionUnitaire, id=payout_id)
    config = ConfigurationFedaPay.objects.filter(is_actif=True).first()
    if not config:
        messages.error(request, "Aucune config FedaPay active.")
        return redirect('/payments/admin/gestion/?tab=repartition')
    exam_titre = payout.paiement.session.exam.titre[:20] if payout.paiement else ''
    result = _envoyer_payout_fedapay(
        config,
        telephone=payout.telephone,
        montant=int(payout.montant),
        description=f"Correction {exam_titre} — {payout.beneficiaire}",
    )
    if result['success']:
        payout.statut = PayoutCorrectionUnitaire.Statut.ENVOYE
        payout.fedapay_payout_id = result['payout_id'] or ''
        payout.reponse_api = result['raw']
        payout.date_traitement = timezone.now()
        payout.message_erreur = ''
        payout.save(update_fields=['statut', 'fedapay_payout_id', 'reponse_api', 'date_traitement', 'message_erreur'])
        messages.success(request, f"Payout {payout.beneficiaire} relancé avec succès.")
    else:
        messages.error(request, f"Échec relance : {result['error']}")
    return redirect('/payments/admin/gestion/?tab=repartition')
