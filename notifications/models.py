from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('INSCRIPTION', 'Inscription'),
        ('BULLETIN', 'Bulletin Disponible'),
        ('APPROBATION', 'Approbation Requise'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255, default='Notification')
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='INSCRIPTION')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"

class EmailQueue(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'pending', 'En attente'
        ENVOYE = 'sent', 'Envoyé'
        ERREUR = 'error', 'Erreur'

    destinataire = models.EmailField()
    sujet = models.CharField(max_length=255)
    corps_texte = models.TextField(blank=True, default='')
    corps_html = models.TextField(blank=True, default='')
    piece_jointe = models.FileField(upload_to='email_attachments/', blank=True, null=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    tentatives = models.IntegerField(default=0)
    erreur = models.TextField(blank=True, default='')
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class GlobalAnnouncement(models.Model):
    titre = models.CharField(max_length=255)
    message = models.TextField()
    type_alerte = models.CharField(max_length=50)
    est_actif = models.BooleanField(default=True)
    date_expiration = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
