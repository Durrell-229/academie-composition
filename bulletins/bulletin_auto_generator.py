import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from bulletins.models import Bulletin, BulletinLigne
from bulletins.services import BulletinService

logger = logging.getLogger(__name__)

class BulletinAutoGenerator:
    """
    Génération automatique de bulletins après correction
    Intégrée avec le système de correction IA et les barèmes
    """
    
    def __init__(self):
        self.bulletin_service = BulletinService()
    
    def generate_after_correction(self, session, evaluation_result: Dict) -> Dict:
        """Générer automatiquement le bulletin après correction"""
        try:
            student = session.eleve
            exam = session.exam
            
            logger.info(f"Génération bulletin pour {student.email} - {exam.titre}")
            
            # Récupérer ou créer le bulletin
            bulletin = self._get_or_create_bulletin(student, session)
            
            # Ajouter la ligne pour cette évaluation
            ligne = self._add_evaluation_ligne(bulletin, session, evaluation_result)
            
            # Calculer les moyennes et statistiques
            self._calculate_bulletin_stats(bulletin)
            
            # Marquer comme généré
            bulletin.derniere_mise_a_jour = timezone.now()
            bulletin.save()
            
            logger.info(f"Bulletin généré avec succès: {bulletin.id}")
            
            return {
                'success': True,
                'bulletin_id': bulletin.id,
                'note': evaluation_result.get('note', 0),
                'moyenne_generale': bulletin.moyenne_generale
            }
            
        except Exception as e:
            logger.error(f"Erreur génération bulletin automatique: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_bulletin(self, student, session):
        """Récupérer ou créer le bulletin"""
        from core.models import Classe
        
        try:
            # Chercher un bulletin existant pour le trimestre
            bulletin = Bulletin.objects.filter(
                eleve=student,
                classe=session.classe,
                annee_scolaire=timezone.now().year,
                trimestre=self._get_current_trimestre()
            ).first()
            
            if bulletin:
                return bulletin
            
            # Créer un nouveau bulletin
            bulletin = Bulletin.objects.create(
                eleve=student,
                classe=session.classe,
                annee_scolaire=timezone.now().year,
                trimestre=self._get_current_trimestre(),
                date_emission=timezone.now(),
                statut='en_cours'
            )
            
            logger.info(f"Nouveau bulletin créé: {bulletin.id}")
            return bulletin
            
        except Exception as e:
            logger.error(f"Erreur création bulletin: {e}")
            raise
    
    def _add_evaluation_ligne(self, bulletin, session, evaluation_result: Dict):
        """Ajouter une ligne d'évaluation au bulletin"""
        try:
            from core.models import Matiere
            
            # Récupérer la matière
            matiere = session.exam.matiere
            
            # Créer la ligne
            ligne = BulletinLigne.objects.create(
                bulletin=bulletin,
                matiere=matiere,
                type_evaluation='composition',
                titre=session.exam.titre,
                note=evaluation_result.get('note', 0),
                note_sur=20,
                coefficient=matiere.coefficient if hasattr(matiere, 'coefficient') else 1,
                date_evaluation=session.date_fin or timezone.now(),
                appreciation=self._generate_appreciation(evaluation_result.get('note', 0)),
                details_correction=evaluation_result
            )
            
            logger.info(f"Ligne bulletin ajoutée: {ligne.id}")
            return ligne
            
        except Exception as e:
            logger.error(f"Erreur ajout ligne bulletin: {e}")
            raise
    
    def _calculate_bulletin_stats(self, bulletin):
        """Calculer les statistiques du bulletin"""
        try:
            lignes = bulletin.lignes.all()
            
            if not lignes:
                bulletin.moyenne_generale = 0
                bulletin.save()
                return
            
            # Calculer la moyenne pondérée
            total_points = 0
            total_coefficients = 0
            
            for ligne in lignes:
                total_points += ligne.note * ligne.coefficient
                total_coefficients += ligne.coefficient
            
            bulletin.moyenne_generale = round(total_points / total_coefficients, 2) if total_coefficients > 0 else 0
            
            # Déterminer le rang
            bulletin.rang_classe = self._calculate_rank(bulletin)
            
            # Déterminer l'avis du conseil
            bulletin.avis_conseil = self._generate_avis(bulletin.moyenne_generale)
            
            bulletin.save()
            
        except Exception as e:
            logger.error(f"Erreur calcul stats bulletin: {e}")
    
    def _get_current_trimestre(self):
        """Déterminer le trimestre actuel"""
        current_month = timezone.now().month
        if current_month <= 11:
            return 1
        elif current_month <= 2:
            return 2
        else:
            return 3
    
    def _generate_appreciation(self, note: float) -> str:
        """Générer l'appréciation selon la note"""
        if note >= 18:
            return "Excellent"
        elif note >= 16:
            return "Très bien"
        elif note >= 14:
            return "Bien"
        elif note >= 12:
            return "Assez bien"
        elif note >= 10:
            return "Passable"
        elif note >= 8:
            return "Insuffisant"
        else:
            return "Très insuffisant"
    
    def _generate_avis(self, moyenne: float) -> str:
        """Générer l'avis du conseil de classe"""
        if moyenne >= 16:
            return "Félicitations du conseil de classe"
        elif moyenne >= 14:
            return "Compliments du conseil de classe"
        elif moyenne >= 12:
            return "Encouragements"
        elif moyenne >= 10:
            return "Peut mieux faire"
        else:
            return "Doit redoubler d'efforts"
    
    def _calculate_rank(self, bulletin) -> int:
        """Calculer le rang de l'élève dans la classe"""
        try:
            # Récupérer tous les bulletins de la classe
            bulletins_classe = Bulletin.objects.filter(
                classe=bulletin.classe,
                annee_scolaire=bulletin.annee_scolaire,
                trimestre=bulletin.trimestre
            ).order_by('-moyenne_generale')
            
            # Trouver le rang
            for i, b in enumerate(bulletins_classe, 1):
                if b.id == bulletin.id:
                    return i
            
            return len(bulletins_classe)
            
        except Exception as e:
            logger.error(f"Erreur calcul rang: {e}")
            return 0
    
    def ensure_bulletin_completeness(self, bulletin):
        """S'assurer que toutes les infos de l'élève sont complètes"""
        try:
            from accounts.models import User
            
            student = bulletin.eleve
            
            # Vérifier les champs obligatoires
            required_fields = ['first_name', 'last_name', 'email']
            missing_fields = [f for f in required_fields if not getattr(student, f)]
            
            if missing_fields:
                logger.warning(f"Champs manquants pour élève {student.id}: {missing_fields}")
            
            # Mettre à jour les infos complémentaires si disponibles
            if hasattr(student, 'date_naissance') and not bulletin.date_naissance:
                bulletin.date_naissance = student.date_naissance
            
            if hasattr(student, 'lieu_naissance') and not bulletin.lieu_naissance:
                bulletin.lieu_naissance = student.lieu_naissance
            
            bulletin.save()
            
        except Exception as e:
            logger.error(f"Erreur vérification complétude bulletin: {e}")

# Instance globale
bulletin_auto_generator = BulletinAutoGenerator()
