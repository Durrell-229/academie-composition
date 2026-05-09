# Vérification des modèles de bulletins pour affichage complet
from django.db import models
from django.conf import settings

class Bulletin(models.Model):
    """Modèle Bulletin avec toutes les infos élèves"""
    
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bulletins')
    classe = models.ForeignKey('core.Classe', on_delete=models.CASCADE, related_name='bulletins')
    
    # Informations personnelles complètes
    matricule = models.CharField(_('matricule'), max_length=50, blank=True)
    date_naissance = models.DateField(_('date de naissance'), null=True, blank=True)
    lieu_naissance = models.CharField(_('lieu de naissance'), max_length=200, blank=True)
    sexe = models.CharField(_('sexe'), max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], blank=True)
    nationalite = models.CharField(_('nationalité'), max_length=100, default='Béninoise')
    
    # Informations académiques
    annee_scolaire = models.PositiveIntegerField(_('année scolaire'))
    trimestre = models.PositiveIntegerField(_('trimestre'))
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0)
    rang_classe = models.PositiveIntegerField(_('rang dans la classe'), null=True, blank=True)
    
    # Informations administratives
    date_emission = models.DateTimeField(_('date d'émission'), auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(_('dernière mise à jour'), auto_now=True)
    
    # Avis et appréciations
    avis_conseil = models.TextField(_('avis du conseil'), blank=True)
    appreciation_generale = models.TextField(_('appréciation générale'), blank=True)
    
    # Statut
    statut = models.CharField(_('statut'), max_length=20, default='en_cours')
    
    # Méta-données
    genere_par_ia = models.BooleanField(_('généré par IA'), default=True)
    
    class Meta:
        verbose_name = _('Bulletin')
        verbose_name_plural = _('Bulletins')
        ordering = ['-annee_scolaire', '-trimestre', 'eleve']
        unique_together = ['eleve', 'classe', 'annee_scolaire', 'trimestre']
    
    def __str__(self):
        return f"Bulletin {self.eleve.email} - {self.classe.nom} - T{self.trimestre}"
    
    def get_eleve_full_info(self):
        """Retourner toutes les infos de l'élève"""
        return {
            'nom': self.eleve.last_name,
            'prenom': self.eleve.first_name,
            'email': self.eleve.email,
            'matricule': self.matricule or self.eleve.matricule if hasattr(self.eleve, 'matricule') else '',
            'date_naissance': self.date_naissance or self.eleve.date_naissance if hasattr(self.eleve, 'date_naissance') else None,
            'lieu_naissance': self.lieu_naissance or self.eleve.lieu_naissance if hasattr(self.eleve, 'lieu_naissance') else '',
            'sexe': self.sexe or self.eleve.sexe if hasattr(self.eleve, 'sexe') else '',
            'nationalite': self.nationalite,
            'classe': self.classe.nom,
            'annee_scolaire': self.annee_scolaire,
            'trimestre': self.trimestre
        }
