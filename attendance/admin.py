"""
Administration pour la gestion des présences
"""

from django.contrib import admin
from .models import Presence, Retard, Absence, PresenceProfesseur, RapportPresence


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'classe', 'date', 'statut', 'minutes_retard', 'est_justifie', 'date_creation']
    list_filter = ['statut', 'est_justifie', 'date']
    search_fields = ['eleve__last_name', 'eleve__first_name', 'classe__nom']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(Retard)
class RetardAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'classe', 'date', 'minutes_retard', 'type_retard', 'est_pardonne', 'date_creation']
    list_filter = ['type_retard', 'est_pardonne', 'date']
    search_fields = ['eleve__last_name', 'eleve__first_name', 'motif']
    readonly_fields = ['id', 'date_creation']


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'classe', 'date_debut', 'date_fin', 'duree_jours', 'type_absence', 'statut', 'valide_par']
    list_filter = ['type_absence', 'statut', 'date_debut']
    search_fields = ['eleve__last_name', 'eleve__first_name', 'motif']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(PresenceProfesseur)
class PresenceProfesseurAdmin(admin.ModelAdmin):
    list_display = ['professeur', 'date', 'statut', 'minutes_retard', 'valide_par']
    list_filter = ['statut', 'date']
    search_fields = ['professeur__last_name', 'professeur__first_name']
    readonly_fields = ['id', 'date_creation']


@admin.register(RapportPresence)
class RapportPresenceAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'classe', 'type_rapport', 'periode_debut', 'periode_fin', 'taux_presence', 'jours_absents', 'date_generation']
    list_filter = ['type_rapport', 'periode_debut', 'periode_fin']
    search_fields = ['eleve__last_name', 'eleve__first_name']
    readonly_fields = ['id', 'date_generation']
