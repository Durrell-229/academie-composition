"""
Administration pour la gestion des emplois du temps
"""

from django.contrib import admin
from .models import EmploiDuTemps, CreneauHoraire, EvenementScolaire, DisponibiliteProfesseur, Salle


@admin.register(EmploiDuTemps)
class EmploiDuTempsAdmin(admin.ModelAdmin):
    list_display = ['nom', 'etablissement', 'type_cible', 'classe', 'professeur', 'annee_scolaire', 'semestre', 'is_actif']
    list_filter = ['type_cible', 'annee_scolaire', 'semestre', 'is_actif']
    search_fields = ['nom', 'etablissement__nom', 'classe__nom', 'professeur__last_name']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(CreneauHoraire)
class CreneauHoraireAdmin(admin.ModelAdmin):
    list_display = ['jour', 'heure_debut', 'heure_fin', 'matiere', 'professeur', 'classe', 'salle', 'is_actif']
    list_filter = ['jour', 'is_actif']
    search_fields = ['matiere__nom', 'professeur__last_name', 'classe__nom', 'salle']
    ordering = ['jour', 'heure_debut']


@admin.register(EvenementScolaire)
class EvenementScolaireAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_evenement', 'etablissement', 'date_debut', 'date_fin', 'lieu', 'priorite', 'is_annule']
    list_filter = ['type_evenement', 'priorite', 'is_annule', 'date_debut']
    search_fields = ['titre', 'description', 'lieu', 'organisateur__last_name']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(DisponibiliteProfesseur)
class DisponibiliteProfesseurAdmin(admin.ModelAdmin):
    list_display = ['professeur', 'jour', 'heure_debut_matin', 'heure_fin_matin', 'heure_debut_apresmidi', 'heure_fin_apresmidi', 'is_actif']
    list_filter = ['jour', 'is_actif']
    search_fields = ['professeur__last_name', 'professeur__first_name']
    ordering = ['professeur', 'jour']


@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'etablissement', 'campus', 'type_salle', 'capacite', 'is_disponible', 'is_accessible']
    list_filter = ['type_salle', 'is_disponible', 'is_accessible', 'etablissement']
    search_fields = ['nom', 'code', 'batiment']
    readonly_fields = ['id', 'date_creation']
