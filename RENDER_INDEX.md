# 📑 Index Déploiement Render — Guide de navigation

Tous les fichiers nécessaires pour déployer votre projet Django sur Render.com

---

## 🚀 Commencer ici

### Pour impatients (5 minutes)
1. Lire : **RENDER_QUICKSTART.md** ← START HERE
2. Obtenir clés API (voir liste dans QUICKSTART)
3. Lancer : `./deploy-render.sh` ou `.\deploy-render.ps1`
4. Pousser GitHub et déployer sur Render

### Pour complets (30 minutes)
1. Lire : **RENDER_DEPLOYMENT.md** (doc complète)
2. Completer : **PRE_DEPLOYMENT_CHECKLIST.md**
3. Configurer : variables d'environnement (voir .env.render)
4. Déployer : suivre les étapes 1-6 de DEPLOYMENT.md

---

## 📂 Structure des fichiers

### 🔧 Configuration (4 fichiers)

| Fichier | Description | Utilité |
|---------|-------------|---------|
| **render.yaml** | Configuration Blueprint pour Render | 📌 Clé - décrit tous les services |
| **Procfile** | Services (web, worker, beat) | Pour Heroku/Render |
| **render-build.sh** | Script de build automatisé | Exécuté par Render lors du build |
| **.env.render** | Template variables d'environnement | Guide pour configurer sur Render |

### 📖 Documentation (4 fichiers)

| Fichier | Contenu | Durée |
|---------|---------|-------|
| **RENDER_QUICKSTART.md** | Version 5 minutes - checklist + liens | ⚡ 5 min |
| **RENDER_DEPLOYMENT.md** | Guide complet 8 étapes + dépannage | 📚 30 min |
| **DEPLOYMENT_FILES_SUMMARY.md** | Résumé ce qui a été créé | 📋 5 min |
| **CELERY_REDIS_CONFIG.md** | Configuration avancée (optionnel) | 🔧 10 min |
| **PRE_DEPLOYMENT_CHECKLIST.md** | 100+ points à vérifier avant deployer | ✅ 15 min |

### 🤖 Scripts (2 fichiers)

| Fichier | OS | Fonction |
|---------|----|-----------
| **deploy-render.sh** | Linux/Mac | Vérification pré-déploiement + push GitHub |
| **deploy-render.ps1** | Windows | Même mais PowerShell |

### 📍 Ce fichier

| Fichier | Rôle |
|---------|------|
| **RENDER_INDEX.md** | Navigation et structure (vous êtes ici) |

---

## 🎯 Chemins par profil

### 👤 Développeur impatient
```
1. RENDER_QUICKSTART.md (5 min)
2. Obtenir clés API (20 min)
3. ./deploy-render.sh (2 min)
4. Render dashboard (10 min)
5. Tests (5 min)
Total : 42 minutes
```

### 👨‍💼 Chef projet / DevOps
```
1. RENDER_DEPLOYMENT.md (30 min)
2. CELERY_REDIS_CONFIG.md (10 min)
3. PRE_DEPLOYMENT_CHECKLIST.md (20 min)
4. Render configuration (30 min)
5. Tests + monitoring (20 min)
Total : 2 heures
```

### 🔍 Code reviewer / Audit
```
1. DEPLOYMENT_FILES_SUMMARY.md (5 min)
2. render.yaml (10 min)
3. PRE_DEPLOYMENT_CHECKLIST.md (15 min)
4. Vérifier requirements.txt (5 min)
Total : 35 minutes
```

---

## 📋 Checklist rapide

```bash
# 1. Vérifier les fichiers de déploiement
ls -la render.yaml Procfile render-build.sh .env.render

# 2. Exécuter la vérification
./deploy-render.sh          # Linux/Mac
.\deploy-render.ps1         # Windows

# 3. Pousser vers GitHub
git add render.yaml Procfile render-build.sh .env.render RENDER_*.md
git commit -m "feat: add Render deployment"
git push origin main

# 4. Sur Render.com
# - Nouveau Blueprint
# - Sélectionner repository
# - Configurer variables
# - Deploy
```

---

## 🔑 Variables d'environnement

Voir **[.env.render](.env.render)** pour la liste complète et les explications.

Résumé des clés requises :
```
DJANGO_SECRET_KEY          ← Auto-généré par Render
DATABASE_URL               ← Auto-lié PostgreSQL
REDIS_URL                  ← Auto-lié Redis
GROQ_API_KEY               ← Obtenir https://console.groq.com
CLOUDINARY_URL             ← Obtenir https://cloudinary.com
RESEND_API_KEY             ← Obtenir https://resend.com
FEDAPAY_PUBLIC_KEY         ← Obtenir https://app.fedapay.com
FEDAPAY_SECRET_KEY         ← Obtenir https://app.fedapay.com
```

---

## 🏗️ Architecture

