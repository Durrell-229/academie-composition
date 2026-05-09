import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser
from .services import RealtimeService

logger = logging.getLogger(__name__)

class ExamRoomConsumer(AsyncWebsocketConsumer):
    """Consumer pour salle d'examen en temps réel"""
    
    async def connect(self):
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']
        self.user = self.scope['user']
        self.room_group_name = f'exam_{self.exam_id}'
        
        # Rejoindre la salle
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notifier les autres participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'message': f'{self.user.get_full_name()} a rejoint la salle'
            }
        )
        
        logger.info(f"User {self.user.id} joined exam room {self.exam_id}")
    
    async def disconnect(self, close_code):
        # Quitter la salle
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notifier les autres participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'message': f'{self.user.get_full_name()} a quitté la salle'
            }
        )
        
        logger.info(f"User {self.user.id} left exam room {self.exam_id}")
    
    async def receive(self, text_data):
        """Recevoir et traiter les messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'timer_update':
                # Mise à jour du timer
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'timer_update',
                        'time_remaining': data.get('time_remaining'),
                        'status': data.get('status')
                    }
                )
            
            elif message_type == 'submission':
                # Soumission de copie
                await self.handle_submission(data)
            
            elif message_type == 'chat_message':
                # Message chat
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'user_id': self.user.id,
                        'user_name': self.user.get_full_name(),
                        'message': data.get('message')
                    }
                )
            
            elif message_type == 'anti_cheat_alert':
                # Alerte anti-triche
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'anti_cheat_alert',
                        'user_id': data.get('user_id'),
                        'alert_type': data.get('alert_type'),
                        'timestamp': data.get('timestamp')
                    }
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def handle_submission(self, data):
        """Gérer la soumission de copie"""
        submission_data = {
            'type': 'submission',
            'user_id': self.user.id,
            'user_name': self.user.get_full_name(),
            'timestamp': data.get('timestamp'),
            'files_count': data.get('files_count', 0)
        }
        
        # Notifier le professeur
        await self.channel_layer.group_send(
            self.room_group_name,
            submission_data
        )
        
        # Déclencher la correction automatique en temps réel
        await self.trigger_realtime_correction(data)
    
    async def trigger_realtime_correction(self, data):
        """Déclencher la correction automatique en temps réel"""
        try:
            from corrections.correction_with_corrige_type import correction_with_corrige_service
            from compositions.models import CompositionSession
            
            session = await database_sync_to_async(CompositionSession.objects.get)(
                id=data.get('session_id')
            )
            
            # Correction en temps réel
            result = await database_sync_to_async(correction_with_corrige_service.correct_student_copy)(
                session,
                data.get('files', []),
                data.get('text_response', '')
            )
            
            # Notifier le résultat
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'correction_result',
                    'user_id': self.user.id,
                    'result': result
                }
            )
            
        except Exception as e:
            logger.error(f"Error in realtime correction: {e}")
    
    async def timer_update(self, event):
        """Mise à jour du timer pour tous les clients"""
        await self.send(text_data=json.dumps({
            'type': 'timer_update',
            'time_remaining': event['time_remaining'],
            'status': event['status']
        }))
    
    async def chat_message(self, event):
        """Message chat pour tous les clients"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'message': event['message']
        }))
    
    async def anti_cheat_alert(self, event):
        """Alerte anti-triche"""
        await self.send(text_data=json.dumps({
            'type': 'anti_cheat_alert',
            'user_id': event['user_id'],
            'alert_type': event['alert_type'],
            'timestamp': event['timestamp']
        }))
    
    async def user_joined(self, event):
        """Notification utilisateur rejoint"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'message': event['message']
        }))
    
    async def user_left(self, event):
        """Notification utilisateur parti"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'message': event['message']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer pour notifications en temps réel"""
    
    async def connect(self):
        self.user = self.scope['user']
        self.notification_group = f'user_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"User {self.user.id} connected to notifications")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.notification_group,
            self.channel_name
        )
        
        logger.info(f"User {self.user.id} disconnected from notifications")
    
    async def receive(self, text_data):
        """Marquer les notifications comme lues"""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'mark_read':
                await self.mark_notifications_read(data.get('notification_ids', []))
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
    
    async def notification_send(self, event):
        """Envoyer une notification"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def mark_notifications_read(self, notification_ids):
        """Marquer les notifications comme lues"""
        from notifications.models import Notification
        Notification.objects.filter(
            id__in=notification_ids,
            recipient=self.user
        ).update(read=True)


class BulletinUpdateConsumer(AsyncWebsocketConsumer):
    """Consumer pour mises à jour de bulletins en temps réel"""
    
    async def connect(self):
        self.user = self.scope['user']
        self.bulletin_group = f'bulletin_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.bulletin_group,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"User {self.user.id} connected to bulletin updates")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.bulletin_group,
            self.channel_name
        )
    
    async def bulletin_update(self, event):
        """Mise à jour de bulletin"""
        await self.send(text_data=json.dumps({
            'type': 'bulletin_update',
            'bulletin': event['bulletin']
        }))


class DashboardConsumer(AsyncWebsocketConsumer):
    """Consumer pour les mises à jour temps réel des dashboards"""
    
    async def connect(self):
        """Connexion au WebSocket"""
        self.user = self.scope["user"]
        
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        self.user_group_name = f"user_{self.user.id}"
        self.role_group_name = f"role_{self.user.role}"
        
        # Rejoindre les groupes de l'utilisateur et de son rôle
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_add(
            self.role_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Utilisateur {self.user.username} connecté au dashboard temps réel")
        
        # Envoyer les données initiales
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        """Déconnexion du WebSocket"""
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_discard(
            self.role_group_name,
            self.channel_name
        )
        
        logger.info(f"Utilisateur {self.user.username} déconnecté du dashboard temps réel")
    
    async def send_initial_data(self):
        """Envoyer les données initiales du dashboard"""
        try:
            from accounts.views import dashboard_view
            from django.http import HttpRequest
            
            # Créer une requête factice
            request = HttpRequest()
            request.user = self.user
            
            # Obtenir les données du dashboard
            context = await database_sync_to_async(dashboard_view)(request)
            
            # Envoyer les données initiales
            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'data': context
            }))
            
        except Exception as e:
            logger.error(f"Erreur envoi données initiales: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Erreur lors du chargement des données'
            }))
    
    async def dashboard_update(self, event):
        """Recevoir les mises à jour du dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'update_type': event['update_type'],
            'data': event['data']
        }))
    
    async def notification_new(self, event):
        """Nouvelle notification"""
        await self.send(text_data=json.dumps({
            'type': 'notification_new',
            'data': event['data']
        }))
    
    async def exam_status_changed(self, event):
        """Changement de statut d'un examen"""
        await self.send(text_data=json.dumps({
            'type': 'exam_status_changed',
            'data': event['data']
        }))
    
    async def correction_completed(self, event):
        """Correction terminée"""
        await self.send(text_data=json.dumps({
            'type': 'correction_completed',
            'data': event['data']
        }))
    
    async def xp_updated(self, event):
        """XP mis à jour"""
        await self.send(text_data=json.dumps({
            'type': 'xp_updated',
            'data': event['data']
        }))
    
    async def badge_earned(self, event):
        """Badge obtenu"""
        await self.send(text_data=json.dumps({
            'type': 'badge_earned',
            'data': event['data']
        }))
    
    async def user_online_status(self, event):
        """Statut de connexion des utilisateurs"""
        await self.send(text_data=json.dumps({
            'type': 'user_online_status',
            'data': event['data']
        }))


