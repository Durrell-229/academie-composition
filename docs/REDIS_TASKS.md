# ⚡ SYSTÈME DE TÂCHES REDIS - DOCUMENTATION COMPLÈTE

> **Pas de Celery !** Toutes les tâches asynchrones utilisent un système Redis léger et intégré.

---

## 🎯 POURQUOI REDIS ET NON CELERY ?

| Aspect | Celery | Redis Tasks (Notre solution) |
|--------|--------|-------------------------------|
| **Dépendances** | Besoin de RabbitMQ/Redis + Celery | Juste Redis |
| **Complexité** | Workers, beat, flower | Un seul worker simple |
| **Ressources** | Consommation élevée | Légère |
| **Maintenance** | Complexe | Simple |
| **Monitoring** | Outils externes | Intégré |

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION DJANGO                     │
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Views     │    │    Tasks    │    │    Models   │   │
│  │             │───▶│  @redis_task│───▶│             │   │
│  └─────────────┘    └─────────────┘    └─────────────┘   │
│         │                    │                    │         │
│         │             ┌──────┴──────┐             │         │
│         │             │             │             │         │
│         ▼             ▼             ▼             ▼         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              REDIS (Task Queue)                         ││
│  │  • List: task_queue                                    ││
│  │  • Keys: task_result:{id}                             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    REDIS WORKER                            │
│                                                              │
│  $ python manage.py run_worker                              │
│                                                              │
│  • Pop tasks from Redis                                     │
│  • Execute functions                                        │
│  • Store results                                            │
│  • Retry on failure                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 FICHIERS CRÉÉS

### Tasks Files (Redis)

| Fichier | Module | Nombre de tâches |
|---------|--------|-----------------|
| `certificats/tasks.py` | Certificats & Examens | 4 tâches |
| `payments/tasks.py` | Paiements | 5 tâches |
| `academic/tasks.py` | Gestion académique | 4 tâches |
| `parents/tasks.py` | Portail parents | 5 tâches |
| `analytics/tasks.py` | Statistiques | 3 tâches |
| `attendance/tasks.py` | Présences | 3 tâches |
| `notifications/tasks.py` | Notifications | 2 tâches |

**Total : 26 tâches Redis** ⚡

---

## 🚀 UTILISATION

### 1. Décorer une fonction avec `@redis_task`

```python
from core.redis_tasks import redis_task

@redis_task("mon_module.ma_tache")
def ma_fonction(param1, param2):
    """Ma tâche asynchrone"""
    # Traitement ici
    return "Résultat"
```

### 2. Lancer la tâche en arrière-plan

```python
# Dans une view ou un model
from mon_module.tasks import ma_fonction

# Lancer la tâche
task_id = ma_fonction.delay("valeur1", "valeur2")

# Le code continue immédiatement
# La tâche s'exécute en parallèle dans le worker
```

### 3. Vérifier le résultat

```python
from core.redis_tasks import get_task_result

result = get_task_result(task_id)
# {'status': 'success', 'result': '...'}
# ou {'status': 'error', 'error': '...'}
```

---

## 📋 LISTE COMPLÈTE DES TÂCHES

### 🎓 Certificats (`certificats/tasks.py`)

| Tâche | Fonction | Description |
|-------|----------|-------------|
| `generer_pdf_certificat` | `generer_pdf_certificat(certificat_id)` | Génère le PDF d'un certificat |
| `corriger_copie_ocr` | `corriger_copie_ocr(copie_id)` | Corrige une copie physique via IA |
| `verifier_certificat_qr` | `verifier_certificat_qr(code)` | Vérifie un certificat via QR |
| `generer_bulletin_examen` | `generer_bulletin_examen(inscription_id)` | Génère le bulletin d'examen |

### 💰 Paiements (`payments/tasks.py`)

| Tâche | Fonction | Description |
|-------|----------|-------------|
| `traiter_paiement_mobile` | `traiter_paiement_mobile(paiement_id, tel, op)` | Traite un paiement Mobile Money |
| `generer_recu` | `generer_reçu_paiement(paiement_id)` | Génère le reçu PDF |
| `envoyer_email_recu` | `envoyer_email_recu(paiement_id)` | Envoie le reçu par email |
| `verifier_echeances` | `verifier_echeances_retard()` | Vérifie les paiements en retard |
| `generer_rapport_financier` | `generer_rapport_financier(etab_id, debut, fin)` | Génère un rapport financier |

### 📚 Academic (`academic/tasks.py`)

| Tâche | Fonction | Description |
|-------|----------|-------------|
| `generer_bulletin` | `generer_bulletin_pdf(bulletin_id)` | Génère le PDF du bulletin |
| `calculer_moyennes_classe` | `calculer_moyennes_classe(classe_id, periode)` | Calcule les moyennes |
| `notifier_nouvelle_note` | `notifier_nouvelle_note(note_id)` | Notifie élèves et parents |
| `calculer_statistiques_trimestre` | `calculer_statistiques_trimestre(etab_id, periode)` | Stats du trimestre |

### 👨‍👩‍👧 Parents (`parents/tasks.py`)

| Tâche | Fonction | Description |
|-------|----------|-------------|
| `notifier_absence` | `notifier_absence_eleve(absence_id)` | Notifie d'une absence |
| `notifier_retard` | `notifier_retard_eleve(retard_id)` | Notifie d'un retard |
| `notifier_bulletin` | `notifier_bulletin_disponible(bulletin_id)` | Notifie du bulletin |
| `notifier_paiement` | `notifier_paiement_requis(paiement_id)` | Notifie d'un paiement |
| `sync_donnees_parent` | `sync_donnees_parent(parent_id)` | Synchronise les données |

