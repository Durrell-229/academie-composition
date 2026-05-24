# Déploiement Académie Numérique sur Render.com

Guide complet pour déployer le projet sur Render avec production-ready configuration.

## 🎯 Aperçu de l'architecture

```
┌─────────────────────────────────────────────────────┐
│         ACADÉMIE NUMÉRIQUE SUR RENDER               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Web (Daphne) ──┐                                  │
│                 ├─→ PostgreSQL (Pro)                │
│  Celery Worker ─┤                                  │
│                 ├─→ Redis (Pro)                     │
│  Celery Beat ──┘                                   │
│                                                     │
│  Cloudinary (stockage) ←───────────────────────    │
│  Resend (emails) ←──────────────────────────       │
│  FedaPay (paiements) ←──────────────────────       │
│  Groq/Gemini (IA) ←────────────────────────        │
│  NVIDIA OCR ←──────────────────────────────        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 📋 Prérequis

1. **Compte Render** : https://render.com
2. **Repository GitHub** avec ce code
3. **Services externes configurés** :
   - Cloudinary (stockage fichiers)
   - Resend (emails)
   - FedaPay (paiements)
   - Groq/Gemini (IA)
   - NVIDIA API (OCR)

## 🚀 Étape 1 : Préparer le repository

### 1.1 Ajouter les fichiers de déploiement

```bash
git add render.yaml Procfile render-build.sh RENDER_DEPLOYMENT.md
git commit -m "feat: add Render deployment configuration"
git push origin main
```

### 1.2 Vérifier la structure

```bash
# Vérifier que tous les fichiers sont présents
ls -la render.yaml Procfile render-build.sh
# Vérifier que render.yaml est valide
cat render.yaml
```

## 🔧 Étape 2 : Configuration sur Render

### 2.1 Créer un nouveau service depuis YAML

1. Aller sur https://render.com/dashboard
2. Cliquer sur **"New" → "Web Service"**
3. Choisir **"Deploy an existing repository from GitHub"**
4. Connecter le repository `numerique-ia-composition`
5. Dans les paramètres du service :
   - **Name** : `academie-numerique-web`
   - **Region** : Frankfurt
   - **Branch** : `main`
   - **Build Command** : Laissez vide (utilisé depuis render.yaml)
   - **Start Command** : Laissez vide (utilisé depuis render.yaml)

### 2.2 Ajouter le fichier render.yaml

Au lieu de configurer via l'UI, Render peut lire `render.yaml` :

```bash
# Dans le dashboard Render:
# 1. "Dashboard" → "Blueprint"
# 2. "New Blueprint"
# 3. Sélectionner le repository
# 4. Render détecte automatiquement render.yaml
# 5. Review et déployer
```

**OU** configurer manuellement chaque service :

### 2.3 Configurer les services manuellement

#### Service Web (`academie-numerique-web`)

1. **Créer le service** :
   - Type : Web Service
   - Repository : `numerique-ia-composition`
   - Build Command : `bash render-build.sh`
   - Start Command : `daphne -b 0.0.0.0 -p 10000 academie_numerique.asgi:application`

2. **Plan** : Pro minimum (free n'a pas assez de ressources)

3. **Environment Variables** : (voir section Étape 3)

#### Service Worker (`academie-celery-worker`)

1. **Créer le service** :
   - Type : Worker Service
   - Repository : `numerique-ia-composition`
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `celery -A academie_numerique worker -l info --concurrency=4`

#### Service Beat (`academie-celery-beat`)

1. **Créer le service** :
   - Type : Worker Service
   - Repository : `numerique-ia-composition`
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `celery -A academie_numerique beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

#### Redis

1. **Créer le service** :
   - Type : Redis
   - Name : `academie-redis`
   - Plan : Pro

#### PostgreSQL

1. **Créer la base de données** :
   - Type : PostgreSQL
   - Name : `academie-db`
   - Database Name : `academie_numerique`
   - User : `academie_user`
   - Plan : Pro

