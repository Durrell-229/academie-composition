# 🔐 Guide Complet — Configurer les variables Render

## ⚠️ IMPORTANT — LIRE D'ABORD

Le nouveau `render.yaml` contient **TOUTES** les 50+ variables d'environnement.

Quand tu crées le Blueprint, tu verras UNE SEULE PAGE avec TOUS les champs à remplir.

---

## 📋 Variables à configurer dans Render Dashboard

Copie-colle exactement ces valeurs dans les champs correspondants :

### 1️⃣ **DJANGO** (Configuration de base)

```
DJANGO_SECRET_KEY: [AUTO-GÉNÉRÉ — Ne rien entrer, Render le fait]
DEBUG: False
ALLOWED_HOSTS: *.onrender.com,votre-domaine.com
RENDER_EXTERNAL_HOSTNAME: [AUTO — Ne rien entrer]
SITE_URL: https://academie-numerique.onrender.com
```

### 2️⃣ **BASE DE DONNÉES** (Auto-lié)

```
DB_ENGINE: postgresql
DATABASE_URL: [AUTO-LIÉ — Ne rien entrer]
```

### 3️⃣ **REDIS** (Auto-lié)

```
REDIS_URL: [AUTO-LIÉ — Ne rien entrer]
CHANNEL_LAYERS_REDIS: [AUTO-LIÉ — Ne rien entrer]
```

### 4️⃣ **IA PROVIDERS** ⭐ À REMPLIR

```
AI_PROVIDER: groq

GROQ_API_KEY: [COPIE DE https://console.groq.com/keys]
              Commence par "gsk_"

GEMINI_API_KEY: [OPTIONNEL - https://aistudio.google.com/app/apikey]
                Commence par "AIza"

MISTRAL_API_KEY: [OPTIONNEL - https://console.mistral.ai/api-keys]
                 Commence par "sn_"

DEEPSEEK_API_KEY: [OPTIONNEL - https://platform.deepseek.com/api-keys]
                  Commence par "sk_"
```

### 5️⃣ **NVIDIA OCR** ⭐ À REMPLIR

```
NVIDIA_API_KEY: [COPIE DE https://build.nvidia.com/discover/api-catalog]
                Commence par "nvapi-"
                OUI, C'EST ICI QUE TU ENTRES TA CLÉ NVIDIA!

NVIDIA_API_BASE_URL: https://integrate.api.nvidia.com/v1
NVIDIA_MODEL: nvidia/nemotron-4-340b-instruct
```

### 6️⃣ **EMAIL (Resend)** ⭐ À REMPLIR

```
RESEND_API_KEY: [COPIE DE https://resend.com/api-keys]
                Commence par "re_"

DEFAULT_FROM_EMAIL: Académie Numérique <noreply@academie-numerique.com>
```

### 7️⃣ **PAIEMENTS (FedaPay)** ⭐ À REMPLIR

```
FEDAPAY_ENVIRONMENT: production

FEDAPAY_PUBLIC_KEY: [COPIE DE https://app.fedapay.com/settings/api-keys]
                    Mode LIVE! (pk_live_xxx, PAS pk_sandbox_xxx)

FEDAPAY_SECRET_KEY: [COPIE DE https://app.fedapay.com/settings/api-keys]
                    Mode LIVE! (sk_live_xxx, PAS sk_sandbox_xxx)

FEDAPAY_WEBHOOK_SECRET: [GÉNÉRÉ SUR https://app.fedapay.com/webhooks]

PRIX_CORRECTION_UNITAIRE: 500
```

### 8️⃣ **STOCKAGE FICHIERS (Cloudinary)** ⭐ À REMPLIR

```
USE_CLOUDINARY_STORAGE: True

CLOUDINARY_URL: [COPIE COMPLÈTE DE https://cloudinary.com/console/settings/api-keys]
                Format: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

### 9️⃣ **MOTS DE PASSE DES RÔLES** ⭐ À REMPLIR

```
ROLE_PASSWORD_ADMIN: [INVENTE UN MOT DE PASSE FORT - min 12 caractères]
ROLE_PASSWORD_CP: [INVENTE UN MOT DE PASSE FORT - min 12 caractères]
ROLE_PASSWORD_PROF: [INVENTE UN MOT DE PASSE FORT - min 12 caractères]
```

**Exemple** : `Admin@2025!Secure` `CP#2025Secure123` `Prof@Secure2025!`

### 🔟 **CORS** (Configuration d'accès)

```
CORS_ALLOW_ALL_ORIGINS: False
CORS_ALLOWED_ORIGINS: https://academie-numerique.onrender.com
CORS_ALLOW_CREDENTIALS: True
```

### 1️⃣1️⃣ **SÉCURITÉ HTTPS** (Production)

```
SECURE_SSL_REDIRECT: True
SESSION_COOKIE_SECURE: True
CSRF_COOKIE_SECURE: True
SECURE_HSTS_SECONDS: 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS: True
SECURE_HSTS_PRELOAD: True
```

### 1️⃣2️⃣ **SESSIONS & COOKIES**

```
SESSION_COOKIE_AGE: 604800
SESSION_COOKIE_HTTPONLY: True
```

