"""
Administration pour le cahier de texte
"""

from django.contrib import admin
from .models import SeanceCours, Devoir, Lecon, RenduDevoir, Progression


@admin.register(SeanceCours)
class SeanceCoursAdmin(admin.ModelAdmin):
    list_display = ['titre', 'classe', 'matiere', 'professeur', 'date', 'heure_debut', 'heure_fin', 'is_effectue']
    list_filter = ['matiere', 'classe', 'is_effectue', 'date']
    search_fields = ['titre', 'classe__nom', 'professeur__last_name']
    readonly_fields = ['id', 'date_saisie', 'date_modification']


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_devoir', 'classe', 'matiere', 'professeur', 'date_attribution', 'date_rendu', 'est_notifie']
    list_filter = ['type_devoir', 'classe', 'matiere', 'est_notifie']
    search_fields = ['titre', 'classe__nom', 'professeur__last_name']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(Lecon)
class LeconAdmin(admin.ModelAdmin):
    list_display = ['numero', 'titre', 'chapitre', 'classe', 'matiere', 'is_realise', 'date_realisation']
    list_filter = ['matiere', 'classe', 'is_realise']
    search_fields = ['titre', 'chapitre', 'classe__nom']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(RenduDevoir)
class RenduDevoirAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'devoir', 'date_rendu', 'statut', 'note', 'est_corrige']
    list_filter = ['statut', 'est_corrige']
    search_fields = ['eleve__last_name', 'devoir__titre']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(Progression)
class ProgressionAdmin(admin.ModelAdmin):
    list_display = ['classe', 'matiere', 'trimestre', 'annee_scolaire', 'nombre_lecons_realisees', 'nombre_lecons_totales', 'pourcentage_avancement']
    list_filter = ['trimestre', 'annee_scolaire', 'matiere']
    search_fields = ['classe__nom', 'matiere__nom']
    readonly_fields = ['id', 'date_creation', 'date_modification']
