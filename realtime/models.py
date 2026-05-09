from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class RealtimeNotification(models.Model):
    """Modèle pour les notifications temps réel"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='realtime_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification temps réel"
        verbose_name_plural = "Notifications temps réel"
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"