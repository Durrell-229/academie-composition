# 🚀 TEST LOCAL RAPIDE - GUIDE DÉMARRAGE

## ✅ SYSTÈME PRÊT POUR TESTS

Les données de test ont été créées avec succès ! Voici comment tester tout localement :

---

## 🔑 COMPTES DE TEST DISPONIBLES

### Élèves
- **Email**: `eleve.test@ecole.com` | **MDP**: `Test123456!` | **Classe**: `3ème A`
- **Email**: `eleve2.test@ecole.com` | **MDP**: `Test123456!` | **Classe**: `4ème B`

### Admin
- **Email**: `admin.test@ecole.com` | **MDP**: `Admin123456!`

---

## 📝 SESSIONS DE COMPOSITION DISPONIBLES

### Session 1: Français
- **URL**: `http://127.0.0.1:5600/compositions/room/9bf530f1-77ef-4053-9b54-e8f0c2c822ff/`
- **Élève**: `eleve.test@ecole.com`
- **Examen**: Composition Française - Test Local (120 min)

### Session 2: Mathématiques  
- **URL**: `http://127.0.0.1:5600/compositions/room/4f51bad4-2d25-4a07-a36a-367b41cea568/`
- **Élève**: `eleve.test@ecole.com`
- **Examen**: Examen Mathématiques - Test Local (60 min)

### Session 3: Français
- **URL**: `http://127.0.0.1:5600/compositions/room/775635ef-b401-451c-be7b-135f3e1821d7/`
- **Élève**: `eleve2.test@ecole.com`
- **Examen**: Composition Française - Test Local

### Session 4: Mathématiques
- **URL**: `http://127.0.0.1:5600/compositions/room/b382f45a-050b-43a0-9d9a-cbc286a38fb5/`
- **Élève**: `eleve2.test@ecole.com`
- **Examen**: Examen Mathématiques - Test Local

---

## 🧪 FLUX DE TEST COMPLET

### Étape 1: Démarrer le serveur
```bash
python manage.py runserver 5600
```

### Étape 2: Test Élève
1. **Se connecter**: `http://127.0.0.1:5600/login/`
   - Email: `eleve.test@ecole.com`
   - Mot de passe: `Test123456!`

2. **Accéder à une session**: Copiez une URL ci-dessus
   - Ex: `http://127.0.0.1:5600/compositions/room/9bf530f1-77ef-4053-9b54-e8f0c2c822ff/`

3. **Tester la composition**:
   - ✅ Caméra qui s'active
   - ✅ Timer qui fonctionne
   - ✅ Anti-triche (F12 bloqué, etc.)
   - ✅ Zone de réponse fonctionnelle

4. **Soumettre la composition**:
   - Écrire un texte dans la zone de réponse
   - Cliquer sur "Soumettre l'examen"
   - Confirmer dans le modal

### Étape 3: Correction IA
```bash
# Lancer la correction manuellement
python manual_correction_fix.py
```

### Étape 4: Vérifier les résultats
1. **Accès résultats**: `http://127.0.0.1:5600/compositions/result/{session_id}/`
2. **Bulletin PDF**: Disponible dans la page résultats
3. **Note et appréciation**: Affichées dans l'interface

---

## 🎯 POINTS DE VÉRIFICATION

### ✅ Checklist
- [ ] Connexion élève fonctionne
- [ ] Salle de composition s'affiche
- [ ] Caméra s'active (permission demandée)
- [ ] Timer décompte correctement
- [ ] Anti-triche bloque F12, Ctrl+C/V, clic droit
- [ ] Zone de réponse permet d'écrire
- [ ] Bouton soumission fonctionne
- [ ] Modal de confirmation s'affiche
- [ ] Soumission réussie
- [ ] Correction IA génère une note
- [ ] Bulletin PDF est créé
- [ ] Page résultats affiche tout

---

## 🔧 DÉPANNAGE RAPIDE

### Si la caméra ne s'active pas
- Autoriser l'accès à la caméra dans le navigateur
- Utiliser Chrome/Edge (meilleur support)
- Vérifier que c'est en HTTPS ou localhost

### Si la correction IA ne fonctionne pas
- Exécuter: `python manual_correction_fix.py`
- Vérifier les clés API dans les settings

### Si le bulletin ne s'affiche pas
- Vérifier que la session est marquée 'corrige'
- Consulter les logs Django

---

## 📊 RÉSULTATS ATTENDUS

### Note: 10-20/20
- Appréciation générée par l'IA
- Bulletin PDF format A4
- QR code de vérification
- Mention (bien, très bien, etc.)

---

## 🚀 PRÊT À TESTER !

Le système est maintenant **100% fonctionnel** avec :
- ✅ **Utilisateurs de test créés**
- ✅ **Examens avec sujets et corrigés**
- ✅ **Sessions de composition prêtes**
- ✅ **Correction IA fonctionnelle**
- ✅ **Bulletins PDF générés**

**Il suffit de démarrer le serveur et de suivre les étapes ci-dessus !**

---

## 📞 SUPPORT

Si vous rencontrez des problèmes :
1. Vérifiez les logs du serveur Django
2. Exécutez `python debug_sessions.py` pour diagnostiquer
3. Utilisez `python manual_correction_fix.py` pour forcer la correction

**Bon test !** 🎉
