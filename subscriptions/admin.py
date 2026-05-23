"""
Admin pour l'application Subscriptions — plans et abonnements utilisateurs génériques.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import SubscriptionPlan, UserSubscription


# ═══════════════════════════════════════════════════════════════
# PLANS D'ABONNEMENT GÉNÉRIQUES
# ═══════════════════════════════════════════════════════════════

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'afficher_niveau', 'afficher_prix',
        'duration_days', 'is_popular', 'is_active',
    ]
    list_filter = ['level', 'is_active', 'is_popular']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'is_popular']

    fieldsets = (
        (_('Plan'), {
            'fields': ('name', 'level', 'price', 'duration_days')
        }),
        (_('Description & Avantages'), {
            'fields': ('description', 'features')
        }),
        (_('Mise en avant'), {
            'fields': ('is_popular', 'is_active')
        }),
    )

    LEVEL_COLORS = {
        'FREE': '#6b7280',
        'PRO': '#3b82f6',
        'ELITE': '#8b5cf6',
    }

    @admin.display(description=_('Niveau'))
    def afficher_niveau(self, obj):
        color = self.LEVEL_COLORS.get(obj.level, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:11px;font-weight:700">{}</span>',
            color, obj.get_level_display()
        )

    @admin.display(description=_('Prix'))
    def afficher_prix(self, obj):
        if obj.price == 0:
            return format_html('<span style="color:#16a34a;font-weight:700">Gratuit</span>')
        return format_html('<strong>{:,.0f} FCFA / mois</strong>', obj.price)


# ═══════════════════════════════════════════════════════════════
# ABONNEMENTS UTILISATEURS
# ═══════════════════════════════════════════════════════════════

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'plan', 'start_date',
        'afficher_fin', 'afficher_statut', 'afficher_expire',
    ]
    list_filter = ['plan__level', 'is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['start_date']
    date_hierarchy = 'start_date'

    fieldsets = (
        (_('Utilisateur & Plan'), {
            'fields': ('user', 'plan', 'is_active')
        }),
        (_('Période'), {
            'fields': ('start_date', 'end_date')
        }),
    )

    @admin.display(description=_('Fin d\'abonnement'))
    def afficher_fin(self, obj):
        if not obj.end_date:
            return format_html('<span style="color:#16a34a;font-weight:700">Illimité</span>')
        color = '#dc2626' if obj.is_expired else '#16a34a'
        return format_html(
            '<span style="color:{}">{}</span>',
            color,
            obj.end_date.strftime('%d/%m/%Y %H:%M')
        )

    @admin.display(description=_('Statut'))
    def afficher_statut(self, obj):
        if obj.is_active and not obj.is_expired:
            return format_html(
                '<span style="background:#16a34a;color:#fff;padding:2px 8px;'
                'border-radius:12px;font-size:11px;font-weight:600">Actif</span>'
            )
        return format_html(
            '<span style="background:#dc2626;color:#fff;padding:2px 8px;'
            'border-radius:12px;font-size:11px;font-weight:600">Inactif</span>'
        )

    @admin.display(description=_('Expiré'), boolean=True)
    def afficher_expire(self, obj):
        return obj.is_expired
