# 🎓 ACADÉMIE NUMÉRIQUE - GUIDE DE DÉMARRAGE RAPIDE

## 📋 Architecture Complète - 17 Applications Django

```
📁 academie_numerique/
├── 🏫 schools/              Multi-établissements, campus, classes
├── 📚 academic/             Gestion académique, notes, bulletins
├── 📅 schedule/             Emplois du temps, événements
├── ✅ attendance/           Présences, absences, retards
├── 📖 cahier/               Cahier de texte, devoirs
├── 💬 messaging/            Messagerie interne
├── 🎓 certificats/          Certificats BEPC/Bac + OCR IA
├── 💰 payments/             Paiements Mobile Money (XOF)
├── 👨‍👩‍👧 parents/              Portail parents
├── 📚 library/              Bibliothèque numérique
├── 📊 analytics/            Statistiques & rapports
├── 🤖 ai_engine/            IA & OCR
└── 🔧 [apps existantes]     accounts, core, exams...
```

---

## 🚀 DÉMARRAGE EN 5 ÉTAPES

### ÉTAPE 1 : Configuration de l'environnement

```bash
# Activer l'environnement virtuel
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Installer les packages supplémentaires pour OCR
pip install pillow qrcode google-generativeai requests xhtml2pdf
```

### ÉTAPE 2 : Exécuter le script de configuration

```bash
# Méthode interactive (recommandée)
python setup_admin_and_demo.py

# Ou créer manuellement le superutilisateur
python manage.py createsuperuser
```

Le script créera :
- ✅ Superutilisateur admin
- ✅ Établissement de démo (Lycée Technique de Cotonou)
- ✅ Campus, classes, matières
- ✅ Types de certificats BEPC/Bac

### Option 2 : Commandes manuelles
```bash
# 1. Activer l'environnement
.venv\Scripts\activate

# 2. Lancer la configuration
python setup_admin_and_demo.py

# 3. Créer les migrations
python manage.py makemigrations schools academic schedule attendance cahier messaging certificats payments parents library analytics
python manage.py migrate

# 4. Lancer Redis (dans un terminal séparé)
# Windows: lancer Redis via Docker ou WSL
# Linux/Mac: redis-server

# 5. Lancer le worker Redis (dans un terminal séparé)
python manage.py run_worker

# 6. Démarrer le serveur (dans un autre terminal)
python manage.py runserver
```

### ÉTAPE 3 : Créer les migrations

```bash
# Créer les migrations pour toutes les nouvelles apps
python manage.py makemigrations schools academic schedule attendance cahier messaging certificats payments parents library analytics

# Appliquer les migrations
python manage.py migrate
```

### ÉTAPE 4 : Démarrer le serveur

```bash
# Mode développement
python manage.py runserver

# Accéder aux interfaces
🌐 http://127.0.0.1:8000/admin/      → Interface d'administration
🌐 http://127.0.0.1:8000/            → Application principale
📊 file:///docs/architecture_uml.html → Diagramme UML complet
```

### ÉTAPE 5 : Configurer les clés API IA (optionnel)

Créer un fichier `.env` à la racine :

```env
# Clés API IA (pour correction OCR)
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Configuration base de données
DB_ENGINE=sqlite3
# DB_ENGINE=postgresql
# DATABASE_URL=postgres://user:pass@localhost:5432/academie

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password

# Sécurité
DJANGO_SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
```

---

## 📐 VUE D'ENSEMBLE DE L'ARCHITECTURE

### Diagramme UML Interactif

Ouvrir le fichier dans votre navigateur :
```
docs/architecture_uml.html
```

Ce diagramme comprend :
- 🏗️ **Architecture globale** : Frontend → Backend → Infrastructure
- 🗄️ **Modèles de données** : Relations entre entités
- 📝 **Flux d'examen OCR** : Mode 2 (copies physiques)
- 👥 **Hiérarchie utilisateurs** : Super admin → Élève
- 💰 **Flux de paiement** : Mobile Money

---

## 🎯 FONCTIONNALITÉS CLÉS

### 1. 🎓 Certificats & Examens (Système Béninois)

