from django import forms
from django.contrib import admin
from django.utils import timezone
import json
from .models import (
    Devoir, DevoirMatiere, DevoirComposition, DevoirReponseEleve,
    BulletinDevoir, BulletinDevoirLigne, Certificat
)
from core.models import Matiere, Classe


class DevoirAdminForm(forms.ModelForm):
    """Formulaire admin pour Devoir avec gestion simplifiée des horaires et coefficients."""
    
    class Meta:
        model = Devoir
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des aides pour les champs JSON
        self.fields['horaires'].help_text = (
            'Format JSON: {"Maths": {"date": "2025-02-01", "heure_demarrage": "08:00", "heure_fin": "10:00", "salle": "A1"}}'
        )
        self.fields['coefficients_par_matiere'].help_text = (
            'Format JSON: {"1": 2.0, "2": 1.5} (ID de la matière: coefficient)'
        )


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    form = DevoirAdminForm
    list_display = ('titre', 'annee_scolaire', 'date_debut', 'date_fin', 'statut', 'createur', 'get_matieres_count')
    list_filter = ('statut', 'annee_scolaire')
    search_fields = ('titre', 'description')
    filter_horizontal = ('classes', 'matieres')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'annee_scolaire', 'instructions')
        }),
        ('Dates et statut', {
            'fields': ('date_debut', 'date_fin', 'statut', 'createur')
        }),
        ('Classes et matières', {
            'fields': ('classes', 'matieres'),
            'description': 'Sélectionnez les classes concernées et les matières du devoir.'
        }),
        ('Configuration avancée (JSON)', {
            'fields': ('horaires', 'coefficients_par_matiere', 'coefficient_default'),
            'classes': ('collapse',),
            'description': (
                '⚠️ Ces champs sont automatiquement gérés via l\'interface de création de devoirs. '
                'Ne les modifiez ici que si nécessaire.'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_matieres_count(self, obj):
        """Affiche le nombre de matières."""
        return obj.matieres.count()
    get_matieres_count.short_description = 'Matières'


@admin.register(DevoirMatiere)
class DevoirMatiereAdmin(admin.ModelAdmin):
    list_display = ('devoir', 'matiere', 'statut', 'soumis_par', 'submitted_at', 'valide_par')
    list_filter = ('statut', 'matiere')
    search_fields = ('devoir__titre', 'matiere__nom')
    readonly_fields = ('epreuve_document_id', 'corrige_document_id', 'submitted_at', 'validated_at')
    
    fieldsets = (
        ('Informations', {
            'fields': ('devoir', 'matiere', 'statut')
        }),
        ('Fichiers', {
            'fields': ('epreuve_file', 'corrige_type_file')
        }),
        ('Traçabilité IA', {
            'fields': ('epreuve_document_id', 'corrige_document_id'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('soumis_par', 'valide_par', 'commentaire_admin', 'submitted_at', 'validated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DevoirComposition)
class DevoirCompositionAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'devoir', 'statut', 'moyenne_generale', 'rang', 'resultat')
    list_filter = ('statut', 'resultat', 'devoir')
    search_fields = ('eleve__email', 'devoir__titre')
    readonly_fields = ('composed_at',)


@admin.register(DevoirReponseEleve)
class DevoirReponseEleveAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'devoir_matiere', 'statut', 'note_ia', 'note_finale', 'created_at')
    list_filter = ('statut', 'devoir_matiere__devoir')
    search_fields = ('eleve__email', 'devoir_matiere__matiere__nom')
    readonly_fields = ('note_ia', 'appreciation_ia', 'feedback_ia', 'corrige_at', 'copie_document_id')
    
    fieldsets = (
        ('Informations', {
            'fields': ('devoir_matiere', 'eleve', 'statut')
        }),
        ('Copie', {
            'fields': ('copie_file', 'copie_text', 'copie_document_id')
        }),
        ('Correction IA', {
            'fields': ('note_ia', 'note_finale', 'appreciation_ia', 'feedback_ia', 'corrige_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BulletinDevoir)
class BulletinDevoirAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'devoir', 'moyenne_generale', 'rang', 'statut', 'approuve_par', 'created_at')
    list_filter = ('statut', 'devoir')
    search_fields = ('eleve__email', 'devoir__titre')
    readonly_fields = ('verification_token', 'moyenne_generale', 'rang', 'created_at', 'approuve_at')


@admin.register(BulletinDevoirLigne)
class BulletinDevoirLigneAdmin(admin.ModelAdmin):
    list_display = ('bulletin', 'matiere', 'coefficient', 'moyenne', 'rang')
    list_filter = ('bulletin__devoir',)
    search_fields = ('matiere', 'bulletin__eleve__email')


@admin.register(Certificat)
class CertificatAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'eleve', 'devoir', 'type_certificat', 'moyenne_obtenue', 'date_delivrance')
    list_filter = ('type_certificat', 'date_delivrance')
    search_fields = ('numero_certificat', 'eleve__email', 'eleve__first_name', 'eleve__last_name')
    readonly_fields = ('numero_certificat', 'verification_token', 'created_at', 'file_pdf')
    
    fieldsets = (
        ('Informations', {
            'fields': ('eleve', 'devoir', 'type_certificat')
        }),
        ('Résultats', {
            'fields': ('moyenne_obtenue', 'mention')
        }),
        ('Certificat', {
            'fields': ('numero_certificat', 'date_delivrance', 'file_pdf', 'verification_token'),
            'classes': ('collapse',)
        }),
    )
