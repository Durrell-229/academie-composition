"""
Formulaires pour la gestion multi-établissements
"""

from django import forms
from .models import Etablissement, Campus, Classe, ConfigurationEtablissement


class EtablissementForm(forms.ModelForm):
    """Formulaire pour créer/modifier un établissement"""
    
    class Meta:
        model = Etablissement
        fields = [
            'nom', 'code', 'type_etablissement', 'logo',
            'adresse', 'ville', 'pays', 'code_postal', 'telephone', 'email', 'site_web',
            'latitude', 'longitude',
            'numero_agrement', 'uai', 'siret',
            'capacite_max', 'nombre_eleves', 'nombre_professeurs',
            'langue_principale', 'fuseau_horaire', 'devise', 'annee_scolaire_courante',
            'is_active', 'is_verified'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Lycée Saint-Michel'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: LYC-SM-001'}),
            'type_etablissement': forms.Select(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'code_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'numero_agrement': forms.TextInput(attrs={'class': 'form-control'}),
            'uai': forms.TextInput(attrs={'class': 'form-control'}),
            'siret': forms.TextInput(attrs={'class': 'form-control'}),
            'capacite_max': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'nombre_eleves': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'nombre_professeurs': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'langue_principale': forms.Select(attrs={'class': 'form-control'}),
            'fuseau_horaire': forms.Select(attrs={'class': 'form-control'}),
            'devise': forms.TextInput(attrs={'class': 'form-control'}),
            'annee_scolaire_courante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2024-2025'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CampusForm(forms.ModelForm):
    """Formulaire pour créer/modifier un campus"""
    
    class Meta:
        model = Campus
        fields = ['nom', 'code', 'adresse', 'ville', 'pays', 'latitude', 'longitude',
                  'superficie', 'nombre_salles', 'nombre_batiments', 'telephone', 'email', 'directeur',
                  'is_principal', 'is_active']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'superficie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nombre_salles': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'nombre_batiments': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'directeur': forms.TextInput(attrs={'class': 'form-control'}),
            'is_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClasseForm(forms.ModelForm):
    """Formulaire pour créer/modifier une classe"""
    
    def __init__(self, *args, etablissement=None, **kwargs):
        super().__init__(*args, **kwargs)
        if etablissement:
            self.fields['campus'].queryset = etablissement.campus.filter(is_active=True)
            self.fields['niveau'].queryset = etablissement.niveaux.filter(is_active=True)
    
    class Meta:
        model = Classe
        fields = ['nom', 'code', 'campus', 'niveau', 'section', 'capacite_max', 'professeur_principal', 'is_active', 'annee_scolaire']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 6ème A'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'campus': forms.Select(attrs={'class': 'form-control'}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A, B, C...'}),
            'capacite_max': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 40}),
            'professeur_principal': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control', 'value': '2024-2025'}),
        }


class ConfigurationEtablissementForm(forms.ModelForm):
    """Formulaire pour configurer un établissement"""
    
    class Meta:
        model = ConfigurationEtablissement
        fields = [
            'systeme_evaluation', 'note_minimale_reussite', 'coefficient_max',
            'heure_debut_cours', 'heure_fin_cours', 'duree_cours', 'pause_dejeuner', 'duree_pause_dejeuner',
            'frequence_bulletins', 'delai_publication_bulletins',
            'tolerance_retard', 'max_absences',
            'devise', 'frais_inscription',
            'notifications_parents', 'notifications_professeurs', 'notifications_eleves',
            'couleur_principale', 'couleur_secondaire', 'nom_personnalise_bulletin'
        ]
        widgets = {
            'systeme_evaluation': forms.Select(attrs={'class': 'form-control'}),
            'note_minimale_reussite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'coefficient_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'heure_debut_cours': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin_cours': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duree_cours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'pause_dejeuner': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duree_pause_dejeuner': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'frequence_bulletins': forms.Select(attrs={'class': 'form-control'}),
            'delai_publication_bulletins': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'tolerance_retard': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_absences': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'devise': forms.TextInput(attrs={'class': 'form-control'}),
            'frais_inscription': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'notifications_parents': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notifications_professeurs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notifications_eleves': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'couleur_principale': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'couleur_secondaire': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'nom_personnalise_bulletin': forms.TextInput(attrs={'class': 'form-control'}),
        }
