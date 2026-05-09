"""
Tâches Redis pour le module paiements
Traitement des paiements Mobile Money, génération de reçus
"""

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from core.redis_tasks import redis_task
from .models import Paiement, TransactionPaiement, EcheancierPaiement

logger = logging.getLogger(__name__)


@redis_task("payments.traiter_paiement_mobile")
def traiter_paiement_mobile(paiement_id, telephone, operateur):
    """
    Traiter un paiement via Mobile Money en arrière-plan
    """
    try:
        from django.shortcuts import get_object_or_404
        
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Simuler l'API Mobile Money (à remplacer par l'API réelle)
        logger.info(f"💰 Traitement paiement {paiement.numero_paiement} - {operateur} - {telephone}")
        
        # Dans un vrai scénario, appeler l'API de l'opérateur
        # Exemple avec MTN MoMo, Orange Money, Wave...
        
        # Simulation réussie
        transaction = TransactionPaiement.objects.create(
            paiement=paiement,
            type_transaction='paiement',
            montant=paiement.montant_paye,
            mode_paiement=paiement.mode_paiement,
            operateur=operateur,
            numero_telephone=telephone,
            est_reussi=True,
            reference_transaction=f"TXN-{operateur.upper()}-{paiement.id[:8]}"
        )
        
        # Mettre à jour le statut du paiement
        paiement.statut = Paiement.StatutPaiement.COMPLET
        paiement.save()
        
        # Générer le reçu
        generer_reçu_paiement.delay(str(paiement.id))
        
        # Envoyer notification
        from notifications.utils import send_notification
        send_notification.delay(
            user_id=paiement.eleve.id,
            title="Paiement confirmé",
            message=f"Votre paiement de {paiement.montant_paye:,.0f} FCFA a été confirmé"
        )
        
        logger.info(f"✅ Paiement {paiement.numero_paiement} traité avec succès")
        return f"Paiement traité: {transaction.reference_transaction}"
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement paiement {paiement_id}: {e}")
        # Marquer la transaction comme échouée
        TransactionPaiement.objects.create(
            paiement_id=paiement_id,
            type_transaction='paiement',
            est_reussi=False,
            message_erreur=str(e)
        )
        raise


@redis_task("payments.generer_recu")
def generer_reçu_paiement(paiement_id):
    """
    Générer le reçu PDF d'un paiement
    """
    try:
        from io import BytesIO
        from django.core.files import File
        from xhtml2pdf import pisa
        from django.shortcuts import get_object_or_404
        
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Rendre le template
        html_content = render_to_string('payments/recu_template.html', {
            'paiement': paiement,
            'etablissement': paiement.frais.etablissement,
        })
        
        # Générer PDF
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content.encode('utf-8'), dest=pdf_buffer)
        pdf_buffer.seek(0)
        
        # Sauvegarder
        filename = f"recu_{paiement.numero_paiement}.pdf"
        # Sauvegarder le fichier (à adapter selon le modèle)
        
        # Envoyer email avec le reçu
        envoyer_email_recu.delay(paiement_id, filename)
        
        logger.info(f"✅ Reçu généré: {filename}")
        return f"Reçu généré: {filename}"
        
    except Exception as e:
        logger.error(f"❌ Erreur génération reçu {paiement_id}: {e}")
        raise


@redis_task("payments.envoyer_email_recu")
def envoyer_email_recu(paiement_id, fichier_pdf=None):
    """
    Envoyer le reçu de paiement par email
    """
    try:
        from django.shortcuts import get_object_or_404
        
        paiement = get_object_or_404(Paiement, id=paiement_id)
        eleve = paiement.eleve
        
        subject = f"Reçu de paiement - {paiement.frais.nom}"
        message = render_to_string('payments/email_recu.html', {
            'eleve': eleve,
            'paiement': paiement,
            'etablissement': paiement.frais.etablissement,
        })
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[eleve.email],
            html_message=message,
            fail_silently=True
        )
        
        logger.info(f"✅ Email reçu envoyé à {eleve.email}")
        return f"Email envoyé à {eleve.email}"
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email reçu {paiement_id}: {e}")
        raise


