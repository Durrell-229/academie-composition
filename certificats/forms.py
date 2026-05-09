"""
Formulaires pour les certificats et examens
"""

from django import forms
from .models import TypeCertificat, CertificatScolaire, ExamenSession, InscriptionExamen, CopieExamenPhysique


class TypeCertificatForm(forms.ModelForm):
    """Formulaire pour créer/modifier un type de certificat"""
    
    class Meta:
        model = TypeCertificat
        fields = ['code', 'nom', 'description', 'niveau_scolaire', 'mention_reussite', 'mention_echec', 
                  'template_fond', 'couleur_principale', 'couleur_secondaire', 
                  'titre_signataire_1', 'titre_signataire_2', 'is_actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'niveau_scolaire': forms.Select(attrs={'class': 'form-control'}),
            'mention_reussite': forms.TextInput(attrs={'class': 'form-control', 'value': 'ADMIS'}),
            'mention_echec': forms.TextInput(attrs={'class': 'form-control', 'value': 'REFUSE'}),
            'template_fond': forms.FileInput(attrs={'class': 'form-control'}),
            'couleur_principale': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'value': '#1e3a8a'}),
            'couleur_secondaire': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'value': '#3b82f6'}),
            'titre_signataire_1': forms.TextInput(attrs={'class': 'form-control', 'value': 'Le Directeur'}),
            'titre_signataire_2': forms.TextInput(attrs={'class': 'form-control', 'value': 'Le Chef des Travaux'}),
            'is_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CertificatScolaireForm(forms.ModelForm):
    """Formulaire pour créer/modifier un certificat"""
    
    class Meta:
        model = CertificatScolaire
        fields = ['type_certificat', 'etablissement', 'eleve', 'classe', 'examen', 
                  'annee_scolaire', 'session', 'moyenne_generale', 'note_maximale',
                  'statut', 'mention', 'intitule_programme', 'appreciation_generale',
                  'lieu_delivrance', 'date_delivrance']
        widgets = {
            'type_certificat': forms.Select(attrs={'class': 'form-control'}),
            'etablissement': forms.Select(attrs={'class': 'form-control'}),
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'examen': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control', 'value': '2024-2025'}),
            'session': forms.TextInput(attrs={'class': 'form-control', 'value': 'Session Principale'}),
            'moyenne_generale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note_maximale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '20'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'mention': forms.TextInput(attrs={'class': 'form-control'}),
            'intitule_programme': forms.TextInput(attrs={'class': 'form-control'}),
            'appreciation_generale': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'lieu_delivrance': forms.TextInput(attrs={'class': 'form-control', 'value': 'Cotonou'}),
            'date_delivrance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ExamenSessionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une session d'examen"""
    
    class Meta:
        model = ExamenSession
        fields = ['type_examen', 'session', 'annee_scolaire', 'etablissement', 
                  'date_debut', 'date_fin', 'date_publication_resultats',
                  'moyenne_admission', 'matieres', 'description', 'instructions',
                  'is_ouvert']
        widgets = {
            'type_examen': forms.Select(attrs={'class': 'form-control'}),
            'session': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control', 'value': '2024-2025'}),
            'etablissement': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_publication_resultats': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'moyenne_admission': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '10'}),
            'matieres': forms.CheckboxSelectMultiple(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_ouvert': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InscriptionExamenForm(forms.ModelForm):
    """Formulaire pour créer/modifier une inscription à un examen"""
    
    class Meta:
        model = InscriptionExamen
        fields = ['session', 'eleve', 'classe', 'statut', 'moyenne_obtenue', 
                  'est_admis', 'decision_jury', 'observations']
        widgets = {
            'session': forms.Select(attrs={'class': 'form-control'}),
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'moyenne_obtenue': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'est_admis': forms.NullBooleanSelect(attrs={'class': 'form-control'}),
            'decision_jury': forms.TextInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CopieExamenPhysiqueForm(forms.ModelForm):
    """Formulaire pour upload une copie physique"""
    
    class Meta:
        model = CopieExamenPhysique
        fields = ['inscription', 'matiere', 'image_copie', 'images_supplementaires', 'observations_correcteur']
        widgets = {
            'inscription': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'image_copie': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'images_supplementaires': forms.HiddenInput(),
            'observations_correcteur': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class VerificationCopieForm(forms.Form):
    """Formulaire pour vérifier une copie corrigée par l'IA"""
    note_finale = forms.DecimalField(
        label='Note finale',
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    appreciation = forms.CharField(
        label='Appréciation',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    annotations = forms.CharField(
        label='Annotations',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False
    )
