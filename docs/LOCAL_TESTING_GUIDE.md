# 🧪 GUIDE DE TEST LOCAL COMPLET
## Académie Numérique IA - Test complet en local

---

## 📋 PRÉREQUIS

### 1. Environnement de développement
```bash
# Vérifier Python 3.14+
python --version

# Activer l'environnement virtuel
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Base de données
```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Créer superutilisateur
python manage.py createsuperuser
```

### 3. Démarrer les services
```bash
# Terminal 1: Serveur Django
python manage.py runserver 5600

# Terminal 2: Worker Redis (optionnel pour tests)
python manage.py run_worker
```

---

## 🎯 SCÉNARIOS DE TEST

### Scénario 1: Inscription Élève
**URL**: `http://127.0.0.1:5600/register/`

1. **Créer un compte élève**
   - Email: `eleve.test@ecole.com`
   - Mot de passe: `Test123456!`
   - Nom: Test Élève
   - Classe: `3ème A`

2. **Vérifications**
   - ✅ Compte créé
   - ✅ Email vérifié (si configuré)
   - ✅ Connexion réussie

### Scénario 2: Création Examen (Admin)
**URL**: `http://127.0.0.1:5600/admin/`

1. **Se connecter comme superutilisateur**
2. **Créer une matière**
   - Nom: `Français`
   - Niveau: `Secondaire`
   - Coefficient: `3`

3. **Créer un examen**
   - Titre: `Composition Français - Test Local`
   - Matière: Français
   - Durée: `60` minutes
   - Note maximale: `20`

4. **Uploader les fichiers**
   - Sujet: `sujet_francais.pdf`
   - Corrigé type: `corrige_francais.pdf`

### Scénario 3: Session de Composition
**URL**: `http://127.0.0.1:5600/compositions/room/{session_id}/`

1. **Démarrer la composition**
   - Caméra: ✅ Active
   - Timer: ✅ 60:00
   - Anti-triche: ✅ Actif

2. **Pendant la composition**
   - ✅ Screenshot toutes les 15s
   - ✅ Analyse Nemotron toutes les 30s
   - ✅ Blocage F12, Ctrl+C/V, clic droit

3. **Soumettre la composition**
   - Texte: Rédiger une réponse
   - Fichier: Scanner une copie (optionnel)
   - Valider la soumission

### Scénario 4: Correction IA
**Processus automatique ou manuel**

1. **Correction automatique** (Redis actif)
   ```bash
   # Vérifier les logs
   python manage.py check_tasks
   ```

2. **Correction manuelle** (tests)
   ```bash
   python manual_correction_fix.py
   ```

3. **Vérifications**
   - ✅ Note générée (ex: 15/20)
   - ✅ Appréciation créée
   - ✅ Bulletin PDF généré
   - ✅ Session marquée 'corrige'

### Scénario 5: Accès Élève au Bulletin
**URL**: `http://127.0.0.1:5600/compositions/result/{session_id}/`

1. **Voir les résultats**
   - Note et mention
   - Appréciation détaillée
   - Points forts/axes d'amélioration

2. **Télécharger le bulletin**
   - PDF officiel format A4
   - QR code de vérification
   - Coefficient officiel

---

## 📊 SCRIPTS DE TEST AUTOMATISÉS

### Script 1: Création données de test
```bash
python create_test_data.py
```

### Script 2: Test complet du flux
```bash
python test_full_flow.py
```

### Script 3: Vérification système
```bash
python system_check.py
```

---

## 🔧 OUTILS DE DÉBOGAGE

### 1. Vérifier les sessions
```bash
python debug_sessions.py
```

### 2. Tester les tâches Redis
```bash
python debug_tasks.py
```

### 3. Correction manuelle
```bash
python manual_correction_fix.py
```

---

## 📱 URLS DE TEST IMPORTANTES

| Service | URL | Description |
|---------|-----|-------------|
| **Accueil** | `http://127.0.0.1:5600/` | Page d'accueil |
| **Admin** | `http://127.0.0.1:5600/admin/` | Administration Django |
| **Dashboard** | `http://127.0.0.1:5600/dashboard/` | Tableau de bord élève |
| **Compositions** | `http://127.0.0.1:5600/compositions/` | Liste des examens |
| **Salle composition** | `http://127.0.0.1:5600/compositions/room/{id}/` | Interface examen |
| **Résultats** | `http://127.0.0.1:5600/compositions/result/{id}/` | Page résultats |
| **Bulletin PDF** | `http://127.0.0.1:5600/compositions/bulletin/{id}/` | Téléchargement bulletin |

