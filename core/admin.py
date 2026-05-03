from django import forms
from django.contrib import admin
from .models import Matiere, Classe, Parametre


class MatiereAdminForm(forms.ModelForm):
    """Formulaire admin pour Matiere avec sélection multiple de niveaux."""
    
    # Champ personnalisé avec checkboxes pour les niveaux
    niveaux_selection = forms.MultipleChoiceField(
        label='Niveaux concernés',
        required=False,
        choices=[
            ('primaire', 'Primaire'),
            ('secondaire', 'Secondaire'),
            ('universitaire', 'Universitaire'),
            ('professionnel', 'Formation Professionnelle'),
            ('entreprise', 'Entreprise'),
        ],
        widget=admin.widgets.FilteredSelectMultiple('niveaux', False),
        help_text='Sélectionnez un ou plusieurs niveaux concernés par cette matière.'
    )
    
    class Meta:
        model = Matiere
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-sélectionner les niveaux existants
        if self.instance.pk and self.instance.niveaux:
            self.fields['niveaux_selection'].initial = self.instance.niveaux
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convertir la sélection en JSON
        instance.niveaux = self.cleaned_data.get('niveaux_selection', [])
        if commit:
            instance.save()
        return instance


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    form = MatiereAdminForm
    list_display = ['nom', 'code', 'couleur', 'get_niveaux_display', 'is_active']
    search_fields = ['nom', 'code']
    list_filter = ['is_active']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'code', 'description')
        }),
        ('Configuration', {
            'fields': ('niveaux_selection', 'couleur', 'icone', 'is_active')
        }),
    )
    
    def get_niveaux_display(self, obj):
        """Affiche les niveaux de façon lisible."""
        if obj.niveaux:
            return ', '.join([n.capitalize() for n in obj.niveaux])
        return '—'
    get_niveaux_display.short_description = 'Niveaux'


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'niveau', 'section', 'annee_academique', 'is_active']
    search_fields = ['nom', 'section']
    list_filter = ['niveau', 'annee_academique']
    
    fieldsets = (
        ('Informations de la classe', {
            'fields': ('nom', 'niveau', 'section', 'annee_academique', 'is_active')
        }),
    )


@admin.register(Parametre)
class ParametreAdmin(admin.ModelAdmin):
    list_display = ['cle', 'description']
    search_fields = ['cle', 'description']