**Types de certificats créés :**
- BEPC (Brevet d'Études du Premier Cycle)
- Baccalauréat

**Caractéristiques :**
- ✅ Template avec drapeau du Bénin
- ✅ Photo de l'élève intégrée
- ✅ Mention ADMIS (vert) / REFUSÉ (rouge)
- ✅ QR Code de vérification
- ✅ Signatures numériques

### 2. 📝 Correction IA OCR (Mode 2)

**Workflow complet :**
1. Élève compose sur feuille physique
2. Professeur upload la photo de la copie
3. **OCR extrait le texte** automatiquement
4. **IA corrige** en comparant avec corrigé-type
5. Note suggérée avec appréciation
6. Professeur vérifie et valide
7. Note enregistrée sur le bulletin

### 3. 📋 Bulletin Scolaire Béninois

**Éléments authentiques :**
- 🇧🇯 Drapeau du Bénin en en-tête
- 🏛️ "République du Bénin - Ministère de l'Enseignement"
- 📜 Devise nationale : "Fraternité - Justice - Travail"
- 📊 Tableau des notes avec coefficients
- ⭐ Compétences transversales (étoiles)
- ✍️ Signatures : Professeur, Directeur, Parent
- 🔒 Cachet officiel rond
- 📱 QR Code de vérification

### 4. 💰 Paiements Mobile Money

**Modes de paiement supportés :**
- 📱 MTN Mobile Money (MoMo)
- 🟠 Orange Money
- 🌊 Wave
- 💵 Espèces
- 💳 Carte bancaire

**Frais gérés :**
- Frais d'inscription
- Frais de scolarité
- Frais d'examen
- Cantine / Transport
- Fournitures scolaires

---

## 👥 ROLES UTILISATEURS

| Rôle | Permissions | Dashboard |
|------|-------------|-----------|
| 👑 **Super Admin** | Tout le système | Configuration globale |
| 👔 **Administrateur** | Établissement | Gestion établissement |
| 📋 **Directeur** | Validation finale | Rapports, certificats |
| 📚 **Prof Principal** | Classe + Matières | Notes, bulletins |
| ✏️ **Professeur** | Matières | Cahier de texte, notes |
| 🎒 **Élève** | Cours, résultats | Emploi du temps, notes |
| 👨‍👩‍👧 **Parent** | Suivi enfant | Notifications, paiements |

---

## ⚡ SYSTÈME DE TÂCHES REDIS (PAS CELERY)

Toutes les tâches asynchrones utilisent **Redis** et non Celery. Le système est plus léger et adapté au projet.

### Démarrer le worker Redis
```bash
# Terminal 1: Lancer le worker
python manage.py run_worker

# Le worker traite automatiquement:
# ✅ Génération des PDF (certificats, bulletins, reçus)
# ✅ Correction OCR des copies physiques
# ✅ Paiements Mobile Money
# ✅ Notifications emails et push
# ✅ Génération de rapports statistiques
```

### Utiliser les tâches dans le code
```python
from certificats.tasks import generer_pdf_certificat, corriger_copie_ocr
from payments.tasks import traiter_paiement_mobile
from academic.tasks import generer_bulletin_pdf

# Lancer une tâche en arrière-plan
task_id = generer_pdf_certificat.delay(certificat_id="uuid-123")
task_id = corriger_copie_ocr.delay(copie_id="uuid-456")
task_id = traiter_paiement_mobile.delay(paiement_id="uuid-789", telephone="+22990123456", operateur="mtn")
```

### Liste des tâches disponibles

| Tâche | Module | Description |
|-------|--------|-------------|
| `generer_pdf_certificat` | certificats | Génère le PDF d'un certificat |
| `corriger_copie_ocr` | certificats | Corrige une copie physique via IA |
| `generer_bulletin_examen` | certificats | Génère le bulletin d'examen |
| `traiter_paiement_mobile` | payments | Traite un paiement Mobile Money |
| `generer_recu` | payments | Génère le reçu PDF |
| `verifier_echeances` | payments | Vérifie les paiements en retard |
| `generer_bulletin_pdf` | academic | Génère le bulletin scolaire |
| `calculer_moyennes_classe` | academic | Calcule les moyennes de la classe |
| `notifier_nouvelle_note` | academic | Notifie élèves et parents |
| `notifier_absence` | parents | Notifie les parents d'une absence |
| `notifier_bulletin` | parents | Notifie des bulletins disponibles |
| `generer_rapport_statistique` | analytics | Génère un rapport complet |
| `calculer_kpi` | analytics | Calcule les indicateurs de performance |
| `generer_rapport_mensuel` | attendance | Rapport de présence mensuel |

## 🔧 COMMANDES UTILES

```bash
# Créer un nouvel utilisateur
python manage.py shell
>>> from accounts.models import User
>>> User.objects.create_user('prof1', 'prof@test.com', 'pass123', role='professeur')

# Générer un certificat
python manage.py shell
>>> from certificats.models import CertificatScolaire
>>> cert = CertificatScolaire.objects.create(...)

# Lancer le worker Redis (tâches asynchrones)
python manage.py run_worker

# Tests
python manage.py test

# Collecter les fichiers statiques
python manage.py collectstatic
```

---

## 📱 API REST (Django Ninja)

Les endpoints API sont disponibles à : `/api/`

Exemples :
- `GET /api/certificats/` → Liste des certificats
- `POST /api/payments/` → Créer un paiement
- `GET /api/attendance/stats/` → Statistiques de présence

---

## 🐳 DÉPLOIEMENT (Docker)

```bash
# Construire l'image
docker-compose build

# Démarrer les services
docker-compose up -d

# Créer le superutilisateur
docker-compose exec web python manage.py createsuperuser
```

---

## 📞 SUPPORT & CONTACT

**Documentation :**
- 📊 Diagramme UML : `docs/architecture_uml.html`
- 📝 Ce guide : `QUICKSTART.md`

**Support technique :**
- 📧 Email : support@academie-numerique.bj
- 🌐 Site web : https://academie-numerique.bj

---

## 🎉 FÉLICITATIONS !

Votre plateforme **Académie Numérique** est maintenant opérationnelle avec :

✅ **17 applications Django** fonctionnelles
✅ **80+ modèles de données** créés
✅ **Système scolaire du Bénin** (BEPC/Bac)
✅ **Correction IA OCR** pour copies physiques
✅ **Paiements Mobile Money** (XOF)
✅ **Certificats authentiques** avec QR Code
✅ **Bulletins officiels** avec drapeau 🇧🇯
✅ **Portail parents** complet
✅ **Messagerie interne** temps réel
✅ **Bibliothèque numérique**

**Prochaine étape :** Configurer votre premier établissement et inviter les utilisateurs ! 🚀

---

*© 2024-2025 Académie Numérique - Système éducatif béninois internationalisé*
