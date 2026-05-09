/**
 * Dashboard Realtime System
 * Gère les mises à jour temps réel pour tous les dashboards
 */

class DashboardRealtime {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.userId = null;
        this.userRole = null;
        this.debugMode = true; // Activer le debug pour diagnostiquer
        
        this.init();
    }
    
    init() {
        // Récupérer les infos utilisateur depuis le template
        this.userId = document.body.dataset.userId || window.currentUser?.id;
        this.userRole = document.body.dataset.userRole || window.currentUser?.role;
        
        if (!this.userId) {
            console.warn('Dashboard Realtime: userId non trouvé');
            return;
        }
        
        this.connect();
        this.setupEventListeners();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/realtime/ws/dashboard/`;
        
        if (this.debugMode) {
            console.log('Dashboard Realtime: Tentative de connexion vers', wsUrl);
        }
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                if (this.debugMode) {
                    console.log('Dashboard Realtime: WebSocket connecté avec succès');
                }
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.showConnectionStatus(true);
                
                // Envoyer les infos utilisateur pour s'inscrire au bon canal
                this.sendUserInfo();
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (this.debugMode) {
                        console.log('Dashboard Realtime: Message reçu', data);
                    }
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Dashboard Realtime: Erreur parsing message', error, event.data);
                }
            };
            
            this.socket.onclose = (event) => {
                if (this.debugMode) {
                    console.log('Dashboard Realtime: WebSocket déconnecté', event.code, event.reason);
                }
                this.isConnected = false;
                this.showConnectionStatus(false);
                
                // Ne pas tenter de reconnexion si c'est une déconnexion normale
                if (event.code !== 1000) {
                    this.attemptReconnect();
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('Dashboard Realtime: Erreur WebSocket', error);
                this.isConnected = false;
                this.showConnectionStatus(false);
                
                if (this.debugMode) {
                    console.log('Dashboard Realtime: Erreur de connexion, nouvelle tentative dans', this.reconnectDelay * this.reconnectAttempts, 'ms');
                }
                this.attemptReconnect();
            };
            
        } catch (error) {
            console.error('Dashboard Realtime: Erreur de connexion WebSocket', error);
            this.isConnected = false;
            this.showConnectionStatus(false);
            this.attemptReconnect();
        }
    }
    
    sendUserInfo() {
        // Envoyer les informations utilisateur au serveur
        if (this.socket && this.isConnected && this.userId) {
            const userInfo = {
                type: 'user_info',
                user_id: this.userId,
                user_role: this.userRole,
                timestamp: new Date().toISOString()
            };
            this.socket.send(JSON.stringify(userInfo));
            if (this.debugMode) {
                console.log('Dashboard Realtime: Infos utilisateur envoyées', userInfo);
            }
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Dashboard Realtime: Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Dashboard Realtime: Nombre maximal de tentatives de reconnexion atteint');
            this.showConnectionError();
        }
    }
    
    handleMessage(data) {
        console.log('Dashboard Realtime: Message reçu', data);
        
        switch (data.type) {
            case 'initial_data':
                this.handleInitialData(data.data);
                break;
            case 'dashboard_update':
                this.handleDashboardUpdate(data.update_type, data.data);
                break;
            case 'notification_new':
                this.handleNewNotification(data.data);
                break;
            case 'exam_status_changed':
                this.handleExamStatusChange(data.data);
                break;
            case 'correction_completed':
                this.handleCorrectionCompleted(data.data);
                break;
            case 'xp_updated':
                this.handleXPUpdated(data.data);
                break;
            case 'badge_earned':
                this.handleBadgeEarned(data.data);
                break;
            case 'user_online_status':
                this.handleUserOnlineStatus(data.data);
                break;
            case 'global_stats_update':
                this.handleGlobalStatsUpdate(data.update_type, data.data);
                break;
            case 'system_alert':
                this.handleSystemAlert(data.data);
                break;
            case 'error':
                this.handleError(data.message);
                break;
            default:
                console.warn('Dashboard Realtime: Type de message non géré', data.type);
        }
    }
    
    handleInitialData(data) {
        // Mettre à jour les éléments du dashboard avec les données initiales
        this.updateStatsCards(data);
        this.updateNotifications(data);
        this.updateRecentActivity(data);
        
        // Afficher une animation de chargement terminé
        this.hideLoadingOverlay();
    }
    
    handleDashboardUpdate(updateType, data) {
        switch (updateType) {
            case 'stats_updated':
                this.updateStatsCards(data);
                break;
            case 'new_result':
                this.addNewResult(data);
                break;
            case 'exam_assigned':
                this.addNewExam(data);
                break;
            case 'notification_count':
                this.updateNotificationCount(data);
                break;
            default:
                this.refreshDashboard();
        }
    }
    
    handleNewNotification(notification) {
        // Ajouter la notification à la liste
        this.addNotificationToList(notification);
        
        // Mettre à jour le compteur
        this.updateNotificationCount({ count: notification.unread_count });
        
        // Afficher une notification toast
        this.showToast(notification.title, notification.message, notification.type);
    }
    
    handleExamStatusChange(examData) {
        // Mettre à jour le statut des examens
        this.updateExamStatus(examData);
        
        // Si examen en cours, afficher une alerte
        if (examData.status === 'en_cours') {
            this.showActiveExamAlert(examData);
        }
    }
    
    handleCorrectionCompleted(correctionData) {
        // Mettre à jour les résultats
        this.updateResultsList(correctionData);
        
        // Mettre à jour les statistiques
        this.updateStatsCards(correctionData.stats);
        
        // Si c'est la correction de l'utilisateur actuel
        if (correctionData.student_id == this.userId) {
            this.showCorrectionNotification(correctionData);
        }
    }
    
    handleXPUpdated(xpData) {
        // Mettre à jour l'affichage de l'XP
        this.updateXPDisplay(xpData);
        
        // Si level up, afficher une animation spéciale
        if (xpData.level_up) {
            this.showLevelUpAnimation(xpData);
        }
    }
    
    handleBadgeEarned(badgeData) {
        // Ajouter le nouveau badge à la collection
        this.addBadgeToCollection(badgeData);
        
        // Afficher une animation d'obtention de badge
        this.showBadgeEarnedAnimation(badgeData);
    }
    
    handleUserOnlineStatus(userData) {
        // Mettre à jour le statut de connexion des utilisateurs
        this.updateUserOnlineStatus(userData);
    }
    
    handleGlobalStatsUpdate(updateType, data) {
        // Pour les admins, mettre à jour les statistiques globales
        if (this.userRole === 'admin') {
            this.updateGlobalStats(data);
        }
    }
    
    handleSystemAlert(alertData) {
        // Afficher une alerte système
        this.showSystemAlert(alertData);
    }
    
    handleError(message) {
        console.error('Dashboard Realtime: Erreur serveur', message);
        this.showToast('Erreur', message, 'error');
    }
    
    // Méthodes de mise à jour UI
    updateStatsCards(data) {
        // Mettre à jour les cartes de statistiques avec animation
        // Adapter aux nouveaux designs premium
        const cards = document.querySelectorAll('[data-stat]');
        cards.forEach(card => {
            const statName = card.dataset.stat;
            if (data[statName] !== undefined) {
                this.animateValue(card, data[statName]);
            }
        });
        
        // Mettre à jour les KPI premium avec les nouvelles classes
        const kpiCards = document.querySelectorAll('.group.relative');
        kpiCards.forEach(card => {
            const statElement = card.querySelector('[data-stat]');
            if (statElement) {
                const statName = statElement.dataset.stat;
                if (data[statName] !== undefined) {
                    this.animateValue(statElement, data[statName]);
                }
            }
        });
    }
    
    updateNotifications(data) {
        // Mettre à jour la liste des notifications
        const container = document.getElementById('notifications-list');
        if (container && data.notifications) {
            container.innerHTML = '';
            data.notifications.forEach(notification => {
                this.addNotificationToList(notification);
            });
        }
    }
    
    updateRecentActivity(data) {
        // Mettre à jour l'activité récente
        const container = document.getElementById('recent-activity');
        if (container && data.recent_activity) {
            container.innerHTML = '';
            data.recent_activity.forEach(activity => {
                this.addActivityItem(activity);
            });
        }
    }
    
    addNewResult(result) {
        // Ajouter un nouveau résultat à la liste
        const container = document.getElementById('results-list');
        if (container) {
            const resultElement = this.createResultElement(result);
            container.insertBefore(resultElement, container.firstChild);
            
            // Limiter le nombre de résultats affichés
            while (container.children.length > 10) {
                container.removeChild(container.lastChild);
            }
        }
    }
    
    addNewExam(exam) {
        // Ajouter un nouvel examen à la liste
        const container = document.getElementById('exams-list');
        if (container) {
            const examElement = this.createExamElement(exam);
            container.insertBefore(examElement, container.firstChild);
            
            // Animer l'ajout
            examElement.classList.add('animate-in');
        }
    }
    
    updateNotificationCount(data) {
        // Mettre à jour le compteur de notifications
        const badges = document.querySelectorAll('.notification-badge');
        badges.forEach(badge => {
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        });
    }
    
    updateExamStatus(examData) {
        // Mettre à jour le statut d'un examen spécifique
        const examElements = document.querySelectorAll(`[data-exam-id="${examData.id}"]`);
        examElements.forEach(element => {
            const statusElement = element.querySelector('.exam-status');
            if (statusElement) {
                statusElement.textContent = examData.status;
                statusElement.className = `exam-status status-${examData.status}`;
            }
        });
    }
    
    updateResultsList(correctionData) {
        // Mettre à jour la liste des résultats
        const resultElements = document.querySelectorAll(`[data-result-id="${correctionData.id}"]`);
        resultElements.forEach(element => {
            this.updateResultElement(element, correctionData);
        });
    }
    
    updateXPDisplay(xpData) {
        // Mettre à jour l'affichage de l'XP
        const xpElements = document.querySelectorAll('[data-xp]');
        xpElements.forEach(element => {
            if (xpData.total_xp !== undefined) {
                this.animateValue(element, xpData.total_xp);
            }
        });
        
        const levelElements = document.querySelectorAll('[data-level]');
        levelElements.forEach(element => {
            if (xpData.level !== undefined) {
                element.textContent = xpData.level;
            }
        });
    }
    
    addBadgeToCollection(badgeData) {
        // Ajouter un badge à la collection
        const container = document.getElementById('badges-collection');
        if (container) {
            const badgeElement = this.createBadgeElement(badgeData);
            container.appendChild(badgeElement);
        }
    }
    
    // Méthodes d'animation et affichage
    animateValue(element, newValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const difference = newValue - currentValue;
        const duration = 500;
        const steps = 20;
        const stepValue = difference / steps;
        let currentStep = 0;
        
        if (this.debugMode) {
            console.log(`Dashboard Realtime: Animation ${element.dataset.stat || 'element'} de ${currentValue} vers ${newValue}`);
        }
        
        const timer = setInterval(() => {
            currentStep++;
            const value = Math.round(currentValue + (stepValue * currentStep));
            element.textContent = value;
            
            if (currentStep >= steps) {
                clearInterval(timer);
                element.textContent = newValue;
                
                // Ajouter une classe d'animation terminée
                element.classList.add('animate-complete');
                setTimeout(() => {
                    element.classList.remove('animate-complete');
                }, 300);
            }
        }, duration / steps);
    }
    
    showToast(title, message, type = 'info') {
        // Créer et afficher une notification toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-in`;
        toast.innerHTML = `
            <div class="toast-content">
                <strong>${title}</strong>
                <p>${message}</p>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
    
    showConnectionStatus(isConnected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = isConnected ? 'status-connected' : 'status-disconnected';
            statusElement.title = isConnected ? 'Connecté en temps réel' : 'Déconnecté';
        }
    }
    
    showConnectionError() {
        this.showToast('Erreur de connexion', 'Impossible de se connecter au temps réel', 'error');
    }
    
    showActiveExamAlert(examData) {
        // Afficher une alerte pour examen actif
        const alertElement = document.getElementById('active-exam-alert');
        if (alertElement) {
            alertElement.classList.remove('hidden');
            alertElement.querySelector('.exam-title').textContent = examData.title;
            alertElement.querySelector('.exam-time').textContent = `Se termine à ${examData.end_time}`;
        }
    }
    
    showCorrectionNotification(correctionData) {
        this.showToast(
            'Nouvelle correction disponible',
            `Votre copie a été corrigée: ${correctionData.grade}/20`,
            'success'
        );
    }
    
    showLevelUpAnimation(xpData) {
        // Afficher une animation de level up
        const animation = document.createElement('div');
        animation.className = 'level-up-animation';
        animation.innerHTML = `
            <div class="level-up-content">
                <h2>🎉 Niveau ${xpData.level} !</h2>
                <p>Félicitations, vous avez atteint un nouveau niveau !</p>
            </div>
        `;
        
        document.body.appendChild(animation);
        
        setTimeout(() => {
            animation.remove();
        }, 3000);
    }
    
    showBadgeEarnedAnimation(badgeData) {
        // Afficher une animation d'obtention de badge
        const animation = document.createElement('div');
        animation.className = 'badge-earned-animation';
        animation.innerHTML = `
            <div class="badge-earned-content">
                <div class="badge-icon">${badgeData.icon}</div>
                <h2>Badge obtenu !</h2>
                <p>${badgeData.name}</p>
            </div>
        `;
        
        document.body.appendChild(animation);
        
        setTimeout(() => {
            animation.remove();
        }, 3000);
    }
    
    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
    
    refreshDashboard() {
        // Recharger les données du dashboard
        window.location.reload();
    }
    
    setupEventListeners() {
        // Écouter les événements de la page
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Pause des mises à jour quand la page n'est pas visible
                if (this.socket && this.isConnected) {
                    this.socket.send(JSON.stringify({ type: 'pause' }));
                }
            } else {
                // Reprendre les mises à jour quand la page devient visible
                if (this.socket && this.isConnected) {
                    this.socket.send(JSON.stringify({ type: 'resume' }));
                }
            }
        });
        
        // Nettoyage à la fermeture de la page
        window.addEventListener('beforeunload', () => {
            if (this.socket) {
                this.socket.close();
            }
        });
        
        // Ajouter un test de connexion manuel
        this.addConnectionTest();
    }
    
    addConnectionTest() {
        // Ajouter un bouton de test pour diagnostiquer
        const testButton = document.createElement('button');
        testButton.textContent = '🔄 Test Temps Réel';
        testButton.className = 'fixed bottom-4 right-4 z-50 bg-primary text-white px-3 py-2 rounded-lg text-sm hover:bg-primary/80 transition-all duration-300 shadow-lg';
        testButton.style.cssText = 'bottom: 80px; right: 20px;';
        testButton.onclick = () => {
            this.testConnection();
        };
        
        document.body.appendChild(testButton);
        
        if (this.debugMode) {
            console.log('Dashboard Realtime: Bouton de test ajouté');
        }
    }
    
    testConnection() {
        if (this.debugMode) {
            console.log('Dashboard Realtime: Test de connexion manuel');
        }
        
        if (this.socket && this.isConnected) {
            // Envoyer un message de test
            const testMessage = {
                type: 'test_connection',
                user_id: this.userId,
                timestamp: new Date().toISOString()
            };
            this.socket.send(JSON.stringify(testMessage));
            
            this.showToast('Test', 'Message de test envoyé', 'info');
        } else {
            this.showToast('Erreur', 'WebSocket non connecté', 'error');
        }
    }
    
    // Méthodes utilitaires pour créer des éléments
    createResultElement(result) {
        const element = document.createElement('div');
        element.className = 'result-item animate-in';
        element.dataset.resultId = result.id;
        element.innerHTML = `
            <div class="result-header">
                <span class="result-title">${result.exam_title}</span>
                <span class="result-grade ${result.grade >= 10 ? 'success' : 'warning'}">${result.grade}/20</span>
            </div>
            <div class="result-meta">
                <span class="result-date">${new Date(result.created_at).toLocaleDateString()}</span>
                <span class="result-matiere">${result.matiere}</span>
            </div>
        `;
        return element;
    }
    
    createExamElement(exam) {
        const element = document.createElement('div');
        element.className = 'exam-item animate-in';
        element.dataset.examId = exam.id;
        element.innerHTML = `
            <div class="exam-header">
                <span class="exam-title">${exam.title}</span>
                <span class="exam-status status-${exam.status}">${exam.status}</span>
            </div>
            <div class="exam-meta">
                <span class="exam-matiere">${exam.matiere}</span>
                <span class="exam-date">${new Date(exam.date_debut).toLocaleDateString()}</span>
            </div>
        `;
        return element;
    }
    
    createBadgeElement(badge) {
        const element = document.createElement('div');
        element.className = 'badge-item';
        element.innerHTML = `
            <div class="badge-icon">${badge.icon}</div>
            <div class="badge-info">
                <h4>${badge.name}</h4>
                <p>${badge.description}</p>
            </div>
        `;
        return element;
    }
    
    addNotificationToList(notification) {
        const container = document.getElementById('notifications-list');
        if (container) {
            const element = document.createElement('div');
            element.className = 'notification-item animate-in';
            element.innerHTML = `
                <div class="notification-content">
                    <strong>${notification.title}</strong>
                    <p>${notification.message}</p>
                    <span class="notification-time">${new Date(notification.created_at).toLocaleTimeString()}</span>
                </div>
            `;
            container.insertBefore(element, container.firstChild);
        }
    }
    
    addActivityItem(activity) {
        const container = document.getElementById('recent-activity');
        if (container) {
            const element = document.createElement('div');
            element.className = 'activity-item animate-in';
            element.innerHTML = `
                <div class="activity-icon">${activity.icon}</div>
                <div class="activity-content">
                    <p>${activity.description}</p>
                    <span class="activity-time">${new Date(activity.timestamp).toLocaleTimeString()}</span>
                </div>
            `;
            container.appendChild(element);
        }
    }
}

// Initialiser le système temps réel quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/dashboard')) {
        window.dashboardRealtime = new DashboardRealtime();
        console.log('Dashboard Realtime: Initialisé automatiquement');
    }
});

// Exporter pour utilisation dans d'autres scripts
window.DashboardRealtime = DashboardRealtime;
