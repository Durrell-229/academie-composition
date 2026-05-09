"""
Formulaires pour la gestion des présences
"""

from django import forms
from .models import Presence, Retard, Absence, RapportPresence


class PresenceForm(forms.ModelForm):
    """Formulaire pour créer/modifier une présence"""
    
    class Meta:
        model = Presence
        fields = ['eleve', 'classe', 'professeur', 'date', 'heure_arrivee', 'statut', 'motif_absence', 'duree_absence', 'minutes_retard', 'est_justifie', 'justificatif', 'observations']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'professeur': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_arrivee': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'motif_absence': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'duree_absence': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'minutes_retard': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'est_justifie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'justificatif': forms.FileInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RetardForm(forms.ModelForm):
    """Formulaire pour créer/modifier un retard"""
    
    class Meta:
        model = Retard
        fields = ['eleve', 'classe', 'date', 'heure_prevue', 'heure_arrivee', 'minutes_retard', 'type_retard', 'motif', 'sanction', 'est_pardonne']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_prevue': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_arrivee': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'minutes_retard': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'type_retard': forms.Select(attrs={'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'sanction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'est_pardonne': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AbsenceForm(forms.ModelForm):
    """Formulaire pour créer/modifier une absence"""
    
    class Meta:
        model = Absence
        fields = ['eleve', 'classe', 'date_debut', 'date_fin', 'type_absence', 'statut', 'motif', 'justificatif', 'valide_par', 'observations']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'type_absence': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'justificatif': forms.FileInput(attrs={'class': 'form-control'}),
            'valide_par': forms.Select(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RapportPresenceForm(forms.ModelForm):
    """Formulaire pour créer/modifier un rapport de présence"""
    
    class Meta:
        model = RapportPresence
        fields = ['eleve', 'classe', 'type_rapport', 'periode_debut', 'periode_fin', 'commentaire', 'recommandation']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'type_rapport': forms.Select(attrs={'class': 'form-control'}),
            'periode_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'periode_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommandation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
