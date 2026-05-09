"""
Administration pour la gestion académique
"""

from django.contrib import admin
from .models import Promotion, Inscription, MatiereClasse, Evaluation, Note, BulletinNotes, Discipline


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'etablissement', 'annee_entree', 'annee_sortie', 'niveau_entree', 'niveau_sortie', 'nombre_eleves', 'is_active']
    list_filter = ['etablissement', 'is_active']
    search_fields = ['nom', 'code', 'etablissement__nom']
    readonly_fields = ['id', 'date_creation']


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ['numero_inscription', 'eleve', 'classe', 'annee_scolaire', 'statut', 'moyenne_generale', 'rang_classe', 'date_inscription']
    list_filter = ['statut', 'classe', 'annee_scolaire', 'est_redoublant', 'est_boursier']
    search_fields = ['numero_inscription', 'eleve__last_name', 'eleve__first_name', 'classe__nom']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(MatiereClasse)
class MatiereClasseAdmin(admin.ModelAdmin):
    list_display = ['matiere', 'classe', 'professeur', 'coefficient', 'heures_semaine', 'pourcentage_programme', 'is_active']
    list_filter = ['classe', 'is_active']
    search_fields = ['matiere__nom', 'classe__nom', 'professeur__last_name']
    readonly_fields = ['id', 'date_creation']


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_evaluation', 'classe', 'professeur', 'date_evaluation', 'duree', 'note_maximale', 'is_published', 'is_terminee']
    list_filter = ['type_evaluation', 'classe', 'is_published', 'is_terminee']
    search_fields = ['titre', 'classe__nom', 'professeur__last_name']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'evaluation', 'note', 'note_sur', 'est_absent', 'est_exclu', 'date_saisie']
    list_filter = ['evaluation', 'est_absent', 'est_exclu']
    search_fields = ['eleve__last_name', 'evaluation__titre']
    readonly_fields = ['id', 'date_saisie', 'date_modification']


@admin.register(BulletinNotes)
class BulletinNotesAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'classe', 'periode', 'type_bulletin', 'moyenne_generale', 'rang', 'est_valide', 'date_emission']
    list_filter = ['type_bulletin', 'periode', 'est_valide']
    search_fields = ['eleve__last_name', 'classe__nom']
    readonly_fields = ['id', 'date_emission']


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'classe', 'date_incident', 'motif', 'type_sanction', 'est_executee']
    list_filter = ['type_sanction', 'est_executee', 'date_incident']
    search_fields = ['eleve__last_name', 'motif', 'description']
    readonly_fields = ['id', 'date_creation']
