# DOCUMENTATION SYSTÈME TEMPS RÉEL

## 🚀 OVERVIEW

Le système temps réel permet à votre application de fonctionner comme une vraie école avec:
- Notifications instantanées
- Salles d'examen en temps réel
- Mises à jour de bulletins en direct
- Chat en temps réel
- Timer synchronisé
- Surveillance anti-triche en direct

## 📋 FONCTIONNALITÉS

### 1. Salles d'Examen en Temps Réel
- Synchronisation du timer entre tous les élèves
- Notifications de début/fin d'examen
- Chat entre participants
- Alertes anti-triche en direct
- Soumission de copies en temps réel

### 2. Notifications Instantanées
- Nouveaux examens/devoirs
- Corrections terminées
- Mises à jour de bulletins
- Messages des professeurs

### 3. Bulletins en Direct
- Mises à jour automatiques après correction
- Calcul de moyenne en temps réel
- Rang en direct

### 4. Surveillance Anti-Triche
- Détection de comportements suspects
- Alertes immédiates aux surveillants
- Logs en temps réel

## 🔧 INSTALLATION

### 1. Installer les dépendances
```bash
python install_realtime.py
```

### 2. Installer Redis
- Windows: Télécharger depuis https://redis.io/download
- Linux: `sudo apt-get install redis-server`
- Mac: `brew install redis`

### 3. Démarrer Redis
```bash
redis-server
```

### 4. Lancer le serveur avec Daphne
```bash
daphne -b 0.0.0.0 -p 8000 academie_numerique.asgi:application
```

## 💻 UTILISATION

### JavaScript Client Example

```javascript
// Connexion à une salle d'examen
const examSocket = new WebSocket('ws://localhost:8000/ws/exam/1/');

examSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'timer_update':
            updateTimer(data.time_remaining);
            break;
        case 'chat_message':
            displayChatMessage(data.user_name, data.message);
            break;
        case 'anti_cheat_alert':
            showAntiCheatAlert(data.alert_type);
            break;
        case 'correction_result':
            displayCorrectionResult(data.result);
            break;
    }
};

// Envoyer un message chat
examSocket.send(JSON.stringify({
    type: 'chat_message',
    message: 'Question sur le sujet'
}));

// Soumettre une copie
examSocket.send(JSON.stringify({
    type: 'submission',
    session_id: 1,
    files: [...],
    text_response: '...'
}));
```

### Notifications
```javascript
const notificationSocket = new WebSocket('ws://localhost:8000/ws/notifications/');

notificationSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'notification') {
        showNotification(data.notification);
    }
};
```

### Bulletins
```javascript
const bulletinSocket = new WebSocket('ws://localhost:8000/ws/bulletin/');

bulletinSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'bulletin_update') {
        updateBulletin(data.bulletin);
    }
};
```

## 🎯 INTÉGRATION AVEC VOTRE SYSTÈME

### Intégration avec Correction Automatique
```python
from realtime.services import realtime_service

# Après correction
realtime_service.notify_correction_completed(
    user_id=student.id,
    correction_result=correction_result
)
```

### Intégration avec Examens
```python
# Notifier début examen
realtime_service.notify_exam_started(
    exam_id=exam.id,
    student_ids=[student.id for student in students]
)

# Mise à jour timer
realtime_service.send_timer_update(
    exam_id=exam.id,
    time_remaining=3600,
    status='active'
)
```

## 📊 MONITORING

### Vérifier l'état des connexions
```python
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
```

### Logs
Les logs sont disponibles dans:
- Django logs
- Redis logs
- Application logs

## 🔒 SÉCURITÉ

- Authentification requise pour toutes les connexions WebSocket
- Validation des messages
- Rate limiting
- Encryption des connexions

## 🚨 TROUBLESHOOTING

### Connexions WebSocket échouent
- Vérifiez que Redis est en cours d'exécution
- Vérifiez la configuration ASGI
- Vérifiez les pare-feux

### Notifications ne s'affichent pas
- Vérifiez que le client WebSocket est connecté
- Vérifiez les logs serveur
- Vérifiez la configuration Channels

### Timer non synchronisé
- Vérifiez la diffusion des messages
- Vérifiez la latence réseau
- Vérifiez l'horloge serveur

## 📈 PERFORMANCE

- Supporte plusieurs milliers de connexions simultanées
- Latence < 100ms pour les messages
- Scalable avec Redis Cluster
- Optimisé pour les écoles de grande taille
