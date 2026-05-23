<div align="center">

<!-- BANNER -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1e3a5f,100:00b4d8&height=220&section=header&text=Academie%20Numerique%20IA&fontSize=48&fontColor=ffffff&fontAlignY=38&desc=Plateforme%20d%27evaluation%20intelligente%20pour%20l%27Afrique&descAlignY=58&descSize=18" width="100%"/>

<!-- BADGES TEMPS REEL -->
[![GitHub Stars](https://img.shields.io/github/stars/Durrell-229/academie-composition?style=for-the-badge&logo=github&color=FFD700&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Durrell-229/academie-composition?style=for-the-badge&logo=github&color=00b4d8&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/Durrell-229/academie-composition?style=for-the-badge&logo=github&color=ff6b6b&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Durrell-229/academie-composition?style=for-the-badge&logo=git&color=4caf50&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition/commits/main)
[![Code Size](https://img.shields.io/github/languages/code-size/Durrell-229/academie-composition?style=for-the-badge&logo=github&color=9c27b0&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition)
[![Contributors](https://img.shields.io/github/contributors/Durrell-229/academie-composition?style=for-the-badge&logo=github&color=ff9800&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition/graphs/contributors)

<!-- STACK TECHNIQUE -->
![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat-square&logo=django&logoColor=white)
![Django Ninja](https://img.shields.io/badge/Django%20Ninja-1.6-009688?style=flat-square&logo=fastapi&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Channels%204.3-DC382D?style=flat-square&logo=redis&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind%20CSS-3.x-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Dev%20%7C%20PostgreSQL-003B57?style=flat-square&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/Licence-MIT-yellow?style=flat-square)

<br/>

> **La première plateforme d'évaluation scolaire intelligente du Bénin.**
> Compositions en ligne, correction par IA, bulletins officiels et suivi en temps réel — tout en un.

<br/>

[🚀 Démarrage rapide](#-installation) · [📸 Aperçu](#-apercu) · [🤖 IA & Correction](#-correction-ia) · [📡 Temps réel](#-notifications-temps-reel) · [🗺 Architecture](#-architecture)

</div>

---

## 📸 Aperçu

<div align="center">

| Salle de composition | Correction IA | Bulletin officiel |
|:---:|:---:|:---:|
| ![Composition](https://images.unsplash.com/photo-1606326608606-aa0b62935f2b?w=340&q=80&auto=format&fit=crop) | ![Correction](https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=340&q=80&auto=format&fit=crop) | ![Bulletin](https://images.unsplash.com/photo-1568667256549-094345857637?w=340&q=80&auto=format&fit=crop) |
| Interface anti-triche temps réel | Multi-provider IA automatique | Format officiel béninois PDF |

</div>

---

## 🎯 Pourquoi Académie Numérique IA ?

<table>
<tr>
<td width="50%">

### Le problème
- 📋 Corrections manuelles longues et coûteuses
- 📬 Bulletins distribués avec semaines de retard
- 📊 Aucun suivi analytique des performances
- 🌍 Accès limité à l'éducation de qualité en Afrique

</td>
<td width="50%">

### Notre solution
- ⚡ Correction automatique en **< 30 secondes** par IA
- 📄 Bulletins PDF générés et envoyés **instantanément**
- 📈 Tableaux de bord analytiques en **temps réel**
- 🌐 Plateforme accessible depuis **n'importe quel appareil**

</td>
</tr>
</table>

---

## ✨ Fonctionnalités

### 🤖 Correction IA
```
Groq (principal) → Gemini (fallback) → Mistral → DeepSeek → NVIDIA Nemotron (OCR)
```
- Correction de copies manuscrites via OCR NVIDIA Nemotron
- Analyse du contenu, pertinence, orthographe, structure
- Note, commentaires et suggestions personnalisés
- Détection de plagiat inter-copies

### 🏛 Compositions en ligne
- Salle de composition sécurisée (anti-triche, détection de focus)
- Upload de copies scannées page par page
- Timer synchronisé avec l'heure officielle du serveur
- QR Code par résultat pour téléchargement mobile du bulletin

### 📊 Bulletins & Certifications
- Format officiel béninois avec coefficients par matière et par série
- Export PDF signé numériquement (PyHanko)
- QR Code d'authenticité vérifiable
- Envoi automatique par email (Resend API)

### 🎮 Gamification
- Points XP, badges, niveaux et classements
- Streaks de participation et récompenses
- Leaderboard par classe et par matière

### 📡 Temps Réel (SSE + WebSockets)
- Notifications push instantanées (cloche, compteur)
- Suivi live du statut de correction IA
- Synchronisation multi-onglets

### 💳 Paiements Mobile Money
- Intégration **FedaPay** (MTN MoMo, Moov Money)
- Commission automatique : **70% prof · 20% plateforme · 10% parrainage**
- Webhooks de confirmation en temps réel

---

## 🗺 Architecture

```
academie-numerique/
├── accounts/          # Utilisateurs UUID, rôles, Google OAuth2, SSO Laravel
├── core/              # Classes, matières, paramètres système
├── exams/             # Examens, assignments, relevés de notes
├── compositions/      # Sessions, salle en ligne, anti-triche, résultats
├── correction/        # Pipeline IA multi-provider + correction humaine
├── corrections/       # App dédiée corrections prof
├── bulletins/         # Génération PDF, coefficients officiels béninois
├── qcm/               # QCM auto-générés par IA par examen
├── devoirs/           # Devoirs nationaux, cycle complet
├── notifications/     # SSE temps réel, annonces globales
├── gamification/      # XP, badges, leaderboard
├── payments/          # FedaPay, abonnements, commissions
├── subscriptions/     # Plans, accès paywall
├── realtime/          # Django Channels / WebSockets
├── certifications/    # Certificats numériques signés
├── plagiat/           # Détection inter-copies
├── analytics/         # Tableaux de bord, statistiques
├── messaging/         # Messagerie interne
├── parents/           # Portail parents
├── library/           # Bibliothèque de ressources
├── schedule/          # Emploi du temps
├── attendance/        # Suivi présences
├── cahier/            # Cahier de textes numérique
├── audittrail/        # Journal d'audit complet
├── webhooks/          # Webhooks sortants
├── schools/           # Multi-établissements
├── api/               # REST API (Django Ninja)
└── academie_numerique/ # Config principale + ASGI + Redis
```

---

## 👥 Rôles & Permissions

| Rôle | Accès | Capacités clés |
|------|-------|---------------|
| 👨‍💼 **Administrateur** | Global | Gestion devoirs nationaux, approbations, statistiques globales |
| 👨‍🏢 **Conseiller Pédagogique** | École | Supervision, validation bulletins, analytics classe |
| 👨‍🏫 **Professeur** | Matière | Création examens/QCM, correction, bulletins, revenus |
| 👨‍🎓 **Élève** | Personnel | Compositions, résultats, bulletins, gamification |
| 👨‍👩‍👧 **Parent** | Enfant | Suivi résultats, notifications, bulletins |

---

## 🚀 Installation

### Prérequis
- Python 3.10+
- Redis (optionnel — fallback thread si absent)
- Git

### 1. Cloner et installer

```bash
git clone https://github.com/Durrell-229/academie-composition.git
cd academie-composition

python -m venv venv
source venv/bin/activate        # Linux/macOS
.\venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Configurer l'environnement

```bash
cp .env.example .env
```

Éditez `.env` avec vos clés :

```env
DJANGO_SECRET_KEY=votre-cle-secrete-tres-longue
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# IA (au moins un provider)
AI_PROVIDER=groq
GROQ_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# Paiements (optionnel — sandbox disponible)
FEDAPAY_ENVIRONMENT=sandbox
FEDAPAY_PUBLIC_KEY=pk_sandbox_xxx
FEDAPAY_SECRET_KEY=sk_sandbox_xxx
```

### 3. Initialiser la base de données

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ouvrez [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧪 Tests rapides

```bash
# Vérification Django (0 erreurs)
python manage.py check

# Créer des données de démonstration
python manage.py shell -c "
from accounts.models import User
from core.models import Classe, Matiere
from exams.models import Exam
from django.utils import timezone
from datetime import timedelta

# Créer un professeur et un élève de test
prof = User.objects.create_user(email='prof@demo.bj', password='demo2026', role='prof', first_name='Jean', last_name='Demo')
eleve = User.objects.create_user(email='eleve@demo.bj', password='demo2026', role='eleve', first_name='Marie', last_name='Demo', classe='Terminale')

print('Demo créé — connectez-vous sur /accounts/login/')
"
```

---

## 🌍 Déploiement (Render.com)

Le projet est prêt pour Render avec `render.yaml` et `Procfile` inclus.

```yaml
# render.yaml (extrait)
services:
  - type: web
    name: academie-numerique
    runtime: python
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: gunicorn academie_numerique.asgi:application -k uvicorn.workers.UvicornWorker
```

Variables d'environnement à configurer sur le dashboard Render :
`DJANGO_SECRET_KEY` · `DATABASE_URL` · `GROQ_API_KEY` · `REDIS_URL` · `FEDAPAY_SECRET_KEY`

---

## 📈 Statistiques du projet

<div align="center">

[![GitHub Activity](https://img.shields.io/github/commit-activity/m/Durrell-229/academie-composition?style=for-the-badge&color=00b4d8&labelColor=1e3a5f&label=Commits%2Fmois)](https://github.com/Durrell-229/academie-composition/commits/main)
[![Top Language](https://img.shields.io/github/languages/top/Durrell-229/academie-composition?style=for-the-badge&color=3776AB&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition)
[![Repo Size](https://img.shields.io/github/repo-size/Durrell-229/academie-composition?style=for-the-badge&color=9c27b0&labelColor=1e3a5f)](https://github.com/Durrell-229/academie-composition)

![GitHub Stats](https://github-readme-stats.vercel.app/api?username=Durrell-229&show_icons=true&theme=tokyonight&hide_border=true&include_all_commits=true&count_private=true)

[![GitHub Streak](https://streak-stats.demolab.com?user=Durrell-229&theme=tokyonight&hide_border=true&locale=fr)](https://git.io/streak-stats)

</div>

---

## 🛡 Sécurité

| Protection | Statut | Détail |
|-----------|--------|--------|
| Variables sensibles | ✅ | Gérées via `.env` (jamais committées) |
| Authentication | ✅ | Django auth + OAuth2 + SSO |
| CSRF | ✅ | Protection Django native |
| Rate limiting | ✅ | Sur login et endpoints critiques |
| Audit trail | ✅ | Journal complet de toutes les actions |
| Signatures PDF | ✅ | PyHanko pour bulletins officiels |

---

## 🤝 Contribuer

Les contributions sont les bienvenues !

```bash
# 1. Forkez le projet
# 2. Créez votre branche
git checkout -b feature/ma-fonctionnalite

# 3. Committez
git commit -m "feat: ajout de ma fonctionnalité"

# 4. Poussez et ouvrez une Pull Request
git push origin feature/ma-fonctionnalite
```

---

## 📄 Licence

Distribué sous la licence **MIT**. Voir [`LICENSE`](LICENSE) pour plus d'informations.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00b4d8,100:1e3a5f&height=120&section=footer" width="100%"/>

**Développé avec passion pour l'éducation africaine**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Durrell--229-0077B5?style=flat-square&logo=linkedin)](https://linkedin.com)
[![GitHub](https://img.shields.io/badge/GitHub-Durrell--229-181717?style=flat-square&logo=github)](https://github.com/Durrell-229)

*Si ce projet vous aide, laissez une ⭐ — cela fait toujours plaisir !*

</div>
