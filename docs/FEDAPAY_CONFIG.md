# 🔐 Configuration FedaPay - Clé API Intégrée

## ✅ Clé API Publique Enregistrée

**Votre clé** : `pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0`

⚠️ **C'est une clé LIVE** - Les paiements seront réels !

---

## 🚀 Configuration Rapide

### Option 1 : Script Automatique (Recommandé)

```bash
# Exécuter le script de configuration
python setup_fedapay_live.py
```

Ce script va :
1. Configurer la clé publique automatiquement
2. Vous demander la clé secrète (sk_live_...)
3. Créer un fichier .env.exemple

### Option 2 : Configuration Manuelle

#### Étape 1 : Exécuter le setup des démos
```bash
python setup_abonnement_demo.py
```

La clé publique sera automatiquement intégrée.

#### Étape 2 : Ajouter la clé secrète dans l'Admin

1. Connectez-vous à l'admin : `/admin/`
2. Allez dans **Payments** > **Configurations FedaPay**
3. Cliquez sur la configuration de votre établissement
4. Dans le champ **"Clé API secrète"**, entrez :
   ```
   sk_live_VOTRE_CLE_SECRETE
   ```
5. Sauvegardez

---

## 🔑 Informations sur les Clés

### Clé Publique (PK) ✅ Déjà Configurée
```
pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0
```
- ✅ Visible côté client (frontend)
- ✅ Utilisée dans le widget FedaPay
- ✅ Ne permet que de créer des transactions

### Clé Secrète (SK) ⚠️ À Configurer
```
sk_live_...
```
- ⚠️ **DOIT RESTER CONFIDENTIELLE**
- ⚠️ Ne jamais exposer dans le frontend
- ⚠️ Permet de valider les paiements
- 🔒 À configurer uniquement dans l'admin Django

---

## 🌐 Configuration Webhook Obligatoire

Dans le Dashboard FedaPay (https://dashboard.fedapay.com) :

1. Allez dans **Développeurs** > **Webhooks**
2. Cliquez **"Ajouter un webhook"**
3. URL du webhook :
   ```
   https://votre-domaine.com/payments/webhook/fedapay/
   ```
4. Événements à sélectionner :
   - ✅ `transaction.approved`
   - ✅ `transaction.declined`
   - ✅ `transaction.canceled`
5. Sauvegardez

---

## 🧪 Test de Paiement

### Avant de tester :
1. ✅ Clé publique configurée
2. ✅ Clé secrète ajoutée dans l'admin
3. ✅ Webhook configuré dans FedaPay
4. ✅ HTTPS activé sur votre domaine

### Tester un paiement :
```
1. Allez sur : /payments/abonnements/
2. Choisissez un plan (Essentiel, Standard, etc.)
3. Cliquez sur "Choisir"
4. Paiement avec Mobile Money ou Carte
5. Vérifiez la confirmation
```

---

## ⚠️ Points d'Attention

### En Mode LIVE :
- 💸 Les paiements sont **RÉELS**
- 🏦 L'argent va sur votre compte FedaPay
- 📧 Les clients reçoivent de vrais reçus
- ⚡ Ne faites pas de tests avec de gros montants

### Sécurité :
```
✅ HTTPS obligatoire
✅ Ne jamais exposer sk_live_ dans le code
✅ Vérifier les signatures des webhooks
✅ Limiter les IPs autorisées (optionnel)
```

---

## 📞 Support

### Problèmes courants :

**"Clé API invalide"**
→ Vérifiez que la clé est complète et sans espaces

**"Paiement refusé"**
→ Vérifiez que votre compte FedaPay est vérifié (KYC)

**"Webhook non reçu"**
→ Vérifiez l'URL et que votre site est accessible

### Contact FedaPay :
- Support : support@fedapay.com
- Documentation : https://docs.fedapay.com

---

## ✅ Checklist Pré-Lancement

- [ ] Clé publique configurée (✅ déjà fait)
- [ ] Clé secrète ajoutée dans l'admin
- [ ] Webhook configuré dans FedaPay Dashboard
- [ ] HTTPS actif sur le domaine
- [ ] Test de paiement réussi (petit montant)
- [ ] Email de reçu reçu
- [ ] Abonnement activé automatiquement

---

## 🎉 Vous êtes prêt !

Votre système de paiement FedaPay est configuré avec votre clé LIVE.

**URL de test** : `/payments/abonnements/`

Bonne chance ! 🚀💳
