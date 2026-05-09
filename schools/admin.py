"""
Administration pour la gestion multi-établissements
"""

from django.contrib import admin
from .models import Etablissement, Campus, NiveauScolaire, Classe, AnneeScolaire, ConfigurationEtablissement


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'type_etablissement', 'ville', 'pays', 'nombre_eleves', 'is_active', 'is_verified']
    list_filter = ['type_etablissement', 'pays', 'is_active', 'is_verified']
    search_fields = ['nom', 'code', 'ville', 'email']
    readonly_fields = ['id', 'date_creation', 'date_modification']
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'code', 'type_etablissement', 'logo')
        }),
        ('Contact et localisation', {
            'fields': ('adresse', 'ville', 'pays', 'code_postal', 'telephone', 'email', 'site_web', 'latitude', 'longitude')
        }),
        ('Informations administratives', {
            'fields': ('numero_agrement', 'uai', 'siret')
        }),
        ('Capacité et statistiques', {
            'fields': ('capacite_max', 'nombre_eleves', 'nombre_professeurs')
        }),
        ('Configuration', {
            'fields': ('langue_principale', 'fuseau_horaire', 'devise', 'annee_scolaire_courante')
        }),
        ('Statut', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Métadonnées', {
            'fields': ('id', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'etablissement', 'ville', 'nombre_salles', 'is_principal', 'is_active']
    list_filter = ['etablissement', 'is_principal', 'is_active']
    search_fields = ['nom', 'code', 'ville', 'adresse']
    readonly_fields = ['id', 'date_creation']


@admin.register(NiveauScolaire)
class NiveauScolaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'etablissement', 'ordre', 'duree_annees', 'is_active']
    list_filter = ['etablissement', 'is_active']
    search_fields = ['nom', 'code', 'etablissement__nom']
    ordering = ['etablissement', 'ordre', 'nom']


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'etablissement', 'campus', 'niveau', 'effectif_actuel', 'capacite_max', 'professeur_principal', 'is_active']
    list_filter = ['etablissement', 'campus', 'niveau', 'is_active', 'annee_scolaire']
    search_fields = ['nom', 'code', 'etablissement__nom', 'niveau__nom']
    readonly_fields = ['id', 'date_creation', 'places_disponibles']


@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'etablissement', 'date_debut', 'date_fin', 'is_courante', 'is_active']
    list_filter = ['etablissement', 'is_courante', 'is_active']
    search_fields = ['nom', 'code', 'etablissement__nom']
    readonly_fields = ['id', 'date_creation']


@admin.register(ConfigurationEtablissement)
class ConfigurationEtablissementAdmin(admin.ModelAdmin):
    list_display = ['etablissement', 'systeme_evaluation', 'note_minimale_reussite', 'devise']
    search_fields = ['etablissement__nom']
    readonly_fields = ['id', 'date_modification']
    fieldsets = (
        ('Configuration académique', {
            'fields': ('systeme_evaluation', 'note_minimale_reussite', 'coefficient_max')
        }),
        ('Configuration horaire', {
            'fields': ('heure_debut_cours', 'heure_fin_cours', 'duree_cours', 'pause_dejeuner', 'duree_pause_dejeuner')
        }),
        ('Configuration bulletins', {
            'fields': ('frequence_bulletins', 'delai_publication_bulletins')
        }),
        ('Configuration absences', {
            'fields': ('tolerance_retard', 'max_absences')
        }),
        ('Configuration paiements', {
            'fields': ('devise', 'frais_inscription', 'mensualites')
        }),
        ('Configuration notifications', {
            'fields': ('notifications_parents', 'notifications_professeurs', 'notifications_eleves')
        }),
        ('Personnalisation', {
            'fields': ('couleur_principale', 'couleur_secondaire', 'nom_personnalise_bulletin')
        }),
        ('Métadonnées', {
            'fields': ('id', 'date_modification'),
            'classes': ('collapse',)
        })
    )