@redis_task("payments.verifier_echeances")
def verifier_echeances_retard():
    """
    Vérifier les échéances de paiement en retard et envoyer des rappels
    """
    try:
        from datetime import date, timedelta
        from notifications.utils import send_notification
        
        today = date.today()
        
        # Échéances dans 3 jours
        echeances_proches = EcheancierPaiement.objects.filter(
            is_paye=False,
            date_echeance__lte=today + timedelta(days=3),
            date_echeance__gte=today
        )
        
        for echeance in echeances_proches:
            paiement = echeance.paiement
            eleve = paiement.eleve
            
            # Envoyer notification
            send_notification.delay(
                user_id=eleve.id,
                title="Rappel de paiement",
                message=f"Votre échéance de {echeance.montant:,.0f} FCFA arrive à échéance le {echeance.date_echeance}"
            )
        
        # Échéances en retard
        echeances_retard = EcheancierPaiement.objects.filter(
            is_paye=False,
            date_echeance__lt=today
        )
        
        for echeance in echeances_retard:
            paiement = echeance.paiement
            paiement.statut = Paiement.StatutPaiement.EN_RETARD
            paiement.save()
        
        logger.info(f"✅ Vérification échéances: {echeances_proches.count()} rappels, {echeances_retard.count()} retards")
        return f"Rappels: {echeances_proches.count()}, Retards: {echeances_retard.count()}"
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification échéances: {e}")
        raise


@redis_task("payments.generer_rapport_financier")
def generer_rapport_financier(etablissement_id, date_debut, date_fin, rapport_id=None):
    """
    Générer un rapport financier périodique
    """
    try:
        from .models import RapportFinancier
        from django.shortcuts import get_object_or_404
        from decimal import Decimal
        
        etablissement = get_object_or_404('schools.Etablissement', id=etablissement_id)
        
        # Calculer les statistiques
        paiements = Paiement.objects.filter(
            frais__etablissement=etablissement,
            date_paiement__range=[date_debut, date_fin]
        )
        
        total_encaisse = sum(p.montant_paye for p in paiements)
        total_attendu = sum(p.montant_total for p in paiements)
        
        # Créer ou mettre à jour le rapport
        if rapport_id:
            rapport = get_object_or_404(RapportFinancier, id=rapport_id)
        else:
            rapport = RapportFinancier(etablissement=etablissement)
        
        rapport.periode_debut = date_debut
        rapport.periode_fin = date_fin
        rapport.total_encaisse = total_encaisse
        rapport.total_attendu = total_attendu
        rapport.total_impaye = total_attendu - total_encaisse
        rapport.taux_recouvrement = (total_encaisse / total_attendu * 100) if total_attendu > 0 else 0
        rapport.nombre_paiements = paiements.count()
        
        rapport.save()
        
        logger.info(f"✅ Rapport financier généré: {rapport.total_encaisse:,.0f} FCFA encaissés")
        return f"Rapport généré - {rapport.total_encaisse:,.0f} FCFA"
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport financier: {e}")
        raise


# ═══════════════════════════════════════════════════════════════
# TÂCHES ABONNEMENTS & FEDAPAY
# ═══════════════════════════════════════════════════════════════

@redis_task("payments.traiter_paiement_fedapay")
def traiter_paiement_fedapay(paiement_id, customer_data=None):
    """
    Traiter un paiement via FedaPay
    """
    try:
        from .models import PaiementAbonnement, ConfigurationFedaPay
        from .fedapay_service import FedaPayService
        from django.shortcuts import get_object_or_404
        
        paiement = get_object_or_404(PaiementAbonnement, id=paiement_id)
        abonnement = paiement.abonnement
        eleve = paiement.eleve
        
        # Vérifier la config FedaPay
        config = abonnement.etablissement.config_fedapay
        if not config or not config.is_actif:
            raise ValueError("Configuration FedaPay non disponible")
        
        # Initialiser le service
        fedapay = FedaPayService(abonnement.etablissement)
        
        # Créer ou récupérer le customer
        if not abonnement.fedapay_customer_id:
            customer_id = fedapay.creer_customer(eleve)
            if customer_id:
                abonnement.fedapay_customer_id = customer_id
                abonnement.save()
        else:
            customer_id = abonnement.fedapay_customer_id
        
        # Créer la transaction
        result = fedapay.creer_transaction(
            paiement=paiement,
            customer_id=customer_id,
            callback_url=f"{settings.SITE_URL}/payments/fedapay/callback/"
        )
        
        if result:
            paiement.statut = paiement.StatutPaiement.EN_COURS
            paiement.save()
            
            logger.info(f"✅ Paiement FedaPay initié: {result['transaction_id']}")
            return {
                'transaction_id': result['transaction_id'],
                'payment_url': result['payment_url']
            }
        else:
            raise Exception("Échec création transaction FedaPay")
            
    except Exception as e:
        logger.error(f"❌ Erreur paiement FedaPay {paiement_id}: {e}")
        paiement.derniere_erreur = str(e)
        paiement.save()
        raise


