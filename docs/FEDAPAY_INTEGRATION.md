# 💳 Intégration FedaPay - Guide Complet

Ce guide explique comment intégrer et utiliser le système de paiement FedaPay dans l'Académie Numérique.

---

## 🎯 Vue d'ensemble

Le système d'abonnement utilise **FedaPay** comme passerelle de paiement principale avec deux modes d'intégration :

1. **Checkout.js Embed** - Widget FedaPay intégré dans la page
2. **API REST + Webhook** - Pour les paiements programmatiques

---

## 📋 Prérequis

### 1. Compte FedaPay

1. Créer un compte sur [FedaPay](https://fedapay.com)
2. Vérifier votre compte (KYC)
3. Récupérer vos clés API :
   - **Clé publique** (pk_...) - pour le frontend
   - **Clé secrète** (sk_...) - pour le backend

### 2. Configuration Django

Ajouter dans `settings.py` :

```python
# URL du site pour les callbacks
SITE_URL = 'https://votre-domaine.com'  # En production
# SITE_URL = 'http://localhost:8000'     # En développement

# FedaPay configuration
FEDAPAY_WEBHOOK_SECRET = 'whsec_votre_secret'  # Générer un secret aléatoire
```

---

## 🚀 Configuration Initiale

### Étape 1 : Créer les plans de démo

```bash
python setup_abonnement_demo.py
```

Cela crée :
- 4 plans d'abonnement (Essentiel, Standard⭐, Premium, Famille)
- Configuration FedaPay en mode Sandbox
- Promotion de rentrée (RENTREE2024)

### Étape 2 : Configurer FedaPay dans l'Admin

1. Connectez-vous à l'admin Django : `/admin/`
2. Allez dans **Payments** > **Configurations FedaPay**
3. Cliquez sur la configuration de votre établissement
4. Remplissez les champs :
   - **Environnement** : `sandbox` (test) ou `production`
   - **Clé API publique** : `pk_...`
   - **Clé API secrète** : `sk_...`
   - **Nom du marchand** : Votre établissement
   - **Email du marchand** : contact@votre-ecole.bj
   - **Secret Webhook** : Générez un secret aléatoire

### Étape 3 : Configurer le Webhook FedaPay

Dans le dashboard FedaPay :

1. Allez dans **Développeurs** > **Webhooks**
2. Ajoutez une URL webhook :
   ```
   https://votre-domaine.com/payments/webhook/fedapay/
   ```
3. Sélectionnez les événements :
   - ✅ `transaction.approved`
   - ✅ `transaction.declined`
   - ✅ `transaction.canceled`
   - ✅ `transaction.refunded`

---

## 💳 Utilisation du Système

### Pour les Élèves

#### 1. Voir les plans d'abonnement
```
GET /payments/abonnements/
```

Page avec :
- Carrousel des plans
- Toggle mensuel/annuel
- Code promo
- FAQ

#### 2. Choisir un plan et payer
```
GET /payments/checkout-fedapay/?plan=standard&type=annuel&code=RENTREE2024
```

Processus :
1. Sélection du plan
2. Choix mensuel/annuel
3. Application code promo (optionnel)
4. Paiement via FedaPay Checkout.js
5. Confirmation automatique
6. Réception du reçu par email

#### 3. Voir ses abonnements
```
GET /payments/mes-abonnements/
```

### Pour les Administrateurs

#### Configuration des plans
```
GET /payments/admin/plans-abonnement/
```

Options configurables :
- Nom, slug, icône
- Prix mensuel/annuel
- Réduction annuelle (%)
- Features incluses
- Limitations
- Couleur, mise en avant
- Badge "Populaire", "Recommandé"

#### Configuration FedaPay
```
GET /payments/admin/config-fedapay/
```

---

## 🔧 Intégration Technique

### Checkout.js Embed

Le template `fedapay_checkout_embed.html` utilise :

```html
<script src="https://cdn.fedapay.com/checkout.js?v=1.1.7"></script>

<script>
FedaPay.init({
    public_key: 'pk_votre_cle_publique',
    transaction: {
        amount: 96000,  // Montant en FCFA
        description: 'Abonnement Standard - Académie Numérique'
    },
    customer: {
        email: 'eleve@email.com',
        firstname: 'Jean',
        lastname: 'Dupont',
        phone_number: {
            number: '0123456789',
            country: 'BJ'
        }
    },
    container: '#fedapay-container',  // ID du conteneur
    ui: {
        theme: 'light',
        language: 'fr'
    },
    onComplete: function(transaction) {
        // Paiement réussi
        handlePaymentSuccess(transaction);
    },
    onError: function(error) {
        // Erreur de paiement
        console.error(error);
    }
});
</script>
```

### API Backend

#### 1. Initier un paiement
```http
POST /payments/api/initier-paiement/
Content-Type: application/json

{
    "plan_id": "uuid-du-plan",
    "type": "annuel",  // ou "mensuel"
    "code_promo": "RENTREE2024",
    "telephone": "0123456789"
}
```

Réponse :
```json
{
    "success": true,
    "paiement_id": "uuid-paiement",
    "task_id": "redis-task-id",
    "message": "Paiement initié"
}
```

#### 2. Confirmer un paiement (après succès FedaPay)
```http
POST /payments/api/confirmer-paiement/
Content-Type: application/json

{
    "transaction_id": "txn_fedapay_123",
    "reference": "ABN-2024-123456",
    "abonnement_id": "uuid-abonnement",
    "montant": 96000
}
```

#### 3. Webhook FedaPay
```http
POST /payments/webhook/fedapay/
X-FedaPay-Signature: signature_hmac

{
    "event": "transaction.approved",
    "data": {
        "id": "txn_fedapay_123",
        "status": "approved",
        "amount": {"total": 96000, "currency": "XOF"}
    }
}
```

---

## 📊 Flux de Paiement Complet

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   ÉLÈVE     │────▶│ PAGE PLANS   │────▶│   CHOIX     │
│             │     │  (Slider)    │     │   PLAN      │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                  │
                       ┌──────────────────────────┘
                       ▼
              ┌─────────────────┐
              │ CHECKOUT-FEDAPAY │
              │  (Checkout.js)   │
              │                 │
              │ • Résumé plan   │
              │ • FedaPay embed │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  FEDAPAY WIDGET │
              │                 │
              │ • Mobile Money  │
              │ • Carte         │
              │ • Virement      │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ APPROVED│   │DECLINED │   │CANCELED │
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ACTIVATION│   │  ERROR  │   │  RETRY  │
    │ABONNEMENT│   │ MESSAGE │   │  PAGE   │
    │  + MAIL │   │         │   │         │
    └─────────┘   └─────────┘   └─────────┘
```

---

## 🎨 Personnalisation

### Modifier les couleurs des plans

Dans l'admin Django, pour chaque plan :
- **Couleur** : Code HEX (ex: `#3b82f6` pour bleu)
- **Icône** : Emoji (ex: `🎓`, `⭐`, `🚀`)

### Modifier les images publicitaires

1. Placez vos images dans `static/images/abonnements/`
2. Formats recommandés :
   - `hero-bg.jpg` : 1920x1080px (fond hero)
   - `promo-student.png` : 600x800px (étudiant promo)

### Modifier les emails

Templates disponibles :
- `email_rappel_renouvellement.html` (7 jours)
- `email_rappel_urgent.html` (3 jours)
- `email_rappel_dernier_jour.html` (1 jour)
- `email_recu_abonnement.html` (confirmation)

---

## 🔒 Sécurité

### Bonnes pratiques

1. **Toujours utiliser HTTPS** en production
2. **Vérifier la signature** des webhooks FedaPay
3. **Ne jamais exposer** la clé secrète (sk_) dans le frontend
4. **Utiliser uniquement** la clé publique (pk_) dans le frontend
5. **Valider les montants** côté serveur

### Vérification Webhook

```python
import hmac
import hashlib

def verifier_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## 🧪 Tests

### Mode Sandbox

En mode Sandbox, utilisez ces cartes de test :

| Numéro | Résultat |
|--------|----------|
| `4111111111111111` | Paiement accepté |
| `4000000000000002` | Paiement refusé |

Pour Mobile Money en test, utilisez n'importe quel numéro valide.

### Scénarios de test

1. **Paiement réussi** :
   ```bash
   curl -X POST /payments/api/initier-paiement/ \
        -d '{"plan_id": "...", "type": "mensuel"}'
   ```

2. **Code promo invalide** :
   ```bash
   curl -X POST /payments/api/initier-paiement/ \
        -d '{"plan_id": "...", "code_promo": "INVALID"}'
   ```

3. **Webhook test** :
   ```bash
   curl -X POST /payments/webhook/fedapay/ \
        -H "X-FedaPay-Signature: ..." \
        -d '{"event": "transaction.approved", "data": {...}}'
   ```

---

## 📞 Support

### Ressources FedaPay

- Documentation : https://docs.fedapay.com
- Support : support@fedapay.com
- Dashboard : https://dashboard.fedapay.com

### Contact Académie Numérique

- Email : support@academie-numerique.bj
- WhatsApp : +229 01 23 45 67 89

---

## 📝 Changelog

### Version 1.0
- ✅ Intégration FedaPay Checkout.js
- ✅ Système d'abonnement mensuel/annuel
- ✅ Codes promo
- ✅ Webhook pour notifications
- ✅ Reçus PDF automatiques
- ✅ Emails de rappel (7j, 3j, 1j)

---

## 🎓 Exemple Complet

```python
# views.py
from payments.fedapay_service import FedaPayService

# Créer un paiement
def creer_paiement(request):
    service = FedaPayService(etablissement)
    
    # Créer customer
    customer_id = service.creer_customer(eleve)
    
    # Créer transaction
    result = service.creer_transaction(
        paiement=paiement_obj,
        customer_id=customer_id,
        callback_url='https://site.com/callback/'
    )
    
    return JsonResponse({
        'payment_url': result['payment_url']
    })
```

```javascript
// JavaScript frontend
FedaPay.init({
    public_key: 'pk_sandbox_...',
    transaction: {
        amount: 96000,
        description: 'Abonnement Standard'
    },
    customer: {
        email: 'eleve@email.com',
        lastname: 'Dupont'
    },
    onComplete: function(txn) {
        // Redirection après succès
        window.location = '/payments/paiement/succes/';
    }
});
```

---

**💳 Système FedaPay prêt à l'emploi !** 🚀
