# 🚀 Render Deployment — Quick Start

**Temps estimé** : 30 minutes

## 📋 Checklist rapide

```
AVANT DÉPLOIEMENT
─────────────────────────────────────────
□ Comptes créés :
  □ Render.com (https://render.com)
  □ Groq (https://console.groq.com) - IA gratuite
  □ Cloudinary (https://cloudinary.com) - Stockage fichiers
  □ Resend (https://resend.com) - Emails gratuits
  □ FedaPay (https://app.fedapay.com) - Paiements

□ Fichiers présents :
  □ render.yaml ✓ (mis à jour)
  □ Procfile ✓ (mis à jour)
  □ render-build.sh ✓ (nouveau)
  □ .env.render ✓ (template)
  □ RENDER_DEPLOYMENT.md ✓ (doc complète)

□ Code pousé vers GitHub


DÉPLOIEMENT SUR RENDER
─────────────────────────────────────────
□ 1. Connecter GitHub à Render
□ 2. Créer Blueprint depuis render.yaml
□ 3. Configurer les variables d'environnement
□ 4. Déployer
□ 5. Vérifier les logs


POST-DÉPLOIEMENT
─────────────────────────────────────────
□ Tester /health/ endpoint
□ Accéder au panneau admin
□ Créer superuser
□ Configurer webhooks FedaPay
□ Tester un email
□ Vérifier les logs Celery
```

## ⚡ Démarrage rapide (5 minutes)

### 1️⃣ Préparer le code

```bash
# Depuis le répertoire du projet
git add render.yaml Procfile render-build.sh .env.render RENDER_DEPLOYMENT.md
git commit -m "feat: add Render deployment"
git push origin main
```

### 2️⃣ Créer un compte Render

1. Aller à https://render.com
2. S'inscrire avec GitHub
3. Autoriser l'accès au repository

### 3️⃣ Créer un Blueprint

1. Dashboard → "New" → "Blueprint"
2. Sélectionner `numerique-ia-composition`
3. Render détecte `render.yaml` automatiquement ✓

### 4️⃣ Configurer les clés API

Dans le formulaire Blueprint, ajouter les variables :

```
GROQ_API_KEY=gsk_XXXXX              (https://console.groq.com)
CLOUDINARY_URL=cloudinary://XXXXX   (https://cloudinary.com)
RESEND_API_KEY=re_XXXXX             (https://resend.com)
FEDAPAY_PUBLIC_KEY=pk_live_XXXXX    (https://app.fedapay.com)
FEDAPAY_SECRET_KEY=sk_live_XXXXX
FEDAPAY_WEBHOOK_SECRET=whsec_XXXXX
```

### 5️⃣ Déployer

Cliquer "Deploy Blueprint" et attendre ~5-10 minutes.

## 🔑 Clés API à obtenir

| Service | Lien | Temps |
|---------|------|-------|
| **Groq** | https://console.groq.com | 2 min |
| **Cloudinary** | https://cloudinary.com | 2 min |
| **Resend** | https://resend.com | 5 min (vérification domaine) |
| **FedaPay** | https://app.fedapay.com | 3 min |
| **NVIDIA OCR** | https://build.nvidia.com | 5 min |

**Total** : ~20 minutes

## 🧪 Tests post-déploiement

```bash
# Remplacer XXXXX par votre domaine Render
export URL="https://academie-numerique-web-XXXXX.onrender.com"

# 1. Health check
curl $URL/health/

# 2. Admin panel
curl -I $URL/admin/

# 3. Vérifier les migrations
curl $URL/api/v1/health/  # ou votre endpoint de santé

# 4. Vérifier les logs
# Dashboard → Service → Logs
```

## 🆘 Dépannage rapide

| Erreur | Solution |
|--------|----------|
| `Module 'daphne' not found` | `daphne` est dans requirements.txt, relancer la build |
| `DATABASE_URL not set` | Vérifier que PostgreSQL est créé et lié dans render.yaml |
| `REDIS_URL not set` | Vérifier que Redis est créé et lié dans render.yaml |
| `WebSocket not working` | S'assurer que Daphne est utilisé (pas Gunicorn) |
| `CORS origin not allowed` | Ajouter CORS_ALLOWED_ORIGINS dans Environment |

## 📊 Monitoring

```bash
# Voir les logs en temps réel
# Dashboard → Service → Logs

# Commandes via Render Shell
# Dashboard → Service → Shell
python manage.py migrate --list
celery -A academie_numerique inspect active
redis-cli ping
```

## 💰 Coûts estimés

| Service | Coût | Notes |
|---------|------|-------|
| **Render Web (Pro)** | $7/mois | Minimum recommandé |
| **Render Worker (Pro)** | $7/mois | Celery |
| **Render PostgreSQL** | $15/mois | Gratuit <90h/mois |
| **Render Redis** | $6/mois | Gratuit <100MB |
| **Groq API** | Gratuit | Jusqu'à 500k requests/mois |
| **Cloudinary** | Gratuit | 25GB stockage |
| **Resend** | Gratuit | 3000 emails/jour |
| **NVIDIA OCR** | Gratuit/payant | Selon usage |
| **FedaPay** | 1.5% | Frais transactions |
| **TOTAL** | ~$35/mois | Sans les clics/transactions |

## 📚 Documentation complète

Pour les détails complets, voir **RENDER_DEPLOYMENT.md**

## 🎓 À savoir

- **Render gratuit** : pas assez pour production (1 instance partagée)
- **Plan Pro** : recommandé pour une vraie école
- **Auto-deploy** : Render redéploie automatiquement à chaque push GitHub
- **Migrations** : Exécutées automatiquement via render-build.sh
- **WebSockets** : Daphne supporte nativement (pas Gunicorn)
- **Workers** : Celery + Redis pour les tâches asynchrones

## 📞 Besoin d'aide ?

- **Docs Render** : https://render.com/docs
- **Docs Django** : https://docs.djangoproject.com
- **Daphne Channels** : https://channels.readthedocs.io/
- **Celery** : https://docs.celeryproject.io/

---

**Prêt ?** Lance ton déploiement ! 🚀

```bash
./deploy-render.sh    # Sur Linux/Mac
.\deploy-render.ps1   # Sur Windows PowerShell
```
