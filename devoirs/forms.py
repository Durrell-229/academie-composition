from django import forms
from django.utils.translation import gettext_lazy as _
from core.models import Matiere, Classe
from accounts.models import User
from .models import Devoir, DevoirMatiere


class ClasseForm(forms.ModelForm):
    """Formulaire pour créer/modifier une classe."""
    
    class Meta:
        model = Classe
        fields = ['nom', 'niveau', 'section', 'annee_academique', 'is_active']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none',
                'placeholder': 'Ex: 6ème A, Tle C, 2nde A'
            }),
            'niveau': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none'
            }),
            'section': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none',
                'placeholder': 'Ex: A, B, C, D, E, G1, G2, G3'
            }),
            'annee_academique': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none',
                'placeholder': 'Ex: 2025-2026'
            }),
        }
        labels = {
            'nom': _('Nom de la classe'),
            'niveau': _('Niveau'),
            'section': _('Série / Filière'),
            'annee_academique': _('Année académique'),
            'is_active': _('Classe active'),
        }


class UserAssignClasseForm(forms.ModelForm):
    """Formulaire pour assigner un élève à une classe."""
    
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.filter(is_active=True),
        label=_('Classe'),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none'
        }),
        empty_label=_('Sélectionner une classe')
    )
    
    class Meta:
        model = User
        fields = ['classe']


class HoraireForm(forms.Form):
    """Formulaire pour ajouter un créneau horaire à un devoir."""
    
    matiere = forms.ModelChoiceField(
        queryset=Matiere.objects.filter(is_active=True),
        label=_('Matière'),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none'
        })
    )
    date = forms.DateField(
        label=_('Date'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none'
        })
    )
    heure_demarrage = forms.TimeField(
        label=_('Heure de début'),
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none'
        })
    )
    heure_fin = forms.TimeField(
        label=_('Heure de fin'),
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none'
        })
    )
    salle = forms.CharField(
        label=_('Salle'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-primary focus:ring-1 focus:ring-primary/30 transition outline-none',
            'placeholder': 'Ex: Amphithéâtre A, Salle 101'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        heure_demarrage = cleaned_data.get('heure_demarrage')
        heure_fin = cleaned_data.get('heure_fin')
        
        if heure_demarrage and heure_fin:
            if heure_fin <= heure_demarrage:
                raise forms.ValidationError(
                    _('L\'heure de fin doit être postérieure à l\'heure de début.')
                )
        
        return cleaned_data


class DevoirMatiereValidationForm(forms.ModelForm):
    """Formulaire pour valider/rejeter une épreuve."""
    
    COMMENT_CHOICES = [
        ('', _('Sélectionner un motif...')),
        ('conforme', _('Conforme - Validé')),
        ('erreur_enonce', _('Erreur dans l\'énoncé')),
        ('programme_non_respecte', _('Programme non respecté')),
        ('qualite_insuffisante', _('Qualité insuffisante')),
        ('corrige_incomplet', _('Corrigé incomplet')),
        ('autre', _('Autre (préciser)')),
    ]
    
    motif_rejet = forms.ChoiceField(
        choices=COMMENT_CHOICES,
        required=False,
        label=_('Motif du rejet'),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-danger focus:ring-1 focus:ring-danger/30 transition outline-none'
        })
    )
    commentaire_detaille = forms.CharField(
        required=False,
        label=_('Commentaire détaillé'),
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-3 rounded-xl bg-bg-secondary border border-border-standard focus:border-danger focus:ring-1 focus:ring-danger/30 transition outline-none resize-none',
            'placeholder': 'Précisez le motif du rejet...'
        })
    )
    
    class Meta:
        model = DevoirMatiere
        fields = []
