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
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_http_methods

from .models import (
    PlanAbonnementScolaire, AbonnementEleve, PaiementAbonnement,
    ConfigurationFedaPay, PromotionAbonnement
)
from .fedapay_service import FedaPayService, FedaPayCheckout
from .tasks import traiter_paiement_fedapay
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
    
    # Vérifier la config FedaPay
    etablissement = request.user.etablissement_eleves.first()
    if not etablissement or not hasattr(etablissement, 'config_fedapay'):
        messages.error(request, "Le paiement n'est pas disponible pour le moment.")
        return redirect('payments:abonnements')
    
    config = etablissement.config_fedapay
    if not config.is_actif:
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
        etablissement = request.user.etablissement_eleves.first()
        
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
            date_fin=timezone.now() + timezone.timedelta(days=plan.duree_jours),
            date_prochain_paiement=timezone.now() + timezone.timedelta(days=plan.duree_jours) if plan.type_plan != 'annuel' else None
        )
        
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
        
        # Lancer la tâche de paiement
        result = traiter_paiement_fedapay.delay(str(paiement.id))
        
        return JsonResponse({
            'success': True,
            'paiement_id': str(paiement.id),
            'task_id': result,
            'message': 'Paiement initié'
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
                    'redirect_url': '/payments/abonnement/succes/'
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
    Webhook pour recevoir les notifications de FedaPay
    """
    try:
        payload = request.body
        signature = request.headers.get('X-FedaPay-Signature', '')
        
        # Récupérer les données
        data = json.loads(payload)
        
        # Trouver la configuration correspondante
        # On doit identifier l'établissement à partir des métadonnées
        metadata = data.get('data', {}).get('metadata', {})
        paiement_id = metadata.get('paiement_id')
        
        if paiement_id:
            paiement = get_object_or_404(PaiementAbonnement, id=paiement_id)
            config = paiement.abonnement.etablissement.config_fedapay
            
            # Vérifier la signature
            import hmac
            import hashlib
            
            expected_signature = hmac.new(
                config.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                logger.warning("Signature webhook invalide")
                return HttpResponse(status=401)
            
            # Traiter le webhook
            service = FedaPayService(paiement.abonnement.etablissement)
            service.traiter_webhook(data)
            
            return HttpResponse(status=200)
        
        return HttpResponse(status=400)
        
    except Exception as e:
        logger.error(f"Erreur webhook FedaPay: {e}")
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
    etablissements = Etablissement.objects.all()
    
    configs = []
    for etab in etablissements:
        config, created = ConfigurationFedaPay.objects.get_or_create(
            etablissement=etab,
            defaults={
                'nom_marchand': etab.nom,
                'email_marchand': etab.email or 'contact@exemple.com',
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
def admin_plans_abonnement(request):
    """
    Gestion des plans d'abonnement (Super Admin)
    """
    plans = PlanAbonnementScolaire.objects.all().select_related('etablissement')
    etablissements = Etablissement.objects.filter(is_actif=True)
    
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
            etablissement_id=request.POST.get('etablissement'),
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
    
    # Vérifier la config FedaPay
    etablissement = eleve.etablissement_eleves.first()
    if not etablissement or not hasattr(etablissement, 'config_fedapay'):
        messages.error(request, "Le paiement n'est pas disponible pour le moment.")
        return redirect('payments:abonnements')
    
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
        send_notification.delay(
            user_id=request.user.id,
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