## 🔐 Étape 3 : Variables d'environnement

### 3.1 Variables critiques (à configurer dans Render)

Dans le dashboard Render de chaque service, ajouter ces variables :

```
# ─── DJANGO ───────────────────────────
DJANGO_SECRET_KEY=<auto-generate dans Render UI>
DEBUG=False
ALLOWED_HOSTS=<votre-domaine>.onrender.com

# ─── BASE DE DONNÉES ──────────────────
DB_ENGINE=postgresql
DATABASE_URL=<auto-lié à la base de données>

# ─── REDIS ────────────────────────────
REDIS_URL=<auto-lié au service Redis>

# ─── IA PROVIDERS (obtenir les clés) ──
AI_PROVIDER=groq
GROQ_API_KEY=gsk_XXXXX  # https://console.groq.com
GEMINI_API_KEY=         # https://aistudio.google.com
MISTRAL_API_KEY=        # https://console.mistral.ai
NVIDIA_API_KEY=         # https://build.nvidia.com/

# ─── EMAIL (Resend) ───────────────────
RESEND_API_KEY=re_XXXXX  # https://resend.com/api-keys
DEFAULT_FROM_EMAIL=Académie Numérique <noreply@academie.com>

# ─── PAIEMENTS (FedaPay) ──────────────
FEDAPAY_ENVIRONMENT=production
FEDAPAY_PUBLIC_KEY=pk_live_XXXXX      # https://app.fedapay.com
FEDAPAY_SECRET_KEY=fedapay_live_XXXXX
FEDAPAY_WEBHOOK_SECRET=whsec_XXXXX

# ─── STOCKAGE (Cloudinary) ────────────
USE_CLOUDINARY_STORAGE=True
CLOUDINARY_URL=cloudinary://XXXXX     # https://cloudinary.com

# ─── RÔLES ────────────────────────────
ROLE_PASSWORD_ADMIN=<mot-de-passe-fort>
ROLE_PASSWORD_CP=<mot-de-passe-fort>
ROLE_PASSWORD_PROF=<mot-de-passe-fort>

# ─── PRIX ─────────────────────────────
PRIX_CORRECTION_UNITAIRE=500  # en XOF

# ─── DOMAINE ──────────────────────────
SITE_URL=https://<votre-domaine>.onrender.com
CORS_ALLOWED_ORIGINS=https://<votre-domaine>.onrender.com

# ─── SÉCURITÉ ─────────────────────────
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 3.2 Obtenir les clés API

| Service | URL | Instruction |
|---------|-----|------------|
| **Groq** | https://console.groq.com | Créer compte → API Keys → Copy |
| **Gemini** | https://aistudio.google.com | Créer compte → Get API Key |
| **Mistral** | https://console.mistral.ai | Créer compte → API Keys |
| **NVIDIA** | https://build.nvidia.com | Créer compte → API Keys |
| **Resend** | https://resend.com | Créer compte → API Keys |
| **FedaPay** | https://app.fedapay.com | Créer compte → Settings → API Keys |
| **Cloudinary** | https://cloudinary.com | Créer compte → Dashboard → Copy CLOUDINARY_URL |

## ✅ Étape 4 : Migrations et données initiales

Après le déploiement, exécuter les commandes d'initialisation :

```bash
# Option 1 : Via Render Shell
# 1. Aller à "Dashboard" → Service → "Shell"
# 2. Exécuter :
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata roles_fixtures  # si vous avez des fixtures

# Option 2 : Via le build script
# Ajouter à render.yaml buildCommand :
# ... && python manage.py createsuperuser --noinput --username admin --email admin@example.com
```

## 🔗 Étape 5 : Domaine personnalisé (optionnel)

1. Aller à **Service Settings** → **Custom Domain**
2. Ajouter votre domaine (ex: `academie-numerique.com`)
3. Suivre les instructions DNS chez votre registraire

## 🧪 Étape 6 : Tests post-déploiement

Après le déploiement, tester :

```bash
# 1. Health check
curl https://<votre-app>.onrender.com/health/

