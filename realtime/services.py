import logging
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from notifications.models import Notification

logger = logging.getLogger(__name__)

class RealtimeService:
    """Service pour fonctionnalités temps réel"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_notification(self, user_id, notification_data):
        """Envoyer une notification en temps réel"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'user_{user_id}',
                {
                    'type': 'notification_send',
                    'notification': notification_data
                }
            )
            
            logger.info(f"Notification sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def broadcast_to_exam_room(self, exam_id, message_type, data):
        """Diffuser un message à tous les participants d'une salle d'examen"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'exam_{exam_id}',
                {
                    'type': message_type,
                    **data
                }
            )
            
            logger.info(f"Message broadcast to exam room {exam_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting to exam room: {e}")
            return False
    
    def send_dashboard_update(self, user_id, update_type, data):
        """Envoyer une mise à jour au dashboard d'un utilisateur"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"user_{user_id}",
                {
                    'type': 'dashboard_update',
                    'update_type': update_type,
                    'data': data
                }
            )
            logger.info(f"Mise à jour dashboard envoyée à l'utilisateur {user_id}: {update_type}")
            return True
        except Exception as e:
            logger.error(f"Erreur envoi mise à jour dashboard: {e}")
            return False
    
    def send_role_update(self, role, update_type, data):
        """Envoyer une mise à jour à tous les utilisateurs d'un rôle"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"role_{role}",
                {
                    'type': 'dashboard_update',
                    'update_type': update_type,
                    'data': data
                }
            )
            logger.info(f"Mise à jour rôle {role} envoyée: {update_type}")
            return True
        except Exception as e:
            logger.error(f"Erreur envoi mise à jour rôle: {e}")
            return False
    
    def send_global_update(self, update_type, data):
        """Envoyer une mise à jour globale à tous les admins"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                "admin_dashboard",
                {
                    'type': 'global_stats_update',
                    'update_type': update_type,
                    'data': data
                }
            )
            logger.info(f"Mise à jour globale envoyée: {update_type}")
            return True
        except Exception as e:
            logger.error(f"Erreur envoi mise à jour globale: {e}")
            return False
    
    def send_correction_completed(self, correction_data):
        """Notifier la complétion d'une correction"""
        try:
            # Envoyer à l'élève concerné
            if 'student_id' in correction_data:
                self.send_dashboard_update(
                    correction_data['student_id'], 
                    'correction_completed', 
                    correction_data
                )
            
            # Envoyer au professeur qui a corrigé
            if 'professor_id' in correction_data:
                self.send_dashboard_update(
                    correction_data['professor_id'], 
                    'correction_completed', 
                    correction_data
                )
            
            # Envoyer aux admins pour les stats
            self.send_global_update('correction_completed', correction_data)
            return True
            
        except Exception as e:
            logger.error(f"Erreur notification correction: {e}")
            return False
    
    def send_exam_status_change(self, exam_data):
        """Notifier le changement de statut d'un examen"""
        try:
            # Envoyer à tous les professeurs
            self.send_role_update('professeur', 'exam_status_changed', exam_data)
            
            # Envoyer aux admins
            self.send_global_update('exam_status_changed', exam_data)
            return True
            
        except Exception as e:
            logger.error(f"Erreur notification changement examen: {e}")
            return False
    
    def send_xp_updated(self, user_id, xp_data):
        """Notifier la mise à jour d'XP"""
        try:
            self.send_dashboard_update(user_id, 'xp_updated', xp_data)
            
            # Envoyer aux classements si pertinent
            if xp_data.get('level_up') or xp_data.get('achievement'):
                self.send_role_update('eleve', 'xp_updated', xp_data)
            return True
                
        except Exception as e:
            logger.error(f"Erreur notification XP: {e}")
            return False
    
    def send_timer_update(self, exam_id, time_remaining, status):
        """Mise à jour du timer d'examen"""
        return self.broadcast_to_exam_room(
            exam_id,
            'timer_update',
            {
                'time_remaining': time_remaining,
                'status': status
            }
        )
    
    def send_chat_message(self, exam_id, user_id, user_name, message):
        """Envoyer un message chat dans la salle d'examen"""
        return self.broadcast_to_exam_room(
            exam_id,
            'chat_message',
            {
                'user_id': user_id,
                'user_name': user_name,
                'message': message
            }
        )
    
    def send_anti_cheat_alert(self, exam_id, user_id, alert_type):
        """Envoyer une alerte anti-triche"""
        return self.broadcast_to_exam_room(
            exam_id,
            'anti_cheat_alert',
            {
                'user_id': user_id,
                'alert_type': alert_type,
                'timestamp': async_to_sync(lambda: __import__('django.utils').timezone.now())()
            }
        )
    
    def update_bulletin(self, user_id, bulletin_data):
        """Mise à jour de bulletin en temps réel"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'bulletin_{user_id}',
                {
                    'type': 'bulletin_update',
                    'bulletin': bulletin_data
                }
            )
            
            logger.info(f"Bulletin update sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending bulletin update: {e}")
            return False
    
    def notify_exam_started(self, exam_id, student_ids):
        """Notifier que l'examen a commencé"""
        for student_id in student_ids:
            self.send_notification(
                student_id,
                {
                    'type': 'exam_started',
                    'exam_id': exam_id,
                    'message': 'Votre examen a commencé'
                }
            )
    
    def notify_correction_completed(self, user_id, correction_result):
        """Notifier que la correction est terminée"""
        self.send_notification(
            user_id,
            {
                'type': 'correction_completed',
                'note': correction_result.get('note', 0),
                'message': f'Votre copie a été corrigée. Note: {correction_result.get("note", 0)}/20'
            }
        )
        
        # Mettre à jour le bulletin
        self.update_bulletin(user_id, correction_result)

# Instance globale
realtime_service = RealtimeService()