---

## 🎮 COMPTE UTILISATEURS DE TEST

### Élève 1
- **Email**: `eleve.test@ecole.com`
- **Mot de passe**: `Test123456!`
- **Classe**: `3ème A`

### Élève 2
- **Email**: `test2@example.com`
- **Mot de passe**: `Test123456!`
- **Classe**: `4ème B`

### Admin
- **Email**: `admin@academie.com`
- **Mot de passe**: `Admin123456!`

---

## ⚠️ POINTS DE CONTRÔLE

### ✅ Checklist de validation

#### [ ] Inscription et connexion
- [ ] Création compte élève
- [ ] Connexion réussie
- [ ] Dashboard accessible

#### [ ] Création examen
- [ ] Matière créée
- [ ] Examen configuré
- [ ] Fichiers uploadés

#### [ ] Session composition
- [ ] Caméra active
- [ ] Timer fonctionnel
- [ ] Anti-triche actif
- [ ] Soumission réussie

#### [ ] Correction IA
- [ ] Analyse Nemotron
- [ ] Note générée
- [ ] Bulletin PDF

#### [ ] Accès résultats
- [ ] Page résultats
- [ ] Bulletin téléchargeable
- [ ] QR code fonctionnel

---

## 🚨 DÉPANNAGE

### Problèmes courants

1. **Caméra ne s'active pas**
   ```bash
   # Vérifier les permissions HTTPS
   # Chrome: chrome://flags/unsafely-treat-insecure-origin-as-secure
   ```

2. **Correction IA ne fonctionne pas**
   ```bash
   # Vérifier les clés API
   python manage.py check_api_keys
   ```

3. **Bulletin PDF ne se génère pas**
   ```bash
   # Vérifier les templates
   python manage.py check_templates
   ```

4. **Redis ne fonctionne pas**
   ```bash
   # Mode manuel disponible
   python manual_correction_fix.py
   ```

---

## 📈 MÉTRIQUES DE PERFORMANCE

### Temps de réponse attendus
- **Chargement page**: < 2 secondes
- **Démarrage caméra**: < 3 secondes
- **Analyse Nemotron**: 15-30 secondes
- **Correction IA**: 30-60 secondes
- **Génération bulletin**: 5-10 secondes

### Ressources système
- **Mémoire**: < 512MB (Django)
- **CPU**: < 25% (correction IA)
- **Stockage**: 10MB par composition

---

## 🎯 OBJECTIFS DE TEST

### Primary Goals
1. ✅ **Flux complet fonctionnel**
2. ✅ **Interface utilisateur responsive**
3. ✅ **Correction IA précise**
4. ✅ **Bulletins générés correctement**
5. ✅ **Performance acceptable**

### Secondary Goals
1. ✅ **Sécurité anti-triche**
2. ✅ **Notifications temps réel**
3. ✅ **Gamification fonctionnelle**
4. ✅ **Accessibilité mobile**

---

## 📝 NOTES DE TEST

### À tester spécifiquement
- [ ] Comportement avec mauvaise connexion
- [ ] Gestion des erreurs IA
- [ ] Limitation taille fichiers
- [ ] Timeout des sessions
- [ ] Accès concurrents multi-utilisateurs

### Rapport de bugs
Utiliser le format:
```
**Titre**: [Court descriptif]
**Étapes**: [1, 2, 3...]
**Résultat attendu**: [Ce qui devrait arriver]
**Résultat obtenu**: [Ce qui se passe]
**Environnement**: [Navigateur, OS]
```

---

## 🚀 DÉPLOIEMENT

### Prérequis pour la production
1. ✅ Tous les tests passent
2. ✅ Performance acceptable
3. ✅ Sécurité validée
4. ✅ Documentation complète

### Checklist déploiement
- [ ] Base de données production
- [ ] Variables d'environnement
- [ ] Services externes (Redis, IA)
- [ ] Monitoring et logs
- [ ] Sauvegardes automatiques

---

*Ce guide couvre tous les aspects du test local. Suivez les étapes séquentiellement pour une validation complète du système.*
