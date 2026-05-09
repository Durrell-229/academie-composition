"""
Administration pour les certificats et examens
"""

from django.contrib import admin
from .models import TypeCertificat, CertificatScolaire, ExamenSession, InscriptionExamen, CopieExamenPhysique, HistoriqueCertificat


@admin.register(TypeCertificat)
class TypeCertificatAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'niveau_scolaire', 'etablissement', 'mention_reussite', 'mention_echec', 'is_actif']
    list_filter = ['niveau_scolaire', 'is_actif', 'etablissement']
    search_fields = ['nom', 'code', 'etablissement__nom']
    readonly_fields = ['id', 'date_creation']


@admin.register(CertificatScolaire)
class CertificatScolaireAdmin(admin.ModelAdmin):
    list_display = ['numero_certificat', 'eleve', 'type_certificat', 'statut', 'moyenne_generale', 'est_delivre', 'date_delivrance']
    list_filter = ['statut', 'est_delivre', 'type_certificat', 'annee_scolaire']
    search_fields = ['numero_certificat', 'eleve__last_name', 'eleve__first_name', 'code_verification']
    readonly_fields = ['id', 'numero_certificat', 'code_verification', 'date_creation', 'date_modification']
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero_certificat', 'type_certificat', 'etablissement', 'eleve', 'classe')
        }),
        ('Session d\'examen', {
            'fields': ('examen', 'annee_scolaire', 'session')
        }),
        ('Résultats', {
            'fields': ('moyenne_generale', 'note_maximale', 'statut', 'mention', 'intitule_programme')
        }),
        ('Signatures', {
            'fields': ('signataire_1', 'date_signature_1', 'signataire_2', 'date_signature_2')
        }),
        ('Délivrance', {
            'fields': ('est_delivre', 'date_delivrance', 'lieu_delivrance', 'delivre_par')
        }),
        ('Sécurité', {
            'fields': ('qr_code', 'code_verification')
        }),
        ('Métadonnées', {
            'fields': ('id', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )


@admin.register(ExamenSession)
class ExamenSessionAdmin(admin.ModelAdmin):
    list_display = ['type_examen', 'session', 'annee_scolaire', 'etablissement', 'date_debut', 'taux_reussite', 'resultats_publies', 'is_ouvert']
    list_filter = ['type_examen', 'session', 'resultats_publies', 'is_ouvert', 'etablissement']
    search_fields = ['etablissement__nom', 'description']
    readonly_fields = ['id', 'date_creation']
    filter_horizontal = ['matieres']


@admin.register(InscriptionExamen)
class InscriptionExamenAdmin(admin.ModelAdmin):
    list_display = ['numero_inscription', 'eleve', 'session', 'classe', 'date_inscription', 'statut', 'est_admis', 'moyenne_obtenue']
    list_filter = ['statut', 'est_admis', 'session__type_examen', 'date_inscription']
    search_fields = ['numero_inscription', 'eleve__last_name', 'eleve__first_name']
    readonly_fields = ['id', 'numero_inscription', 'date_inscription']


@admin.register(CopieExamenPhysique)
class CopieExamenPhysiqueAdmin(admin.ModelAdmin):
    list_display = ['inscription', 'matiere', 'statut', 'note_suggeree_ia', 'note_finale', 'corrige_par_ia', 'date_soumission']
    list_filter = ['statut', 'corrige_par_ia', 'matiere']
    search_fields = ['inscription__eleve__last_name', 'matiere__nom']
    readonly_fields = ['id', 'date_soumission', 'date_correction_ia', 'date_verification']


@admin.register(HistoriqueCertificat)
class HistoriqueCertificatAdmin(admin.ModelAdmin):
    list_display = ['certificat', 'code_verification', 'resultat_verification', 'ip_verificateur', 'date_verification']
    list_filter = ['resultat_verification', 'date_verification']
    search_fields = ['certificat__numero_certificat', 'code_verification']
    readonly_fields = ['id', 'date_verification']
