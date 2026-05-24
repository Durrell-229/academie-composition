# ✅ Checklist pré-déploiement Render

À compléter AVANT de pousser vers GitHub et Render.

## 📋 Code & Repository

### Configuration Django
- [ ] DEBUG = False en production (settings.py)
- [ ] ALLOWED_HOSTS configuré pour domaine Render
- [ ] SECRET_KEY sera généré par Render
- [ ] DATABASES utilise dj_database_url
- [ ] STATIC_ROOT = BASE_DIR / 'staticfiles'
- [ ] STATIC_URL = '/static/'
- [ ] WhiteNoise middleware présent
- [ ] CORS configuré pour les domaines autorisés

### Fichiers de déploiement
- [ ] `render.yaml` présent et valide
- [ ] `Procfile` présent et à jour
- [ ] `render-build.sh` exécutable
- [ ] `.env.render` (template, ne pas commiter)
- [ ] `RENDER_DEPLOYMENT.md` complet
- [ ] `RENDER_QUICKSTART.md` présent
- [ ] `CELERY_REDIS_CONFIG.md` si Celery utilisé

### Requirements.txt
- [ ] Django 5.2+ présent
- [ ] daphne ou channels présent
- [ ] psycopg2-binary présent (PostgreSQL)
- [ ] redis présent
- [ ] gunicorn présent (fallback)
- [ ] whitenoise présent
- [ ] cloudinary ou boto3 présent (stockage)
- [ ] celery présent si utilisé
- [ ] Pas de dépendances système (Windows paths, etc.)

### Git
- [ ] `.gitignore` exclude .env, *.pyc, __pycache__
- [ ] Branch main à jour
- [ ] Pas de credentials en dur dans le code
- [ ] Pas de fichiers volumineux (>100MB)
- [ ] History propre ou acceptable

## 🔐 Sécurité

### Credentials
- [ ] Pas de SECRET_KEY en dur
- [ ] Pas de API keys en dur
- [ ] Pas de passwords en dur
- [ ] Pas de .env local commité
- [ ] Pas de tokens d'accès
- [ ] .gitignore couvre tous les secrets

### Dépendances
- [ ] Pas de dépendances obsolètes
- [ ] Pas de vulnérabilités connues
  ```bash
  pip install safety
  safety check
  ```
- [ ] Versions compatibles les unes avec les autres
- [ ] Pas de conflits de versions

### Settings Django
- [ ] SECURE_SSL_REDIRECT = True
- [ ] SESSION_COOKIE_SECURE = True
- [ ] CSRF_COOKIE_SECURE = True
- [ ] SECURE_HSTS_SECONDS = 31536000
- [ ] ALLOWED_HOSTS restrictive
- [ ] DEBUG = False

## 🗄️ Base de données

### Migrations
- [ ] Pas de migrations en attente
  ```bash
  python manage.py makemigrations --check --dry-run
  ```
- [ ] Toutes les migrations appliquées localement
  ```bash
  python manage.py showmigrations
  ```
- [ ] Pas de transactions longues
- [ ] Pas de DROP TABLE en migrations

### Fixtures
- [ ] Fixtures de données initiales présentes (si nécessaire)
- [ ] Fixtures testées en local
- [ ] Fichiers de fixture commités

## 📦 Services externes

### Cloudinary (stockage fichiers)
- [ ] Compte créé : https://cloudinary.com
- [ ] API Key obtenue
- [ ] CLOUDINARY_URL copiée
- [ ] 25GB gratuit vérifiés
- [ ] Domaine sécurisé

### Resend (email)
- [ ] Compte créé : https://resend.com
- [ ] Domaine vérifié
- [ ] API Key générée
- [ ] Limite : 3000 emails/jour
- [ ] DEFAULT_FROM_EMAIL défini

### FedaPay (paiements)
- [ ] Compte créé : https://app.fedapay.com
- [ ] Clés API copiées (public + secret)
- [ ] Webhook secret généré
- [ ] Webhook URL configurée
- [ ] Mode : production ou sandbox ?

### Groq / Gemini / etc (IA)
- [ ] Au moins UN provider configuré
- [ ] Clés API obtenues
- [ ] Limites de requêtes connues
- [ ] Fallback prévu si un provider tombe

### NVIDIA OCR (optionnel)
- [ ] Compte créé : https://build.nvidia.com
- [ ] API Key obtenue
- [ ] OCR testé en local

## 🧪 Tests locaux

### Connexions
- [ ] `python manage.py check` réussit
  ```bash
  python manage.py check
  ```
- [ ] Base de données locale fonctionne
- [ ] Redis local fonctionne (si utilisé)
- [ ] Email (console backend) fonctionne
- [ ] Cloudinary credentials testées

### Fonctionnalité
- [ ] Admin panel accessible
- [ ] Authentification fonctionne
- [ ] Créer/lire/modifier/supprimer fonctionnent
- [ ] Fichiers uploadent (test Cloudinary)
- [ ] Emails s'envoient (test console)
- [ ] Tâches Celery s'exécutent (si utilisé)

### Performance
- [ ] Page charge en < 2s
- [ ] Pas de N+1 queries
- [ ] Database queries optimisées
- [ ] Assets statiques chargent vite

