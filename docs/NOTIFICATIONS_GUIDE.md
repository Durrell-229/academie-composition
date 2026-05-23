# 📢 Système de Notifications en Temps Réel

## 🎯 Fonctionnalités Implémentées

### ✅ **1. Notifications Push en Temps Réel (SSE)**
- Les utilisateurs reçoivent instantanément les notifications sans recharger la page
- Utilisation de **Server-Sent Events (SSE)** pour une connexion persistante
- Reconnexion automatique en cas de perte de connexion

### ✅ **2. Cloche de Notification dans la Navigation**
- Icône de cloche visible dans la barre de navigation (`app_base.html`)
- Badge rouge avec compteur de notifications non lues
- Menu déroulant avec aperçu des 10 dernières notifications
- Mise à jour automatique du compteur en temps réel

### ✅ **3. Page de Notifications Améliorée**
- Liste complète des notifications avec filtres visuels
- Marquer une notification comme lue via AJAX (sans rechargement)
- Marquer toutes les notifications comme lues
- Support des notifications navigateur (si permission accordée)

### ✅ **4. Création de Notifications pour Admins**
- Modal "Envoyer Notification" dans le dashboard admin
- Options de destinataires : Tous, Élèves, Professeurs, Conseillers
- Types de notifications : Inscription, Bulletin, Approbation
- Envoi instantané à tous les utilisateurs sélectionnés

## 🚀 Comment ça Marche

### **Flux de Notification en Temps Réel**

```
ADMIN CRÉE NOTIFICATION
        ↓
Django enregistre en base de données
        ↓
SSE détecte nouvelle notification (toutes les 2s)
        ↓
Push notification à TOUS les clients connectés
        ↓
Chaque utilisateur voit la notification apparaître
        ↓
Badge de cloche se met à jour automatiquement
        ↓
Notification navigateur affichée (si activée)
```

## 📋 Utilisation

### **Pour les Administrateurs**

1. **Créer une notification :**
   - Aller au Dashboard Admin
   - Cliquer sur "Envoyer Notification" (icône cloche)
   - Remplir le formulaire :
     - **Titre** : Titre court et descriptif
     - **Message** : Contenu détaillé
     - **Destinataires** : Choisir le groupe cible
     - **Type** : Catégorie de notification
   - Cliquer sur "Envoyer"

2. **Exemples de notifications :**
   ```
   Titre: "Nouveau bulletin disponible"
   Message: "Votre bulletin du trimestre 1 est maintenant disponible. Consultez-le dans la section Mes Bulletins."
   Destinataires: Élèves uniquement
   Type: Bulletin
   ```

### **Pour les Utilisateurs**

1. **Recevoir des notifications :**
   - Se connecter à l'application
   - La cloche dans la navigation montre les notifications non lues
   - Cliquer sur la cloche pour voir l'aperçu
   - Cliquer sur "Voir toutes les notifications" pour la liste complète

2. **Marquer comme lu :**
   - **Depuis la cloche** : Cliquer sur une notification la marque comme lue
   - **Depuis la page** : Cliquer sur "Marquer comme lu" ou "Tout marquer comme lu"
   - Les notifications lues n'ont plus de point bleu

3. **Notifications Navigateur :**
   - À la première visite, le navigateur demande la permission
   - Si accepté, les notifications apparaissent même si l'onglet est en arrière-plan

## 🔧 Architecture Technique

### **Fichiers Créés/Modifiés**

```
notifications/
├── views_sse.py              # ✨ NOUVEAU: SSE stream pour temps réel
├── views.py                  # ✏️ AJOUT: mark_notification_read
├── urls.py                   # ✏️ AJOUT: routes SSE et mark-read

templates/
├── partials/
│   └── _notification_bell.html  # ✨ NOUVEAU: Cloche avec Alpine.js
├── notifications/
│   └── list.html                # ✏️ AMÉLIORÉ: Temps réel + AJAX
├── app_base.html                # ✏️ AJOUT: Include notification bell
```

### **Endpoints API**

| URL | Méthode | Description |
|-----|---------|-------------|
| `/notifications/stream/` | GET | SSE stream (connexion persistante) |
| `/notifications/unread-count/` | GET | Retourne le compteur de non-lus (JSON) |
| `/notifications/mark-read/<id>/` | POST | Marque une notification comme lue |
| `/notifications/create/` | POST | Créer une notification (admin uniquement) |

### **Technologies Utilisées**

- **Server-Sent Events (SSE)** : Push serveur → client
- **Alpine.js** : Réactivité côté client
- **Django ORM** : Gestion des notifications
- **Browser Notification API** : Notifications système

## 🎨 Personnalisation

### **Ajouter un Nouveau Type de Notification**

1. Dans `notifications/models.py` :
```python
NOTIFICATION_TYPES = [
    ('INSCRIPTION', 'Inscription'),
    ('BULLETIN', 'Bulletin Disponible'),
    ('APPROBATION', 'Approbation Requise'),
    ('NOUVEAU_TYPE', 'Nouveau Type'),  # ← Ajouter ici
]
```

2. Dans `_notification_bell.html`, ajouter l'icône :
```javascript
'bg-purple/10 text-purple': notif.type === 'NOUVEAU_TYPE',
```

## 🐛 Dépannage

### **Les notifications n'apparaissent pas en temps réel ?**

1. Vérifier la console du navigateur pour les erreurs SSE
2. Confirmer que `EventSource` est supporté (oui pour tous les navigateurs modernes)
3. Vérifier que le serveur Django n'est pas en mode debug avec reload auto

### **Le compteur de cloche ne se met pas à jour ?**

1. Ouvrir la console navigateur
2. Vérifier les erreurs JavaScript
3. Confirmer que Alpine.js est chargé

### **Les notifications navigateur ne fonctionnent pas ?**

1. Vérifier la permission du navigateur : `Settings > Privacy > Notifications`
2. Demander la permission manuellement dans la console :
```javascript
Notification.requestPermission()
```

## 📊 Performance

- **Intervalle de détection SSE** : 2 secondes (configurable dans `views_sse.py`)
- **Notifications en mémoire par client** : ~1KB
- **Reconnexion automatique** : Après 5 secondes en cas d'erreur
- **Impact serveur** : Minimal (1 thread par connexion SSE)

## 🔒 Sécurité

- ✅ Authentification requise pour tous les endpoints
- ✅ Vérification CSRF sur les POST
- ✅ Un utilisateur ne peut marquer QUE ses propres notifications
- ✅ Seuls les admins peuvent créer des notifications

## 🎯 Prochaines Améliorations (Optionnelles)

- [ ] WebSockets avec Django Channels (plus performant que SSE)
- [ ] Notifications groupées ("Vous avez 5 nouvelles notifications")
- [ ] Son de notification personnalisé
- [ ] Filtrage des notifications par catégorie
- [ ] API REST complète pour les notifications
- [ ] Support des images dans les notifications

---

**💡 Astuce** : Pour tester le système en local, ouvrez deux navigateurs :
1. Navigateur 1 : Connecté comme Admin
2. Navigateur 2 : Connecté comme Élève
3. Envoyez une notification depuis l'admin et observez-la apparaître instantanément dans le navigateur de l'élève !
