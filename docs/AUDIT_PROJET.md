# 🔍 Audit — Académie Numérique IA
> Date : 13 mai 2026 | Django 5.2 | Déploiement : Render (free)

---

## Résumé exécutif

Le projet est une plateforme académique Django ambitieuse et bien documentée, avec de nombreuses fonctionnalités (correction IA, bulletins PDF, paiements FedaPay, QCM, gamification, temps réel SSE...). Cependant, l'audit révèle **4 problèmes critiques de sécurité**, des lacunes d'architecture importantes, et un état Git qui nécessite un nettoyage urgent. Ces points doivent être traités avant tout passage en production.

---

## 🔴 CRITIQUE — Sécurité

### 1. Clés API réelles dans `.env`
Le fichier `.env` contient des clés **de production actives** :
```
GROQ_API_KEY=gsk_[RÉVOQUÉE]
NVIDIA_API_KEY=nvapi-[RÉVOQUÉE]
```
Bien que `.env` soit dans `.gitignore`, ces clés sont visibles localement et exposées si quelqu'un accède à la machine. **Régénérer ces clés immédiatement** si elles ont été exposées ou partagées.

### 2. Clé FedaPay publique hardcodée dans du code source
```python
# setup_abonnement_demo.py (ligne 48)
'cle_api_publique': 'pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0'

# setup_fedapay_live.py (ligne 26)
CLE_PUBLIQUE = 'pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0'
```
**Action :** Déplacer dans une variable d'environnement `FEDAPAY_PUBLIC_KEY` et utiliser `os.getenv()`.

### 3. `ALLOWED_HOSTS = ['*']` — Toutes les requêtes acceptées
```python
# settings.py ligne 16
ALLOWED_HOSTS = ['*']
```
Cela autorise n'importe quel domaine à faire des requêtes vers votre serveur. **En production, spécifier explicitement les domaines autorisés.**
```python
# À corriger :
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
```

### 4. `CORS_ALLOW_ALL_ORIGINS = True` avec credentials
```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
```
Cette combinaison est particulièrement dangereuse : elle autorise n'importe quel site à faire des requêtes authentifiées vers votre API. À restreindre aux domaines connus en production.

---

## 🟠 IMPORTANT — Architecture et déploiement

### 5. SQLite en production sur Render
```yaml
# render.yaml
- key: DB_ENGINE
  value: sqlite3
```
Sur Render en plan gratuit, le système de fichiers est **éphémère** : la base SQLite est effacée à chaque redéploiement. Toutes les données sont perdues. Il faut migrer vers PostgreSQL (Render propose un plan gratuit PostgreSQL).

### 6. `SECRET_KEY` avec valeur par défaut faible
```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production-very-secret-key-2025')
```
Si la variable d'environnement n'est pas définie, Django utilise cette clé prévisible. En production, `DJANGO_SECRET_KEY` doit toujours être définie et aléatoire (50+ caractères).

### 7. `CSRF_COOKIE_SECURE` défini deux fois
La ligne `CSRF_COOKIE_SECURE = not DEBUG` apparaît deux fois dans `settings.py` (lignes ~278 et ~311). La deuxième écrase la première. À nettoyer.

