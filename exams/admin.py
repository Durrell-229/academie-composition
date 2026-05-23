from django.contrib import admin
from .models import (
    Exam, ExamFile, ExamAssignment,
    ExamenNational, ExamenNationalMatiere, ExamenComposition,
    ExamenReponseEleve, ExamenBulletin, ExamenBulletinLigne
)


class ExamFileInline(admin.TabularInline):
    model = ExamFile
    extra = 1


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_exam', 'matiere', 'classe', 'createur', 'statut', 'date_debut', 'date_fin', 'telephone_prof_beneficiaire']
    list_filter = ['type_exam', 'statut', 'matiere', 'classe']
    search_fields = ['titre', 'description', 'telephone_prof_beneficiaire']
    inlines = [ExamFileInline]
    date_hierarchy = 'date_debut'
    fieldsets = (
        (None, {
            'fields': ('titre', 'description', 'type_exam', 'trimestre', 'matiere', 'classe', 'createur')
        }),
        ('Planification', {
            'fields': ('date_debut', 'date_fin', 'duree_minutes', 'note_maximale', 'coefficient', 'statut', 'est_public', 'instructions')
        }),
        ('Anti-triche', {
            'fields': ('anti_cheat_active', 'camera_required', 'fullscreen_required')
        }),
        ('Répartition paiement', {
            'fields': ('telephone_prof_beneficiaire',),
            'description': (
                'Numéro Mobile Money (MTN/Moov) du professeur qui recevra 50 % '
                'de chaque paiement de correction. '
                'Les 50 % restants sont répartis automatiquement : '
                '5 % Dev1 · 5 % Dev2 · 40 % Entretien plateforme.'
            ),
        }),
    )


@admin.register(ExamAssignment)
class ExamAssignmentAdmin(admin.ModelAdmin):
    list_display = ['exam', 'eleve', 'classe', 'assigned_by', 'assigned_at']
    list_filter = ['assigned_at']
    search_fields = ['exam__titre', 'eleve__email']


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN EXAMEN NATIONAL
# ═══════════════════════════════════════════════════════════════════════════

class ExamenNationalMatiereInline(admin.TabularInline):
    model = ExamenNationalMatiere
    extra = 1


@admin.register(ExamenNational)
class ExamenNationalAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_examen', 'annee_scolaire', 'statut', 'date_debut', 'date_fin', 'createur']
    list_filter = ['type_examen', 'statut', 'annee_scolaire']
    search_fields = ['nom', 'instructions']
    filter_horizontal = ['classes', 'matieres']
    inlines = [ExamenNationalMatiereInline]
    date_hierarchy = 'date_debut'


@admin.register(ExamenNationalMatiere)
class ExamenNationalMatiereAdmin(admin.ModelAdmin):
    list_display = ['examen', 'matiere', 'statut', 'submitted_at']
    list_filter = ['statut', 'examen']
    search_fields = ['examen__nom', 'matiere__nom']


@admin.register(ExamenComposition)
class ExamenCompositionAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'examen', 'statut', 'moyenne_generale', 'rang', 'resultat']
    list_filter = ['statut', 'resultat', 'examen']
    search_fields = ['eleve__email', 'examen__nom']


@admin.register(ExamenReponseEleve)
class ExamenReponseEleveAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'examen_matiere', 'statut', 'note_ia', 'note_finale', 'created_at']
    list_filter = ['statut', 'examen_matiere__examen']
    search_fields = ['eleve__email', 'examen_matiere__matiere__nom']


class ExamenBulletinLigneInline(admin.TabularInline):
    model = ExamenBulletinLigne
    extra = 0


@admin.register(ExamenBulletin)
class ExamenBulletinAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'examen', 'moyenne_generale', 'rang', 'statut', 'created_at']
    list_filter = ['statut', 'examen']
    search_fields = ['eleve__email', 'examen__nom']
    inlines = [ExamenBulletinLigneInline]
