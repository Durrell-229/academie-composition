from django.contrib import admin
from .models import Bareme


@admin.register(Bareme)
class BaremeAdmin(admin.ModelAdmin):
    list_display = ['exam', 'titre', 'total_points', 'cree_par', 'created_at']
    list_filter = ['total_points']
    search_fields = ['exam__titre', 'titre']
    readonly_fields = ['id', 'created_at', 'updated_at']
