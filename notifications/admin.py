from django.contrib import admin
from .models import Notification, EmailQueue, GlobalAnnouncement


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('recipient__email', 'title', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations', {
            'fields': ('recipient', 'title', 'message', 'type', 'is_read')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Marquer les notifications comme lues."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = 'Marquer comme lu'
    
    def mark_as_unread(self, request, queryset):
        """Marquer les notifications comme non lues."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme non lue(s).')
    mark_as_unread.short_description = 'Marquer comme non lu'


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'sujet', 'statut', 'tentatives', 'created_at', 'sent_at')
    list_filter = ('statut', 'created_at')
    search_fields = ('destinataire', 'sujet')
    readonly_fields = ('created_at', 'sent_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Email', {
            'fields': ('destinataire', 'sujet', 'corps_texte', 'corps_html', 'piece_jointe')
        }),
        ('Statut', {
            'fields': ('statut', 'tentatives', 'erreur', 'sent_at')
        }),
    )


@admin.register(GlobalAnnouncement)
class GlobalAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_alerte', 'est_actif', 'date_expiration', 'created_at')
    list_filter = ('type_alerte', 'est_actif')
    search_fields = ('titre', 'message')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Annonce', {
            'fields': ('titre', 'message', 'type_alerte', 'est_actif', 'date_expiration')
        }),
    )