@redis_task("payments.envoyer_recu_abonnement")
def envoyer_recu_abonnement(paiement_id):
    """
    Générer et envoyer le reçu d'abonnement par email
    """
    try:
        from io import BytesIO
        from django.core.files import File
        from xhtml2pdf import pisa
        from django.template.loader import render_to_string
        from django.core.mail import send_mail
        from django.shortcuts import get_object_or_404
        from .models import PaiementAbonnement
        
        paiement = get_object_or_404(PaiementAbonnement, id=paiement_id)
        eleve = paiement.eleve
        abonnement = paiement.abonnement
        
        # Générer le PDF
        html_content = render_to_string('payments/recu_abonnement.html', {
            'paiement': paiement,
            'abonnement': abonnement,
            'eleve': eleve,
            'plan': abonnement.plan,
            'etablissement': abonnement.etablissement,
        })
        
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content.encode('utf-8'), dest=pdf_buffer)
        pdf_buffer.seek(0)
        
        # Sauvegarder
        filename = f"recu_abonnement_{paiement.reference_transaction}.pdf"
        paiement.recu_pdf.save(filename, File(pdf_buffer))
        
        # Envoyer email
        subject = f"🎓 Reçu de paiement - {abonnement.plan.nom}"
        message = render_to_string('payments/email_recu_abonnement.html', {
            'eleve': eleve,
            'paiement': paiement,
            'abonnement': abonnement,
        })
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[eleve.email],
            html_message=message,
            fail_silently=True
        )
        
        logger.info(f"✅ Reçu abonnement envoyé à {eleve.email}")
        return f"Reçu envoyé à {eleve.email}"
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi reçu abonnement {paiement_id}: {e}")
        raise


@redis_task("payments.rappel_abonnement_7j")
def rappel_abonnement_7j(abonnement_id):
    """
    Envoyer un rappel 7 jours avant expiration
    """
    try:
        from django.shortcuts import get_object_or_404
        from .models import AbonnementEleve
        from notifications.utils import send_notification
        
        abonnement = get_object_or_404(AbonnementEleve, id=abonnement_id)
        
        if abonnement.jours_restants <= 7 and not abonnement.rappel_7j_envoye:
            eleve = abonnement.eleve
            jours = abonnement.jours_restants
            
            # Email
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            
            subject = f"⏰ Votre abonnement expire dans {jours} jours"
            message = render_to_string('payments/email_rappel_renouvellement.html', {
                'eleve': eleve,
                'abonnement': abonnement,
                'jours_restants': jours,
                'plan': abonnement.plan,
                'url_renouvellement': f"{settings.SITE_URL}/abonnements/renouveler/{abonnement.id}/",
            })
            
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[eleve.email],
                html_message=message,
                fail_silently=True
            )
            
            # Notification push
            send_notification.delay(
                user_id=eleve.id,
                title=f"⏰ Abonnement expire dans {jours} jours",
                message=f"Renouvelez votre abonnement {abonnement.plan.nom} pour ne pas perdre l'accès"
            )
            
            abonnement.rappel_7j_envoye = True
            abonnement.save()
            
            logger.info(f"✅ Rappel 7j envoyé à {eleve.email}")
            return f"Rappel envoyé à {eleve.email}"
            
    except Exception as e:
        logger.error(f"❌ Erreur rappel 7j {abonnement_id}: {e}")
        raise


@redis_task("payments.rappel_abonnement_3j")
def rappel_abonnement_3j(abonnement_id):
    """
    Envoyer un rappel 3 jours avant expiration (plus urgent)
    """
    try:
        from django.shortcuts import get_object_or_404
        from .models import AbonnementEleve
        from notifications.utils import send_notification
        
        abonnement = get_object_or_404(AbonnementEleve, id=abonnement_id)
        
        if abonnement.jours_restants <= 3 and not abonnement.rappel_3j_envoye:
            eleve = abonnement.eleve
            
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            
            subject = "⚠️ ACTION REQUISE : Votre abonnement expire dans 3 jours"
            message = render_to_string('payments/email_rappel_urgent.html', {
                'eleve': eleve,
                'abonnement': abonnement,
                'jours_restants': abonnement.jours_restants,
                'url_renouvellement': f"{settings.SITE_URL}/abonnements/renouveler/{abonnement.id}/",
            })
            
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[eleve.email],
                html_message=message,
                fail_silently=True
            )
            
            # Notification push urgente
            send_notification.delay(
                user_id=eleve.id,
                title="⚠️ Abonnement expire bientôt !",
                message=f"Plus que {abonnement.jours_restants} jours. Renouvelez maintenant !",
                priority='high'
            )
            
            abonnement.rappel_3j_envoye = True
            abonnement.save()
            
            logger.info(f"✅ Rappel 3j (urgent) envoyé à {eleve.email}")
            return f"Rappel urgent envoyé à {eleve.email}"
            
    except Exception as e:
        logger.error(f"❌ Erreur rappel 3j {abonnement_id}: {e}")
        raise