### 8. Ordre du middleware incorrect
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',  # ← Devrait être en 1er
    ...
]
```
`SecurityMiddleware` doit être le **premier** middleware de la liste pour appliquer les redirections HTTPS et autres protections le plus tôt possible. `WhiteNoise` doit venir juste après `SecurityMiddleware`.

### 9. CSP affaiblie par `unsafe-inline` et `unsafe-eval`
La Content Security Policy est bien définie, mais `'unsafe-inline'` et `'unsafe-eval'` dans `script-src` annulent une grande partie de sa protection contre les attaques XSS.

---

## 🟡 QUALITÉ DU CODE

### 10. 45 fichiers Python éparpillés à la racine
La racine du projet contient une quantité excessive de scripts :
- 16 fichiers `test_*.py` (tests manuels)
- ~10 fichiers `fix_*.py` / `debug_*.py` / `implement_*.py`
- Plusieurs scripts utilitaires ad hoc

**Recommandation :** Organiser dans des sous-dossiers (`/scripts/`, `/tests/`) ou supprimer les scripts obsolètes.

### 11. Duplication dans `requirements.txt`
Les packages suivants apparaissent plusieurs fois avec des contraintes différentes :
- `redis` (version `5.0.1` fixée ET `redis` sans version)
- `requests` (avec et sans contrainte de version `>=2.31.0`)
- `Pillow` (avec et sans contrainte `>=10.0.0`)

Cela peut provoquer des conflits d'installation. Garder une seule entrée par package.

### 12. README mentionne Django 4.x mais le projet tourne sur Django 5.2
```markdown
[![Django](https://img.shields.io/badge/Framework-Django%204.x-green.svg)]
```
Le badge est obsolète. Le projet utilise `Django==5.2.13`.

### 13. Deux apps similaires : `correction` vs `corrections`
Le projet a deux apps pour la correction (`correction/` et `corrections/`) et deux pour les certificats (`certifications/` et `certificats/`). Cela crée de la confusion et complique la maintenance.

### 14. `templates_backup/` committé dans le repo
Un dossier de sauvegarde de templates est versionné dans le repo. Ce type de dossier ne devrait pas être dans Git — utiliser les branches ou les tags pour sauvegarder.

---

## 🔵 GIT & VERSIONING

### 15. 1 commit en avance sur `origin/main`
```
Your branch is ahead of 'origin/main' by 1 commit.
```
Des changements locaux ne sont pas pushés.

### 16. Très nombreux fichiers modifiés non stagés
Des centaines de fichiers sont modifiés (migrations, templates, hooks...) sans être committs. L'historique Git devient difficile à lire et à auditer.

### 17. `db.sqlite3` non commité (correct ✅) mais présent à la racine
Le fichier `db.sqlite3` (3.2 MB) est bien ignoré par Git, mais sa présence dans le dossier de production ajoute du bruit. Sur Render, utiliser PostgreSQL.

### 18. Fichiers image à la racine : `bulletin.png`, `copie.jpg`, `Max_a_transforme_moi_cette.png`
Ces fichiers n'ont rien à faire à la racine du projet. Les déplacer vers `/media/` ou `/docs/`.

---

## ✅ Ce qui est bien fait

- **Sécurité en production** : `SECURE_SSL_REDIRECT`, `HSTS`, `SESSION_COOKIE_SECURE` correctement configurés pour `DEBUG=False`.
- **`.env` exclu de Git** : Les vraies clés ne sont pas dans l'historique Git.
- **`db.sqlite3` exclu de Git** : Bonne pratique respectée.
- **Logging configuré** : Console + fichier, avec niveaux par module.
- **Hooks Claude** : Scanner de secrets, bloqueur de commandes dangereuses — bonne initiative.
- **Documentation abondante** : Nombreux fichiers `.md` de documentation technique.
- **Architecture multi-provider IA** : Fallback automatique Groq/Gemini/Mistral bien pensé.
- **render.yaml** : Déploiement automatisé avec migrations et collectstatic.

---

## Plan d'action prioritaire

| Priorité | Action | Effort |
|----------|--------|--------|
| 🔴 P0 | Régénérer les clés GROQ et NVIDIA | 10 min |
| 🔴 P0 | Déplacer `pk_live_FedaPay` dans `.env` | 15 min |
| 🔴 P0 | Restreindre `ALLOWED_HOSTS` et `CORS_ALLOW_ALL_ORIGINS` | 15 min |
| 🟠 P1 | Migrer vers PostgreSQL sur Render | 1h |
| 🟠 P1 | Corriger l'ordre des middlewares | 5 min |
| 🟠 P1 | Supprimer la ligne `CSRF_COOKIE_SECURE` en double | 2 min |
| 🟡 P2 | Nettoyer les 45 scripts à la racine | 30 min |
| 🟡 P2 | Dédupliquer `requirements.txt` | 10 min |
| 🔵 P3 | Committer ou stasher les fichiers modifiés | 20 min |
| 🔵 P3 | Supprimer `templates_backup/` du repo | 5 min |

---

*Rapport généré par audit automatique — Académie Numérique IA — 13 mai 2026*
