"""
Formulaires pour la gestion académique
"""

from django import forms
from .models import Promotion, Inscription, MatiereClasse, Evaluation, Note, BulletinNotes, Discipline
from schools.models import Classe, NiveauScolaire


class PromotionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une promotion"""
    
    class Meta:
        model = Promotion
        fields = ['nom', 'code', 'annee_entree', 'annee_sortie', 'niveau_entree', 'niveau_sortie', 'description', 'is_active']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'annee_entree': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2024-2025'}),
            'annee_sortie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2028-2029'}),
            'niveau_entree': forms.Select(attrs={'class': 'form-control'}),
            'niveau_sortie': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InscriptionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une inscription"""
    
    class Meta:
        model = Inscription
        fields = ['eleve', 'classe', 'promotion', 'annee_scolaire', 'statut', 'frais_inscription_payes', 
                  'frais_scolarite_payes', 'solde_du', 'est_redoublant', 'est_boursier', 'type_bourse', 'observations']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'promotion': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'frais_inscription_payes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'frais_scolarite_payes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'solde_du': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'est_redoublant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_boursier': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'type_bourse': forms.TextInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MatiereClasseForm(forms.ModelForm):
    """Formulaire pour ajouter une matière à une classe"""
    
    def __init__(self, *args, classe=None, **kwargs):
        super().__init__(*args, **kwargs)
        if classe:
            self.fields['matiere'].queryset = classe.etablissement.matieres.all()
    
    class Meta:
        model = MatiereClasse
        fields = ['matiere', 'professeur', 'coefficient', 'heures_semaine', 'salle', 'is_active']
        widgets = {
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'professeur': forms.Select(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'heures_semaine': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'salle': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EvaluationForm(forms.ModelForm):
    """Formulaire pour créer/modifier une évaluation"""
    
    class Meta:
        model = Evaluation
        fields = ['titre', 'type_evaluation', 'description', 'date_evaluation', 'duree', 
                  'note_maximale', 'coefficient', 'is_published', 'observations_professeur']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'type_evaluation': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_evaluation': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duree': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'note_maximale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observations_professeur': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class NoteForm(forms.ModelForm):
    """Formulaire pour saisir une note"""
    
    class Meta:
        model = Note
        fields = ['note', 'note_sur', 'appreciation', 'observation', 'est_absent', 'est_exclu', 'note_reportee']
        widgets = {
            'note': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note_sur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '20'}),
            'appreciation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'est_absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_exclu': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note_reportee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BulletinNotesForm(forms.ModelForm):
    """Formulaire pour créer/modifier un bulletin"""
    
    class Meta:
        model = BulletinNotes
        fields = ['periode', 'type_bulletin', 'moyenne_generale', 'moyenne_classe', 'rang', 
                  'effectif_classe', 'appreciation_generale', 'comportement', 'nombre_absences', 
                  'nombre_retards', 'est_valide', 'decision_conseil']
        widgets = {
            'periode': forms.TextInput(attrs={'class': 'form-control'}),
            'type_bulletin': forms.Select(attrs={'class': 'form-control'}),
            'moyenne_generale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'moyenne_classe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rang': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'effectif_classe': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'appreciation_generale': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'comportement': forms.Select(attrs={'class': 'form-control'}),
            'nombre_absences': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'nombre_retards': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'est_valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'decision_conseil': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DisciplineForm(forms.ModelForm):
    """Formulaire pour enregistrer un incident disciplinaire"""
    
    class Meta:
        model = Discipline
        fields = ['eleve', 'date_incident', 'motif', 'description', 'type_sanction', 
                  'duree_sanction', 'description_sanction', 'observations']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'date_incident': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motif': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_sanction': forms.Select(attrs={'class': 'form-control'}),
            'duree_sanction': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'description_sanction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
