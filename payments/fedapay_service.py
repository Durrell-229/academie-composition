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
    Service d'intégration avec l'API FedaPay.
    Priorité config : DB (ConfigurationFedaPay) → variables d'environnement (settings.FEDAPAY_*)
    """

    SANDBOX_URL = "https://sandbox-api.fedapay.com/v1"
    PRODUCTION_URL = "https://api.fedapay.com/v1"

    def __init__(self, etablissement=None):
        self.etablissement = etablissement
        self.config = None

        if etablissement:
            try:
                self.config = etablissement.config_fedapay
            except Exception:
                logger.warning(f"Pas de configuration FedaPay en DB pour {getattr(etablissement, 'nom', etablissement)} — fallback sur settings.")

    @property
    def _env(self):
        """Environnement actif : DB > settings."""
        if self.config:
            return self.config.environnement
        return getattr(settings, 'FEDAPAY_ENVIRONMENT', 'sandbox')

    @property
    def _secret_key(self):
        """Clé secrète active : DB > settings."""
        if self.config and self.config.cle_api_secrete:
            return self.config.cle_api_secrete
        return getattr(settings, 'FEDAPAY_SECRET_KEY', '')

    @property
    def _public_key(self):
        """Clé publique active : DB > settings."""
        if self.config and self.config.cle_api_publique:
            return self.config.cle_api_publique
        return getattr(settings, 'FEDAPAY_PUBLIC_KEY', '')

    @property
    def _webhook_secret(self):
        """Secret webhook : DB > settings."""
        if self.config and self.config.webhook_secret:
            return self.config.webhook_secret
        return getattr(settings, 'FEDAPAY_WEBHOOK_SECRET', '')

    @property
    def base_url(self):
        """URL de base selon l'environnement."""
        return self.PRODUCTION_URL if self._env == 'production' else self.SANDBOX_URL

    @property
    def headers(self):
        """Headers pour les requêtes API."""
        key = self._secret_key
        if not key:
            raise ValueError("Clé secrète FedaPay non configurée. Ajoutez FEDAPAY_SECRET_KEY dans .env")
        return {
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
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
        Vérifier la signature d'un webhook FedaPay via le SDK officiel.
        payload : bytes (request.body) ou str.
        signature : valeur de l'en-tête X-FEDAPAY-SIGNATURE.
        """
        from fedapay import WebhookSignature
        secret = self._webhook_secret
        if not secret:
            logger.warning("FEDAPAY_WEBHOOK_SECRET non configuré — webhook non vérifié.")
            return True  # Mode dégradé : accepter sans vérification si secret absent
        try:
            payload_bytes = payload if isinstance(payload, bytes) else payload.encode('utf-8')
            WebhookSignature.verify_header(payload_bytes, signature, secret)
            return True
        except Exception as e:
            logger.error(f"❌ Signature webhook invalide: {e}")
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
        Traiter une transaction approuvée, puis distribuer les commissions.
        """
        try:
            # Mettre à jour le statut du paiement
            paiement.statut = paiement.StatutPaiement.SUCCES
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

            # Distribuer les commissions automatiquement
            try:
                self.envoyer_payouts(paiement)
            except Exception as e_pay:
                logger.error(f"❌ Erreur distribution commissions (paiement {paiement.id}): {e_pay}")

            # Envoyer reçu par email
            try:
                from .tasks import envoyer_recu_abonnement
                envoyer_recu_abonnement.delay(str(paiement.id))
            except Exception:
                pass

            # Notification de succès
            try:
                from notifications.utils import send_notification
                send_notification(
                    user=paiement.eleve,
                    title="Paiement confirmé !",
                    message=f"Votre abonnement {abonnement.plan.nom} est maintenant actif."
                )
            except Exception:
                pass

            logger.info(f"✅ Transaction approuvée traitée: {paiement.fedapay_transaction_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur traitement transaction approuvée: {e}")
            return False

    # ─────────────────────────────────────────────────────────────
    # PAYOUT / RÉPARTITION DES COMMISSIONS
    # ─────────────────────────────────────────────────────────────

    def envoyer_payouts(self, paiement) -> dict:
        """
        Calcule et envoie les 3 parts (admin / commercial / prestataire)
        via l'API payout FedaPay, puis crée les lignes PayoutCommission.

        Flux :
          1. Récupérer ConfigurationCommission de l'établissement
          2. Calculer chaque part
          3. Appeler _envoyer_payout_unique() pour chaque bénéficiaire
          4. Retourner un résumé
        """
        from .models import ConfigurationCommission, PayoutCommission

        etablissement = paiement.abonnement.plan.etablissement

        try:
            config_commission = ConfigurationCommission.objects.get(
                etablissement=etablissement, is_actif=True
            )
        except ConfigurationCommission.DoesNotExist:
            logger.info(
                f"Aucune configuration de commission pour {etablissement} "
                f"— payouts ignorés (mode sans commission)."
            )
            return {'success': True, 'skipped': True, 'reason': 'Aucune configuration de commission'}

        montant = int(paiement.montant)
        parts = config_commission.calculer_parts(montant)

        beneficiaires = [
            ('admin',       config_commission.telephone_admin,       parts['admin'],       config_commission.taux_admin),
            ('commercial',  config_commission.telephone_commercial,  parts['commercial'],  config_commission.taux_commercial),
            ('prestataire', config_commission.telephone_prestataire, parts['prestataire'], config_commission.taux_prestataire),
        ]

        resultats = {}
        for role, telephone, montant_part, taux in beneficiaires:
            payout_obj = PayoutCommission.objects.create(
                paiement=paiement,
                beneficiaire=role,
                telephone=telephone,
                montant=montant_part,
                taux_applique=taux,
                statut=PayoutCommission.Statut.EN_ATTENTE,
            )
            reponse = self._envoyer_payout_unique(telephone, montant_part, payout_obj)
            resultats[role] = reponse

        logger.info(
            f"Payouts distribués — paiement {paiement.id}: "
            f"admin {parts['admin']} / commercial {parts['commercial']} / prestataire {parts['prestataire']} FCFA"
        )
        return {'success': True, 'parts': parts, 'resultats': resultats}

    def _envoyer_payout_unique(self, telephone: str, montant: int, payout_obj) -> dict:
        """
        Appelle POST /v1/payouts sur l'API FedaPay pour un seul bénéficiaire,
        puis met à jour le PayoutCommission.
        """
        from .models import PayoutCommission

        payload = {
            'send_now': True,
            'payouts': [
                {
                    'amount': montant,
                    'currency': {'iso': 'XOF'},
                    'mode': 'mtn',
                    'customer': {
                        'phone_number': {
                            'number': telephone,
                            'country': 'BJ',
                        }
                    },
                }
            ],
        }

        try:
            response = requests.post(
                f"{self.base_url}/payouts",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            result = response.json()

            if response.status_code in [200, 201]:
                payout_id = (
                    result.get('v_payouts', [{}])[0].get('id', '')
                    if 'v_payouts' in result
                    else result.get('id', '')
                )
                payout_obj.statut = PayoutCommission.Statut.ENVOYE
                payout_obj.fedapay_payout_id = str(payout_id)
                payout_obj.reponse_api = result
                payout_obj.date_traitement = timezone.now()
                payout_obj.save()
                logger.info(f"✅ Payout envoyé: {telephone} — {montant} FCFA")
                return {'success': True, 'payout_id': payout_id}
            else:
                payout_obj.statut = PayoutCommission.Statut.ECHEC
                payout_obj.reponse_api = result
                payout_obj.message_erreur = response.text[:500]
                payout_obj.date_traitement = timezone.now()
                payout_obj.save()
                logger.error(f"❌ Payout échoué {telephone}: {response.text[:200]}")
                return {'success': False, 'error': response.text[:200]}

        except Exception as e:
            payout_obj.statut = PayoutCommission.Statut.ECHEC
            payout_obj.message_erreur = str(e)[:500]
            payout_obj.date_traitement = timezone.now()
            payout_obj.save()
            logger.error(f"❌ Exception payout {telephone}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _transaction_refusee(self, paiement, data):
        """
        Traiter une transaction refusée
        """
        paiement.statut = paiement.StatutPaiement.ECHEC
        paiement.fedapay_webhook_data = data
        paiement.save()
        
        # Notification d'échec
        from notifications.utils import send_notification
        send_notification(
            user=paiement.eleve,
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
        Créer une URL de checkout simple pour un paiement.
        Utilise la config DB si disponible, sinon les variables d'environnement.
        """
        try:
            # Résoudre la config : DB > settings
            config = None
            if etablissement is None:
                abonnement = eleve.abonnements.select_related('etablissement').filter(statut='actif').first()
                etablissement = abonnement.etablissement if abonnement else None
            if etablissement and hasattr(etablissement, 'config_fedapay'):
                try:
                    config = etablissement.config_fedapay
                except Exception:
                    pass

            if config:
                env = config.environnement
                public_key = config.cle_api_publique
            else:
                env = getattr(settings, 'FEDAPAY_ENVIRONMENT', 'sandbox')
                public_key = getattr(settings, 'FEDAPAY_PUBLIC_KEY', '')

            if not public_key:
                logger.error("Clé publique FedaPay non configurée.")
                return None

            base_url = "https://pay.fedapay.com" if env == 'production' else "https://pay.sandbox.fedapay.com"

            params = {
                'public_key': public_key,
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