# 2. Admin panel
https://<votre-app>.onrender.com/admin/

# 3. Vérifier les logs
# Dashboard → Service → Logs

# 4. Tester les webhooks FedaPay
# https://docs.fedapay.com/webhooks

# 5. Tester les emails (Resend)
# Envoyer un email de test via Django
```

## 🔍 Dépannage courant

### Erreur : "DJANGO_SECRET_KEY not set"

```
Solution : Render doit générer automatiquement avec generateValue: true
Si absent : Dashboard → Environment → DJANGO_SECRET_KEY → Generate
```

### Erreur : "No module named 'daphne'"

```
Solution : daphne est dans requirements.txt (channels==4.0.0)
Vérifier que la dernière version est installée
```

### Erreur : "CORS origin not allowed"

```
Solution : Ajouter CORS_ALLOWED_ORIGINS dans Environment
CORS_ALLOWED_ORIGINS=https://<votre-domaine>.onrender.com
```

### Erreur : "Database connection failed"

```
Solution : Vérifier que DATABASE_URL est lié à la base de données
Dashboard → Database → Connection String → Copy
Coller dans SERVICE Environment → DATABASE_URL
```

### WebSocket non fonctionnel

```
Solution : S'assurer que Daphne est utilisé (pas Gunicorn)
startCommand : daphne -b 0.0.0.0 -p 10000 academie_numerique.asgi:application
```

## 📊 Monitoring

Render fournit :
- **Logs** : Service → Logs (en temps réel)
- **Metrics** : Service → Metrics (CPU, RAM, requêtes)
- **Alerts** : Service → Alerts (configurer des alertes)

### Commandes utiles via Render Shell

```bash
# Vérifier la base de données
python manage.py dbshell
\dt  # lister les tables PostgreSQL

# Vérifier Redis
redis-cli ping

# Vérifier Celery
celery -A academie_numerique inspect active

# Vérifier les migrations
python manage.py showmigrations

# Nettoyer les sessions expirées
python manage.py clearsessions
```

## 🔄 Mise à jour du code

```bash
# 1. Push les changements
git add .
git commit -m "Update code"
git push origin main

# 2. Render redéploie automatiquement
# 3. Migrations s'exécutent automatiquement (render-build.sh)
# 4. Service redémarre

# 5. Vérifier les logs
# Dashboard → Service → Logs
```

## 💾 Sauvegarde et restauration

```bash
# Via Render Shell
# Exporter la base de données
pg_dump $DATABASE_URL > backup.sql

# Importer depuis backup
psql $DATABASE_URL < backup.sql

# Exporter les fichiers Cloudinary
# (Cloudinary gère les backups automatiquement)
```

## 📝 Checklist de déploiement

- [ ] Repository GitHub avec tous les fichiers
- [ ] `render.yaml`, `Procfile`, `render-build.sh` présents
- [ ] `requirements.txt` à jour
- [ ] `settings.py` compatible Render (ALLOWED_HOSTS, etc.)
- [ ] Variables d'environnement configurées
- [ ] Services créés (Web, Worker, Beat, Redis, PostgreSQL)
- [ ] Bases de données reliées correctement
- [ ] Migrations exécutées
- [ ] Utilisateur admin créé
- [ ] Domaine personnalisé configuré (optionnel)
- [ ] Tests post-déploiement réussis
- [ ] Monitoring activé

## 🆘 Support

- **Render Docs** : https://render.com/docs
- **Django Docs** : https://docs.djangoproject.com
- **Daphne Docs** : https://channels.readthedocs.io/en/latest/
- **Celery Docs** : https://docs.celeryproject.io

## 📧 Configuration d'un webhook Render

Pour redéployer automatiquement sur push GitHub :

1. Dashboard → Service → Settings
2. Auto-deploy → On
3. Render écoute automatiquement les changements sur la branche `main`

---

**Dernière mise à jour** : 2026-05-24
**Version** : 1.0
**Maintenance** : Durell-229
