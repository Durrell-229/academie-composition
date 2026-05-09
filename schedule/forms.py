"""
Formulaires pour la gestion des emplois du temps
"""

from django import forms
from .models import EmploiDuTemps, CreneauHoraire, EvenementScolaire, DisponibiliteProfesseur, Salle


class EmploiDuTempsForm(forms.ModelForm):
    """Formulaire pour créer/modifier un emploi du temps"""
    
    class Meta:
        model = EmploiDuTemps
        fields = ['type_cible', 'classe', 'professeur', 'salle', 'annee_scolaire', 'semestre', 'nom', 'description', 'is_actif', 'is_public']
        widgets = {
            'type_cible': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'professeur': forms.Select(attrs={'class': 'form-control'}),
            'salle': forms.TextInput(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2024-2025'}),
            'semestre': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CreneauHoraireForm(forms.ModelForm):
    """Formulaire pour créer/modifier un créneau horaire"""
    
    class Meta:
        model = CreneauHoraire
        fields = ['jour', 'heure_debut', 'heure_fin', 'matiere', 'professeur', 'classe', 'salle', 'couleur', 'note', 'is_actif']
        widgets = {
            'jour': forms.Select(attrs={'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'professeur': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'salle': forms.TextInput(attrs={'class': 'form-control'}),
            'couleur': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EvenementScolaireForm(forms.ModelForm):
    """Formulaire pour créer/modifier un événement scolaire"""
    
    class Meta:
        model = EvenementScolaire
        fields = ['titre', 'description', 'type_evenement', 'date_debut', 'date_fin', 'lieu', 'salle', 
                  'priorite', 'rappel_avant', 'couleur', 'is_annule', 'motif_annulation']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_evenement': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
            'salle': forms.TextInput(attrs={'class': 'form-control'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'rappel_avant': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'couleur': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_annule': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'motif_annulation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DisponibiliteProfesseurForm(forms.ModelForm):
    """Formulaire pour créer/modifier une disponibilité professeur"""
    
    class Meta:
        model = DisponibiliteProfesseur
        fields = ['jour', 'heure_debut_matin', 'heure_fin_matin', 'heure_debut_apresmidi', 'heure_fin_apresmidi', 'notes', 'is_actif']
        widgets = {
            'jour': forms.Select(attrs={'class': 'form-control'}),
            'heure_debut_matin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin_matin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_debut_apresmidi': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin_apresmidi': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SalleForm(forms.ModelForm):
    """Formulaire pour créer/modifier une salle"""
    
    class Meta:
        model = Salle
        fields = ['nom', 'code', 'type_salle', 'capacite', 'superficie', 'equipements', 'etage', 'batiment', 'is_disponible', 'is_accessible', 'notes']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'type_salle': forms.Select(attrs={'class': 'form-control'}),
            'capacite': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'superficie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'equipements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'etage': forms.TextInput(attrs={'class': 'form-control'}),
            'batiment': forms.TextInput(attrs={'class': 'form-control'}),
            'is_disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_accessible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