### 1️⃣3️⃣ **LOGGING**

```
LOG_LEVEL: info
```

---

## 🚀 ÉTAPES DANS RENDER DASHBOARD

### Étape 1 : Aller à Render.com

https://render.com/dashboard

### Étape 2 : Créer Blueprint

```
1. Cliquer "New"
2. Sélectionner "Blueprint"
3. Connecter GitHub (si pas encore fait)
4. Sélectionner repository "academie-composition"
```

### Étape 3 : Render va détecter render.yaml

Tu verras une liste de services :
- ✓ Web service (academie-numerique-web)
- ✓ Background worker (academie-celery-worker)
- ✓ Background worker (academie-celery-beat)
- ✓ Redis
- ✓ PostgreSQL

### Étape 4 : Choisir l'option

Si tu vois le message :
```
We found existing services that match this Blueprint, 
but those services are already associated with an existing Blueprint instance
```

**Sélectionne** : "Create all as new services"

### Étape 5 : Remplir les variables d'environnement

Tu verras une LONGUE liste avec des champs vides pour chaque variable.

**REMPLIS DANS CET ORDRE** :

1. **Laisser vide** (Auto-généré) :
   - DJANGO_SECRET_KEY
   - DATABASE_URL
   - REDIS_URL
   - CHANNEL_LAYERS_REDIS
   - RENDER_EXTERNAL_HOSTNAME

2. **Copier mes valeurs** (de ce guide) :
   - DEBUG: `False`
   - ALLOWED_HOSTS: `*.onrender.com`
   - AI_PROVIDER: `groq`
   - LOG_LEVEL: `info`
   - Etc...

3. **ENTRER TES CLÉS API** (tes vrais secrets) :
   - `GROQ_API_KEY`: Ta clé Groq
   - `NVIDIA_API_KEY`: Ta clé NVIDIA ← C'EST ICI!
   - `RESEND_API_KEY`: Ta clé Resend
   - `CLOUDINARY_URL`: Ton URL Cloudinary
   - `FEDAPAY_PUBLIC_KEY`: Ta clé publique FedaPay
   - `FEDAPAY_SECRET_KEY`: Ta clé secrète FedaPay
   - `FEDAPAY_WEBHOOK_SECRET`: Ton secret webhook
   - Etc...

### Étape 6 : Vérifier

Avant de déployer, vérif que :
```
☑ Groq API Key entré
☑ NVIDIA API Key entré
☑ Cloudinary URL entré
☑ FedaPay clés entrées
☑ Resend API Key entrée
☑ Mots de passe des rôles définis
☑ DEBUG = False
☑ AI_PROVIDER = groq
```

### Étape 7 : Deploy!

Cliquer "Deploy Blueprint"

Attendre ~10-15 minutes pour que tout se configure.

---

## 🔍 Où trouver les clés API

| Clé | URL | Temps |
|-----|-----|-------|
| **GROQ_API_KEY** | https://console.groq.com/keys | 2 min |
| **NVIDIA_API_KEY** | https://build.nvidia.com | 5 min |
| **RESEND_API_KEY** | https://resend.com/api-keys | 3 min |
| **CLOUDINARY_URL** | https://cloudinary.com/console/settings/api-keys | 2 min |
| **FEDAPAY** | https://app.fedapay.com/settings/api-keys | 5 min |

**Temps total** : ~20 minutes pour obtenir toutes les clés

---

## ✅ Checklist finale

Avant de cliquer "Deploy":

- [ ] GROQ_API_KEY ≠ vide
- [ ] NVIDIA_API_KEY ≠ vide
- [ ] CLOUDINARY_URL ≠ vide
- [ ] RESEND_API_KEY ≠ vide
- [ ] FEDAPAY_PUBLIC_KEY ≠ vide
- [ ] FEDAPAY_SECRET_KEY ≠ vide
- [ ] FEDAPAY_WEBHOOK_SECRET ≠ vide
- [ ] ROLE_PASSWORD_ADMIN ≠ vide
- [ ] ROLE_PASSWORD_CP ≠ vide
- [ ] ROLE_PASSWORD_PROF ≠ vide
- [ ] DEBUG = False (IMPORTANT!)
- [ ] ALLOWED_HOSTS = *.onrender.com

---

## 🐛 Si tu trouves pas un champ

**Cherche dans la liste** en utilisant `Ctrl+F` (Windows) ou `Cmd+F` (Mac) :

```
Ctrl+F "NVIDIA" → Trouvera NVIDIA_API_KEY
Ctrl+F "GROQ" → Trouvera GROQ_API_KEY
Ctrl+F "RESEND" → Trouvera RESEND_API_KEY
Ctrl+F "CLOUDINARY" → Trouvera CLOUDINARY_URL
Ctrl+F "FEDAPAY" → Trouvera toutes les clés FedaPay
```

---

## 📊 Résumé

```
Total variables:     50+
Variables à laisser vides:  5 (Auto-générées/liées)
Variables à remplir:  45
Temps estimé:        30 minutes
Facilité:            ⭐⭐⭐⭐ Facile (copier-coller)
```

---

**Prêt ?** Lance le Blueprint et remplis les variables! 🚀

Dernière mise à jour : 2026-05-24