### Compatible Render
- [ ] Pas de accès filesystem (sauf /tmp)
- [ ] Pas de long-running requests (>30s)
- [ ] Pas de hardcoded paths (utiliser Path, os.path)
- [ ] Port utilisé : variable $PORT ou 10000

## 📝 Documentation

### README
- [ ] README.md à jour
- [ ] Instructions installation présentes
- [ ] Commands de déploiement listé
- [ ] Architecture expliquée

### Déploiement
- [ ] RENDER_DEPLOYMENT.md complète
- [ ] RENDER_QUICKSTART.md présente
- [ ] Exemples de variables d'environnement
- [ ] Dépannage documenté

## 🚀 Render Configuration

### Account Setup
- [ ] Compte Render créé
- [ ] Email vérifié
- [ ] Payment method ajoutée (si nécessaire)
- [ ] GitHub connecté
- [ ] Repository autorisé

### Services Planning
- [ ] Nombre de services compris
- [ ] Coûts estimés acceptables
- [ ] Régions disponibles vérifiées (Frankfurt choisi)

### Environment Planning
- [ ] 50+ variables d'environnement identifiées
- [ ] Clés API obtenues
- [ ] Passwords forts générés
- [ ] Secrets gérés (pas en dur)

## 📊 Logs & Monitoring

### Logging
- [ ] LOG_LEVEL défini
- [ ] Logs structurés (JSON si possible)
- [ ] Pas de logs verbeux en prod
- [ ] Erreurs sont trackées

### Monitoring (optionnel)
- [ ] Sentry configuré (erreur tracking)
- [ ] Health check endpoint présent
- [ ] Uptime monitoring envisagé
- [ ] Alertes configurées

## 🔄 Processus de déploiement

### Avant Push
- [ ] Git repository propre
  ```bash
  git status
  ```
- [ ] Pas de conflits
- [ ] Commits explicatifs
- [ ] Branch main à jour

### Push vers GitHub
- [ ] Tous les fichiers commités
  ```bash
  git add .
  git commit -m "feat: Render deployment configuration"
  git push origin main
  ```
- [ ] GitHub Actions réussissent (si configurées)
- [ ] Branch protégée (optionnel)

### Création Blueprint Render
- [ ] render.yaml détecté
- [ ] Services reconnus
- [ ] Pas d'erreurs de validation
- [ ] Preview correct

### Configuration Variables
- [ ] Toutes les variables required ajoutées
- [ ] Pas de variables vides
- [ ] Secrets marqués "sync: false"
- [ ] Values de test vs production clairs

## 📱 Post-déploiement

### Vérifications immédiates
- [ ] Build logs sans erreurs
- [ ] Services "Online"
- [ ] Instances running
- [ ] Health check passing

### Tests fonctionnels
- [ ] Admin panel accessible
- [ ] Authentification fonctionne
- [ ] CRUD operations marchent
- [ ] WebSockets fonctionnent
- [ ] Emails s'envoient
- [ ] Fichiers uploadent

### Monitoring
- [ ] CPU utilisation normale
- [ ] Memory utilisation acceptable
- [ ] Database connections OK
- [ ] Logs sans erreurs récurrentes

### Domaine (si applicable)
- [ ] DNS configuré
- [ ] SSL certificate automatique (Render)
- [ ] HTTPS fonctionne
- [ ] Redirect HTTP → HTTPS

## 🐛 Rollback Plan

En cas de problème :

1. **Logs** : Vérifier immédiatement
   ```
   Dashboard → Service → Logs
   ```

2. **Redéploiement** :
   ```bash
   # Sur Render
   Dashboard → Service → Redeploy
   ```

3. **Rollback** :
   ```bash
   git revert <bad-commit>
   git push origin main
   # Render redéploie automatiquement
   ```

4. **Désactiver** (urgence) :
   ```
   Dashboard → Service → Suspend
   ```

5. **Restauration base de données** :
   ```bash
   # Si sauvegarde préalable effectuée
   psql $DATABASE_URL < backup.sql
   ```

## 📞 Support en cas de besoin

- **Render Status** : https://status.render.com
- **Render Docs** : https://render.com/docs
- **Django Docs** : https://docs.djangoproject.com
- **Discord Render** : https://discord.gg/render (communauté)

## ✨ Signatures finales

```bash
# Vérification finale avant push
./deploy-render.sh    # Linux/Mac
.\deploy-render.ps1   # Windows PowerShell

# Output attendu :
# ✅ Tous les prérequis sont présents
# ✅ État Git OK
# ✅ render.yaml valide
# ✅ Dépendances OK
# 🚀 Prêt pour le déploiement !
```

---

## 📈 Statistiques avant déploiement

```bash
# Compter les fichiers
find . -name "*.py" -type f | wc -l  # Python files
find . -name "*.html" -type f | wc -l  # Templates

# Vérifier la taille
du -sh .  # Total size
git count-objects -v  # Git size

# Dépendances
pip list | wc -l  # Nombre packages

# Code quality (optionnel)
python -m py_compile **/*.py  # Vérifier syntax
pylint --version  # Si installé
```

---

**Important** : Ne pas déployer tant que toutes les cases ☑️ ne sont pas cochées.

Dernière mise à jour : 2026-05-24
