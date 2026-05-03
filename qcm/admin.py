from django.contrib import admin
from .models import QuestionBank, Choice, QCMExam, QCMExamQuestion, QCMAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ('texte', 'est_correct', 'ordre', 'explication')


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('texte_trunc', 'matiere', 'difficulte', 'createur', 'est_publique', 'generee_par_ia', 'created_at')
    list_filter = ('difficulte', 'est_publique', 'generee_par_ia', 'matiere', 'created_at')
    search_fields = ('texte', 'explication', 'tags')
    inlines = [ChoiceInline]
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Question', {
            'fields': ('texte', 'explication', 'matiere', 'createur')
        }),
        ('Classification', {
            'fields': ('difficulte', 'tags', 'source_cours')
        }),
        ('Options', {
            'fields': ('est_publique', 'generee_par_ia')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_public', 'make_private', 'mark_as_ai_generated']
    
    def texte_trunc(self, obj):
        return obj.texte[:60] + '...' if len(obj.texte) > 60 else obj.texte
    texte_trunc.short_description = 'Question'
    
    def make_public(self, request, queryset):
        updated = queryset.update(est_publique=True)
        self.message_user(request, f'{updated} question(s) rendue(s) publique(s).')
    make_public.short_description = 'Rendre publiques'
    
    def make_private(self, request, queryset):
        updated = queryset.update(est_publique=False)
        self.message_user(request, f'{updated} question(s) rendue(s) privée(s).')
    make_private.short_description = 'Rendre privées'
    
    def mark_as_ai_generated(self, request, queryset):
        updated = queryset.update(generee_par_ia=True)
        self.message_user(request, f'{updated} question(s) marquées comme générées par IA.')
    mark_as_ai_generated.short_description = 'Marquer comme IA'


@admin.register(QCMExam)
class QCMExamAdmin(admin.ModelAdmin):
    list_display = ('exam', 'mode_notation', 'melanger_questions', 'melanger_choix', 
                    'afficher_resultat_immediat', 'nb_questions_par_page')
    list_filter = ('mode_notation', 'afficher_resultat_immediat')
    search_fields = ('exam__titre',)
    
    fieldsets = (
        ('Configuration QCM', {
            'fields': ('exam', 'mode_notation', 'points_bonne_reponse', 'penalite_mauvaise_reponse')
        }),
        ('Affichage', {
            'fields': ('melanger_questions', 'melanger_choix', 'nb_questions_par_page', 'afficher_resultat_immediat')
        }),
    )


@admin.register(QCMExamQuestion)
class QCMExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('qcm_exam', 'question', 'ordre', 'points')
    list_filter = ('qcm_exam__exam',)
    search_fields = ('question__texte',)


@admin.register(QCMAnswer)
class QCMAnswerAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'est_correct', 'points_obtenus', 'answered_at')
    list_filter = ('est_correct', 'session__exam')
    search_fields = ('session__eleve__email', 'question__texte')
    readonly_fields = ('answered_at',)
    date_hierarchy = 'answered_at'
    
    fieldsets = (
        ('Réponse', {
            'fields': ('session', 'question', 'choix_selectionnes')
        }),
        ('Résultat', {
            'fields': ('est_correct', 'points_obtenus', 'answered_at')
        }),
    )