### 📊 Analytics (`analytics/tasks.py`)

| Tâche | Fonction | Description |
|-------|----------|-------------|
| `generer_rapport_statistique` | `generer_rapport_statistique(rapport_id)` | Génère un rapport |
| `calculer_kpi` | `calculer_kpi(etab_id, type, periode)` | Calcule un KPI |
| `generer_tableau_bord` | `generer_tableau_bord(user_id, periode)` | Génère un dashboard |

### ✅ Attendance (`attendance/tasks.py`)

| Tâche | Fonction | Description |
|-------|----------|-------------|
| `generer_rapport_mensuel` | `generer_rapport_mensuel(classe_id, mois, annee)` | Rapport mensuel |
| `notifier_absences_cumulees` | `notifier_absences_cumulees(eleve_id)` | Alert absences |
| `calculer_statistiques_assiduite` | `calculer_statistiques_assiduite(classe_id, debut, fin)` | Stats assiduité |

### 🔔 Notifications (`notifications/tasks.py`)

| Tâche | Fonction | Description |
|-------|----------|-------------|
| `send_notification_email` | `send_notification_email(notification_id)` | Envoie un email |
| `create_and_send_notification` | `create_and_send_notification(...)` | Crée et envoie |

---

## 🖥️ COMMANDES DE GESTION

### Démarrer le worker

```bash
# Terminal dédié
python manage.py run_worker

# Options
python manage.py run_worker --max-tasks 100  # Stop après 100 tâches
```

### Lancer Redis (si pas déjà en cours)

```bash
# Docker
redisdocker run -d -p 6379:6379 redis:latest

# Linux/Mac
redis-server

# Windows (WSL)
sudo service redis-server start
```

### Vérifier les tâches en attente

```python
# Shell Django
from core.redis_tasks import get_redis_connection
r = get_redis_connection()
r.llen('task_queue')  # Nombre de tâches en attente
```

---

## 🔧 CONFIGURATION

### Variables d'environnement

```env
# Redis (obligatoire pour les tâches)
REDIS_URL=redis://localhost:6379/0
# ou
REDIS_URL=redis://user:password@host:6379/0
```

### Settings Django

```python
# academie_numerique/settings.py

# Redis (déjà configuré)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Pas de Celery
# CELERY_BROKER_URL = ...  # ❌ PAS NÉCESSAIRE
# CELERY_RESULT_BACKEND = ...  # ❌ PAS NÉCESSAIRE
```

---

## 📊 MONITORING

### Logs du worker

```bash
# Afficher les logs en temps réel
python manage.py run_worker 2>&1 | tee worker.log
```

### Vérifier le statut des tâches

```python
from core.redis_tasks import get_task_result

# Vérifier si une tâche est terminée
result = get_task_result("task-uuid-123")
if result:
    print(f"Statut: {result['status']}")
    print(f"Résultat: {result.get('result')}")
```

---

## 🧪 EXEMPLES D'UTILISATION

### Exemple 1 : Génération de PDF en arrière-plan

```python
# views.py
from certificats.tasks import generer_pdf_certificat
from django.http import JsonResponse

def delivrer_certificat(request, certificat_id):
    # Lancer la génération en arrière-plan
    task_id = generer_pdf_certificat.delay(certificat_id)
    
    return JsonResponse({
        'success': True,
        'message': 'Certificat en cours de génération',
        'task_id': task_id
    })
```

### Exemple 2 : Correction OCR d'une copie

```python
# views.py
from certificats.tasks import corriger_copie_ocr

def upload_copie_examen(request):
    # Sauvegarder la copie
    copie = CopieExamenPhysique.objects.create(
        inscription=inscription,
        image_copie=request.FILES['image'],
        statut='en_attente'
    )
    
    # Lancer la correction IA
    task_id = corriger_copie_ocr.delay(str(copie.id))
    
    return JsonResponse({
        'success': True,
        'message': 'Copie en cours de correction par IA',
        'task_id': task_id,
        'estimated_time': '30 secondes'
    })
```

### Exemple 3 : Paiement Mobile Money

```python
# views.py
from payments.tasks import traiter_paiement_mobile

def effectuer_paiement(request):
    paiement = Paiement.objects.create(
        eleve=request.user,
        frais=frais,
        montant_paye=montant,
        mode_paiement='momo',
        statut='en_attente'
    )
    
    # Traiter le paiement en arrière-plan
    task_id = traiter_paiement_mobile.delay(
        paiement_id=str(paiement.id),
        telephone=request.POST['telephone'],
        operateur=request.POST['operateur']  # 'mtn', 'orange', 'wave'
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Paiement en cours de traitement',
        'task_id': task_id
    })
```

---

## 🎓 RÉCAPITULATIF

✅ **26 tâches Redis** créées et prêtes à l'emploi  
✅ **Pas de Celery** - Système léger basé sur Redis  
✅ **Génération PDF** en arrière-plan (certificats, bulletins, reçus)  
✅ **Correction OCR** automatique des copies physiques  
✅ **Paiements Mobile Money** asynchrones  
✅ **Notifications** emails et push  
✅ **Rapports statistiques** générés automatiquement  

---

## 📞 SUPPORT

En cas de problème avec les tâches Redis :

1. Vérifier que Redis est en cours : `redis-cli ping` → `PONG`
2. Vérifier le worker est lancé : `python manage.py run_worker`
3. Vérifier les logs : `logs/django.log` et `worker.log`
4. Redémarrer le worker si bloqué

---

**⚡ Système de tâches Redis - Léger, rapide, efficace !**