```
GitHub Repository
    ├── render.yaml           ← Fichier principal
    ├── Procfile              ← Services
    ├── render-build.sh       ← Build script
    └── requirements.txt      ← Dépendances
    
                ↓
                
Render Dashboard
    ├── 5 services automatiquement créés
    │   ├── Web (Daphne) - interface utilisateur
    │   ├── Worker (Celery) - tâches async
    │   ├── Beat (Scheduler) - planification
    │   ├── Redis - cache/session
    │   └── PostgreSQL - données
    │
    └── 50+ variables d'environnement (manuelles)
```

---

## 📊 Services créés

| Service | Type | Plan | Coût |
|---------|------|------|------|
| academie-numerique-web | Web | Pro | $7/mois |
| academie-celery-worker | Worker | Pro | $7/mois |
| academie-celery-beat | Worker | Pro | $7/mois |
| academie-redis | Redis | Pro | $6/mois |
| academie-db | PostgreSQL | Pro | $15/mois |
| **Total Render** | | | **~$35/mois** |

Plus coûts externes (FedaPay, etc.) : 0-50/mois

---

## 🔗 Services externes

| Service | Gratuit | Lien | Notes |
|---------|---------|------|-------|
| Groq (IA) | ✓ | https://console.groq.com | 500k req/mois gratuit |
| Cloudinary | 25GB | https://cloudinary.com | Stockage fichiers |
| Resend | 3k/jour | https://resend.com | Emails |
| FedaPay | 1.5% | https://app.fedapay.com | Paiements Bénin |
| NVIDIA OCR | Gratuit | https://build.nvidia.com | Reconnaissance optique |

---

## 🧪 Tests

Voir **PRE_DEPLOYMENT_CHECKLIST.md** pour tests locaux.

Tests post-déploiement :
```bash
curl https://<your-app>.onrender.com/health/
curl https://<your-app>.onrender.com/admin/
```

---

## 🐛 Dépannage

Tableau comparatif des erreurs courantes :

| Erreur | Page concernée |
|--------|-----------------|
| "Module daphne not found" | DEPLOYMENT.md → Dépannage |
| "DATABASE_URL not set" | DEPLOYMENT.md → Étape 3 |
| "CORS origin not allowed" | DEPLOYMENT.md → Tests |
| "WebSocket not working" | CELERY_REDIS_CONFIG.md |
| "Health check failing" | PRE_DEPLOYMENT_CHECKLIST.md |

---

## 📞 Support

- **Render** : https://render.com/docs
- **Django** : https://docs.djangoproject.com
- **Daphne** : https://channels.readthedocs.io/
- **Celery** : https://docs.celeryproject.io/

---

## ✅ Avant de déployer

1. [ ] Lire le document approprié (QUICKSTART ou DEPLOYMENT)
2. [ ] Compléter PRE_DEPLOYMENT_CHECKLIST.md
3. [ ] Exécuter ./deploy-render.sh (ou .ps1)
4. [ ] Pousser vers GitHub
5. [ ] Créer Blueprint Render
6. [ ] Configurer variables
7. [ ] Déployer
8. [ ] Tester

---

## 📈 Statistiques des fichiers

| Fichier | Mots | Sections | Créé |
|---------|------|----------|------|
| RENDER_DEPLOYMENT.md | 2500+ | 8 | 2026-05-24 |
| PRE_DEPLOYMENT_CHECKLIST.md | 1000+ | 20 | 2026-05-24 |
| RENDER_QUICKSTART.md | 600+ | 8 | 2026-05-24 |
| CELERY_REDIS_CONFIG.md | 700+ | 12 | 2026-05-24 |
| render.yaml | 150+ | 5 services | 2026-05-24 |
| .env.render | 200+ | 13 sections | 2026-05-24 |

**Total documentation** : ~6000 mots

---

## 🎓 Ordre de lecture recommandé

```
1ère visite
├── RENDER_INDEX.md (ce fichier) ← Vous êtes ici
└── RENDER_QUICKSTART.md ← Ensuite

Pour plus de détails
├── RENDER_DEPLOYMENT.md (complet)
├── DEPLOYMENT_FILES_SUMMARY.md (ce qui a été créé)
└── PRE_DEPLOYMENT_CHECKLIST.md (avant de lancer)

Configuration avancée
├── CELERY_REDIS_CONFIG.md (si Celery)
├── render.yaml (lire la config)
└── .env.render (copier les vars)

Outils automatisés
├── deploy-render.sh (Linux/Mac)
└── deploy-render.ps1 (Windows)
```

---

## 🚀 Démarrage immédiat

```bash
# Étape 1 : Vérification
./deploy-render.sh  # ou .\deploy-render.ps1 sur Windows

# Étape 2 : Push
git push origin main

# Étape 3 : Render
# 1. https://render.com/dashboard
# 2. New → Blueprint
# 3. Sélectionner repo
# 4. Deploy

# Durée totale : ~15 minutes
```

---

**Status** : ✅ Prêt pour déploiement  
**Dernière mise à jour** : 2026-05-24  
**Maintenance** : Durell-229  
**Version** : 1.0

📖 **Commençons !** → Lire **RENDER_QUICKSTART.md**
