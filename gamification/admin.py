from django.contrib import admin
from .models import Badge, UserBadge, GlobalLeaderboard, XPAction, StreakRecord


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'icone', 'categorie', 'points', 'rarete', 'est_actif')
    list_filter = ('categorie', 'rarete', 'est_actif')
    search_fields = ('nom', 'description')
    
    fieldsets = (
        ('Badge', {
            'fields': ('nom', 'description', 'icone', 'categorie')
        }),
        ('Configuration', {
            'fields': ('points', 'rarete', 'condition_obtention', 'est_actif')
        }),
    )


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'obtenu_at', 'est_nouveau')
    list_filter = ('est_nouveau', 'obtenu_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'badge__nom')
    readonly_fields = ('obtenu_at',)
    date_hierarchy = 'obtenu_at'
    
    fieldsets = (
        ('Attribution', {
            'fields': ('user', 'badge', 'est_nouveau', 'obtenu_at')
        }),
    )


@admin.register(GlobalLeaderboard)
class GlobalLeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'periode', 'rang_mondial', 'rang_national', 'score_total', 'niveau', 'pays')
    list_filter = ('periode', 'pays', 'date_periode')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('updated_at',)
    date_hierarchy = 'date_periode'
    
    fieldsets = (
        ('Classement', {
            'fields': ('user', 'periode', 'date_periode', 'pays')
        }),
        ('Scores', {
            'fields': ('rang_mondial', 'rang_national', 'score_total', 'points_xp', 'niveau')
        }),
        ('Statistiques', {
            'fields': ('nb_compositions', 'nb_excellentes', 'moyenne', 'streak_jours')
        }),
        ('Métadonnées', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(XPAction)
class XPActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'points_gagnes', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Action XP', {
            'fields': ('user', 'action', 'points_gagnes', 'created_at')
        }),
    )
    
    actions = ['recalculate_xp']
    
    def recalculate_xp(self, request, queryset):
        """Placeholder for XP recalculation."""
        self.message_user(request, f'{queryset.count()} action(s) sélectionnée(s).')
    recalculate_xp.short_description = 'Recalculer XP'


@admin.register(StreakRecord)
class StreakRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_activity_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('last_activity_date',)
    
    fieldsets = (
        ('Série', {
            'fields': ('user', 'current_streak', 'longest_streak', 'last_activity_date')
        }),
    )
