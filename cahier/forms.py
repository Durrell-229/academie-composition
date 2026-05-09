"""
Formulaires pour le cahier de texte
"""

from django import forms
from .models import SeanceCours, Devoir, Lecon, RenduDevoir, Progression


class SeanceCoursForm(forms.ModelForm):
    """Formulaire pour creer/modifier une seance"""
    
    class Meta:
        model = SeanceCours
        fields = ['classe', 'matiere', 'date', 'heure_debut', 'heure_fin', 'salle', 'titre', 'contenu', 'competences', 'objectifs', 'activites', 'materiel_utilise', 'documents', 'is_effectue']
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'salle': forms.TextInput(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'competences': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activites': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'materiel_utilise': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'documents': forms.FileInput(attrs={'class': 'form-control'}),
            'is_effectue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DevoirForm(forms.ModelForm):
    """Formulaire pour creer/modifier un devoir"""
    
    class Meta:
        model = Devoir
        fields = ['classe', 'matiere', 'titre', 'type_devoir', 'description', 'consignes', 'date_attribution', 'date_rendu', 'heure_rendu', 'note_maximale', 'coefficient', 'documents', 'est_evaluable', 'est_visible']
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'type_devoir': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'consignes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_attribution': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_rendu': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_rendu': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'note_maximale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'documents': forms.FileInput(attrs={'class': 'form-control'}),
            'est_evaluable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LeconForm(forms.ModelForm):
    """Formulaire pour creer/modifier une lecon"""
    
    class Meta:
        model = Lecon
        fields = ['classe', 'matiere', 'numero', 'titre', 'chapitre', 'contenu', 'resume', 'points_cles', 'questions_importantes', 'duree_estimee', 'support_cours', 'is_realise', 'date_realisation']
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'numero': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'chapitre': forms.TextInput(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'resume': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points_cles': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'questions_importantes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duree_estimee': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'support_cours': forms.FileInput(attrs={'class': 'form-control'}),
            'is_realise': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date_realisation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class RenduDevoirForm(forms.ModelForm):
    """Formulaire pour creer/modifier un rendu"""
    
    class Meta:
        model = RenduDevoir
        fields = ['date_rendu', 'contenu', 'documents', 'commentaire_eleve', 'note', 'appreciation', 'commentaire_professeur', 'est_corrige', 'est_visible_eleve']
        widgets = {
            'date_rendu': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'documents': forms.FileInput(attrs={'class': 'form-control'}),
            'commentaire_eleve': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'note': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'appreciation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'commentaire_professeur': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'est_corrige': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_visible_eleve': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProgressionForm(forms.ModelForm):
    """Formulaire pour creer/modifier une progression"""
    
    class Meta:
        model = Progression
        fields = ['classe', 'matiere', 'annee_scolaire', 'trimestre', 'nombre_lecons_totales', 'nombre_lecons_realisees', 'observations', 'difficultes_rencontrees', 'actions_correctives']
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control'}),
            'trimestre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_lecons_totales': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'nombre_lecons_realisees': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'difficultes_rencontrees': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actions_correctives': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