@redis_task("payments.rappel_abonnement_1j")
def rappel_abonnement_1j(abonnement_id):
    """
    Dernier rappel 1 jour avant expiration
    """
    try:
        from django.shortcuts import get_object_or_404
        from .models import AbonnementEleve
        from notifications.utils import send_notification
        
        abonnement = get_object_or_404(AbonnementEleve, id=abonnement_id)
        
        if abonnement.jours_restants <= 1 and not abonnement.rappel_1j_envoye:
            eleve = abonnement.eleve
            
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            
            subject = "🚨 DERNIER JOUR : Votre abonnement expire demain !"
            message = render_to_string('payments/email_rappel_dernier_jour.html', {
                'eleve': eleve,
                'abonnement': abonnement,
                'url_renouvellement': f"{settings.SITE_URL}/abonnements/renouveler/{abonnement.id}/",
            })
            
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[eleve.email],
                html_message=message,
                fail_silently=True
            )
            
            # Notification push critique
            send_notification.delay(
                user_id=eleve.id,
                title="🚨 DERNIER JOUR !",
                message="Votre abonnement expire demain. Renouvelez immédiatement !",
                priority='critical'
            )
            
            abonnement.rappel_1j_envoye = True
            abonnement.save()
            
            logger.info(f"✅ Rappel 1j (critique) envoyé à {eleve.email}")
            return f"Dernier rappel envoyé à {eleve.email}"
            
    except Exception as e:
        logger.error(f"❌ Erreur rappel 1j {abonnement_id}: {e}")
        raise


@redis_task("payments.verifier_abonnements_expires")
def verifier_abonnements_expires():
    """
    Vérifier tous les abonnements expirés et suspendre l'accès
    """
    try:
        from django.utils import timezone
        from .models import AbonnementEleve
        from notifications.utils import send_notification
        
        abonnements_expires = AbonnementEleve.objects.filter(
            statut=AbonnementEleve.StatutAbonnement.ACTIF,
            date_fin__lt=timezone.now()
        )
        
        count = 0
        for abonnement in abonnements_expires:
            abonnement.statut = AbonnementEleve.StatutAbonnement.EXPIRE
            abonnement.save()
            
            # Notifier l'élève
            send_notification.delay(
                user_id=abonnement.eleve.id,
                title="⛔ Abonnement expiré",
                message=f"Votre abonnement {abonnement.plan.nom} a expiré. Renouvelez pour retrouver l'accès."
            )
            
            # Email
            from django.core.mail import send_mail
            send_mail(
                subject="Votre abonnement a expiré",
                message=f"Bonjour {abonnement.eleve.first_name},\n\nVotre abonnement {abonnement.plan.nom} a expiré. Renouvelez-le pour continuer à accéder à toutes les fonctionnalités.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[abonnement.eleve.email],
                fail_silently=True
            )
            
            count += 1
        
        logger.info(f"✅ {count} abonnements expirés traités")
        return f"{count} abonnements expirés"
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification abonnements expirés: {e}")
        raise


@redis_task("payments.generer_rapport_abonnements")
def generer_rapport_abonnements(etablissement_id, date_debut, date_fin):
    """
    Générer un rapport des abonnements
    """
    try:
        from django.shortcuts import get_object_or_404
        from schools.models import Etablissement
        from .models import AbonnementEleve, PaiementAbonnement
        
        etablissement = get_object_or_404(Etablissement, id=etablissement_id)
        
        # Statistiques
        abonnements = AbonnementEleve.objects.filter(
            etablissement=etablissement,
            date_souscription__range=[date_debut, date_fin]
        )
        
        paiements = PaiementAbonnement.objects.filter(
            abonnement__etablissement=etablissement,
            date_creation__range=[date_debut, date_fin],
            statut=PaiementAbonnement.StatutPaiement.SUCCES
        )
        
        stats = {
            'total_abonnements': abonnements.count(),
            'actifs': abonnements.filter(statut=AbonnementEleve.StatutAbonnement.ACTIF).count(),
            'expirés': abonnements.filter(statut=AbonnementEleve.StatutAbonnement.EXPIRE).count(),
            'revenus_total': sum(p.montant for p in paiements),
            'nouveaux': abonnements.filter(statut=AbonnementEleve.StatutAbonnement.ACTIF, nombre_paiements=1).count(),
            'renouvellements': abonnements.filter(statut=AbonnementEleve.StatutAbonnement.ACTIF, nombre_paiements__gt=1).count(),
        }
        
        logger.info(f"✅ Rapport abonnements généré: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur rapport abonnements: {e}")
        raise
