"""
Service d'intégration FedaPay
Gestion des paiements, abonnements et webhooks
"""

import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FedaPayService:
    """
    Service d'intégration avec l'API FedaPay
    """
    
    SANDBOX_URL = "https://sandbox-api.fedapay.com/v1"
    PRODUCTION_URL = "https://api.fedapay.com/v1"
    
    def __init__(self, etablissement=None):
        """
        Initialiser le service avec la configuration d'un établissement
        """
        self.etablissement = etablissement
        self.config = None
        
        if etablissement:
            try:
                self.config = etablissement.config_fedapay
            except:
                logger.warning(f"Pas de configuration FedaPay pour {etablissement.nom}")
    
    @property
    def base_url(self):
        """URL de base selon l'environnement"""
        if self.config and self.config.environnement == 'production':
            return self.PRODUCTION_URL
        return self.SANDBOX_URL
    
    @property
    def headers(self):
        """Headers pour les requêtes API"""
        if not self.config:
            raise ValueError("Configuration FedaPay non disponible")
        
        return {
            'Authorization': f'Bearer {self.config.cle_api_secrete}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def creer_customer(self, eleve):
        """
        Créer un customer FedaPay pour un élève
        """
        try:
            data = {
                'firstname': eleve.first_name,
                'lastname': eleve.last_name,
                'email': eleve.email,
                'phone_number': {
                    'number': eleve.phone or '',
                    'country': 'BJ'  # Bénin
                }
            }
            
            response = requests.post(
                f"{self.base_url}/customers",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                customer_id = result.get('id')
                logger.info(f"✅ Customer FedaPay créé: {customer_id} pour {eleve.email}")
                return customer_id
            else:
                logger.error(f"❌ Erreur création customer: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception création customer FedaPay: {e}")
            return None
    
    def creer_transaction(self, paiement, customer_id, callback_url=None):
        """
        Créer une transaction de paiement
        """
        try:
            data = {
                'description': f"Abonnement {paiement.abonnement.plan.nom}",
                'amount': {
                    'total': int(paiement.montant),
                    'currency': 'XOF'
                },
                'customer': {
                    'id': customer_id
                },
                'callback_url': callback_url or settings.SITE_URL,
                'metadata': {
                    'paiement_id': str(paiement.id),
                    'eleve_id': str(paiement.eleve.id),
                    'plan': paiement.abonnement.plan.nom
                }
            }
            
            response = requests.post(
                f"{self.base_url}/transactions",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                transaction_id = result.get('id')
                payment_url = result.get('url')
                
                # Mettre à jour le paiement
                paiement.fedapay_transaction_id = transaction_id
                paiement.fedapay_url_paiement = payment_url
                paiement.save()
                
                logger.info(f"✅ Transaction créée: {transaction_id}")
                return {
                    'transaction_id': transaction_id,
                    'payment_url': payment_url,
                    'status': result.get('status')
                }
            else:
                logger.error(f"❌ Erreur création transaction: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception création transaction: {e}")
            return None
    
    def verifier_transaction(self, transaction_id):
        """
        Vérifier le statut d'une transaction
        """
        try:
            response = requests.get(
                f"{self.base_url}/transactions/{transaction_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'status': result.get('status'),  # pending, approved, declined, canceled
                    'amount': result.get('amount', {}).get('total'),
                    'currency': result.get('amount', {}).get('currency'),
                    'customer': result.get('customer'),
                    'payment_method': result.get('payment_method')
                }
            else:
                logger.error(f"❌ Erreur vérification transaction: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception vérification transaction: {e}")
            return None
    
    def rembourser_transaction(self, transaction_id, amount=None):
        """
        Rembourser une transaction
        """
        try:
            data = {}
            if amount:
                data['amount'] = int(amount)
            
            response = requests.post(
                f"{self.base_url}/transactions/{transaction_id}/refund",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Transaction remboursée: {transaction_id}")
                return True
            else:
                logger.error(f"❌ Erreur remboursement: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception remboursement: {e}")
            return False
    
    def generer_token_paiement(self, transaction_id):
        """
        Générer un token de paiement pour Mobile Money
        """
        try:
            response = requests.post(
                f"{self.base_url}/transactions/{transaction_id}/token",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('token')
            else:
                logger.error(f"❌ Erreur génération token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception génération token: {e}")
            return None
    
    def verifier_webhook(self, payload, signature):
        """
        Vérifier la signature d'un webhook FedaPay
        """
        import hmac
        import hashlib
        
        try:
            expected_signature = hmac.new(
                self.config.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"❌ Erreur vérification webhook: {e}")
            return False
    
    def traiter_webhook(self, data):
        """
        Traiter un webhook reçu de FedaPay
        """
        try:
            event = data.get('event')
            transaction_data = data.get('data', {})
            transaction_id = transaction_data.get('id')
            
            logger.info(f"📩 Webhook reçu: {event} - Transaction: {transaction_id}")
            
            # Récupérer le paiement associé
            from .models import PaiementAbonnement
            
            try:
                paiement = PaiementAbonnement.objects.get(fedapay_transaction_id=transaction_id)
            except PaiementAbonnement.DoesNotExist:
                logger.error(f"❌ Paiement non trouvé pour transaction: {transaction_id}")
                return False
            
            # Traiter selon l'événement
            if event == 'transaction.approved':
                return self._transaction_approuvee(paiement, transaction_data)
            elif event == 'transaction.declined':
                return self._transaction_refusee(paiement, transaction_data)
            elif event == 'transaction.canceled':
                return self._transaction_annulee(paiement, transaction_data)
            elif event == 'transaction.refunded':
                return self._transaction_rembourse(paiement, transaction_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Exception traitement webhook: {e}")
            return False
    
    def _transaction_approuvee(self, paiement, data):
        """
        Traiter une transaction approuvée
        """
        try:
            from core.redis_tasks import redis_task
            
            # Mettre à jour le statut
            paiement.statut = PaiementAbonnement.StatutPaiement.SUCCES
            paiement.date_paiement = timezone.now()
            paiement.fedapay_webhook_data = data
            paiement.save()
            
            # Activer l'abonnement
            abonnement = paiement.abonnement
            abonnement.statut = abonnement.StatutAbonnement.ACTIF
            abonnement.date_debut = timezone.now()
            abonnement.date_fin = timezone.now() + timedelta(days=abonnement.plan.duree_jours)
            abonnement.dernier_paiement = timezone.now()
            abonnement.montant_paye_total += paiement.montant
            abonnement.nombre_paiements += 1
            abonnement.save()
            
            # Envoyer reçu par email
            from .tasks import envoyer_recu_abonnement
            envoyer_recu_abonnement.delay(str(paiement.id))
            
            # Notification de succès
            from notifications.utils import send_notification
            send_notification.delay(
                user_id=paiement.eleve.id,
                title="🎉 Paiement confirmé !",
                message=f"Votre abonnement {abonnement.plan.nom} est maintenant actif."
            )
            
            logger.info(f"✅ Transaction approuvée traitée: {paiement.fedapay_transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement transaction approuvée: {e}")
            return False
    
    def _transaction_refusee(self, paiement, data):
        """
        Traiter une transaction refusée
        """
        paiement.statut = paiement.StatutPaiement.ECHEC
        paiement.fedapay_webhook_data = data
        paiement.save()
        
        # Notification d'échec
        from notifications.utils import send_notification
        send_notification.delay(
            user_id=paiement.eleve.id,
            title="❌ Paiement refusé",
            message="Votre paiement n'a pas pu être traité. Veuillez réessayer."
        )
        
        return True
    
    def _transaction_annulee(self, paiement, data):
        """
        Traiter une transaction annulée
        """
        paiement.statut = paiement.StatutPaiement.ANNULE
        paiement.fedapay_webhook_data = data
        paiement.save()
        return True
    
    def _transaction_rembourse(self, paiement, data):
        """
        Traiter une transaction remboursée
        """
        paiement.statut = paiement.StatutPaiement.REMBOURSE
        paiement.fedapay_webhook_data = data
        paiement.save()
        
        # Suspendre l'abonnement
        abonnement = paiement.abonnement
        abonnement.statut = abonnement.StatutAbonnement.SUSPENDU
        abonnement.save()
        
        return True


class FedaPayCheckout:
    """
    Classe utilitaire pour créer un checkout FedaPay simple
    """
    
    @staticmethod
    def creer_checkout_url(eleve, montant, description, reference, callback_url=None, etablissement=None):
        """
        Créer une URL de checkout simple pour un paiement
        """
        try:
            # Récupérer la config FedaPay via l'abonnement actif de l'élève
            if etablissement is None:
                abonnement = eleve.abonnements.select_related('etablissement').filter(statut='actif').first()
                etablissement = abonnement.etablissement if abonnement else None
            if not etablissement or not hasattr(etablissement, 'config_fedapay'):
                logger.error("Configuration FedaPay non trouvée")
                return None
            
            config = etablissement.config_fedapay
            
            base_url = "https://pay.fedapay.com" if config.environnement == 'production' else "https://pay.sandbox.fedapay.com"
            
            params = {
                'public_key': config.cle_api_publique,
                'amount': int(montant),
                'currency': 'XOF',
                'description': description,
                'reference': reference,
                'callback_url': callback_url or settings.SITE_URL,
                'customer_email': eleve.email,
                'customer_firstname': eleve.first_name,
                'customer_lastname': eleve.last_name,
                'customer_phone': eleve.phone or '',
            }
            
            # Construire l'URL
            import urllib.parse
            query_string = urllib.parse.urlencode(params)
            checkout_url = f"{base_url}/?{query_string}"
            
            return checkout_url
            
        except Exception as e:
            logger.error(f"❌ Erreur création checkout URL: {e}")
            return None