class GlobalStatsConsumer(AsyncWebsocketConsumer):
    """Consumer pour les statistiques globales en temps réel (admin)"""
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if not (self.user.is_staff or self.user.role == 'admin'):
            await self.close()
            return
        
        self.admin_group_name = "admin_dashboard"
        
        await self.channel_layer.group_add(
            self.admin_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Admin {self.user.username} connecté au dashboard global")
        
        # Envoyer les stats initiales
        await self.send_initial_stats()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.admin_group_name,
            self.channel_name
        )
    
    async def send_initial_stats(self):
        """Envoyer les statistiques initiales"""
        try:
            from accounts.views import dashboard_view
            from django.http import HttpRequest
            
            request = HttpRequest()
            request.user = self.user
            
            # Obtenir les données admin
            context = await database_sync_to_async(dashboard_view)(request)
            
            await self.send(text_data=json.dumps({
                'type': 'initial_stats',
                'data': context
            }))
            
        except Exception as e:
            logger.error(f"Erreur envoi stats initiales: {e}")
    
    async def global_stats_update(self, event):
        """Mise à jour des statistiques globales"""
        await self.send(text_data=json.dumps({
            'type': 'global_stats_update',
            'data': event['data']
        }))
    
    async def system_alert(self, event):
        """Alerte système"""
        await self.send(text_data=json.dumps({
            'type': 'system_alert',
            'data': event['data']
        }))
