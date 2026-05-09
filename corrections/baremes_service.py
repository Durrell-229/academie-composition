import logging
from typing import Dict, List, Optional
from django.conf import settings
from ai_engine.enhanced_multi_ai import multi_ai

logger = logging.getLogger(__name__)

class BaremesService:
    """
    Service de barèmes IA pour la correction automatique
    Utilise NVIDIA Nemotron pour l'analyse et l'évaluation
    """
    
    def __init__(self):
        self.ai_service = multi_ai
        self.default_bareme = {
            'comprehension': 0.25,
            'structure': 0.20,
            'precision': 0.25,
            'methodologie': 0.15,
            'presentation': 0.15
        }
    
    def generate_bareme_ia(self, matiere: str, classe: str, theme: str, type_evaluation: str = 'examen') -> Dict:
        """Générer un barème automatique avec IA selon le programme béninois"""
        try:
            # Prompt pour générer le barème
            prompt = f"""Génère un barème de correction détaillé pour:

Matère: {matiere}
Classe: {classe}
Thème: {theme}
Type d'évaluation: {type_evaluation}
Contexte: Programme éducatif béninois

Format JSON requis:
{{
    "titre": "Titre du barème",
    "total_points": 20,
    "critères": [
        {{
            "nom": "Critère 1",
            "points": 5,
            "description": "Description détaillée",
            "indicateurs": ["Indicateur 1", "Indicateur 2"],
            "ponderation": 0.25
        }}
    ],
    "competences_visees": ["Compétence 1", "Compétence 2"],
    "references_programme": "Référence au programme officiel béninois"
}}

Génère le barème maintenant:"""
            
            response = self.ai_service.generate(prompt)
            
            # Parser la réponse JSON
            try:
                import json
                bareme = json.loads(response)
                
                # Valider et normaliser le barème
                bareme = self._validate_bareme(bareme)
                
                logger.info(f"Barème généré pour {matiere} - {classe}")
                return bareme
                
            except json.JSONDecodeError:
                logger.error("Réponse IA non-JSON valide")
                return self._get_default_bareme(matiere, theme)
                
        except Exception as e:
            logger.error(f"Erreur génération barème IA: {e}")
            return self._get_default_bareme(matiere, theme)
    
    def _validate_bareme(self, bareme: Dict) -> Dict:
        """Valider et normaliser le barème généré"""
        # S'assurer que le total est 20
        if 'total_points' not in bareme or bareme['total_points'] != 20:
            bareme['total_points'] = 20
        
        # Normaliser les pondérations
        if 'critères' in bareme:
            total_ponderation = sum(c.get('ponderation', 0) for c in bareme['critères'])
            if total_ponderation != 1.0:
                for critere in bareme['critères']:
                    critere['ponderation'] = critere.get('ponderation', 0) / total_ponderation
        
        # Ajouter les champs manquants
        if 'competences_visees' not in bareme:
            bareme['competences_visees'] = []
        if 'references_programme' not in bareme:
            bareme['references_programme'] = "Programme officiel béninois"
        
        return bareme
    
    def _get_default_bareme(self, matiere: str, theme: str) -> Dict:
        """Retourner un barème par défaut"""
        return {
            'titre': f"Barème {matiere} - {theme}",
            'total_points': 20,
            'critères': [
                {
                    'nom': 'Compréhension du sujet',
                    'points': 4,
                    'description': 'Capacité à comprendre et restituer les concepts clés',
                    'indicateurs': ['Définitions correctes', 'Mise en contexte', 'Explication claire'],
                    'ponderation': 0.20
                },
                {
                    'nom': 'Structure et organisation',
                    'points': 4,
                    'description': 'Organisation logique de la réponse',
                    'indicateurs': ['Introduction', 'Développement structuré', 'Conclusion'],
                    'ponderation': 0.20
                },
                {
                    'nom': 'Précision et exactitude',
                    'points': 5,
                    'description': 'Exactitude des informations fournies',
                    'indicateurs': ['Données correctes', 'Calculs justes', 'Références précises'],
                    'ponderation': 0.25
                },
                {
                    'nom': 'Méthodologie et raisonnement',
                    'points': 4,
                    'description': 'Qualité du raisonnement et de la méthode',
                    'indicateurs': ['Logique', 'Étapes claires', 'Justifications'],
                    'ponderation': 0.20
                },
                {
                    'nom': 'Présentation et expression',
                    'points': 3,
                    'description': "Qualité de l'expression et de la présentation",
                    'indicateurs': ['Orthographe', 'Grammaire', 'Lisibilité'],
                    'ponderation': 0.15
                }
            ],
            'competences_visees': [
                'Analyse et synthèse',
                'Raisonnement critique',
                'Communication écrite'
            ],
            'references_programme': 'Programme officiel béninois'
        }
    
    def evaluate_with_bareme(self, student_text: str, correction_text: str, bareme: Dict) -> Dict:
        """Évaluer la copie selon le barème avec IA"""
        try:
            total_note = 0
            criteres_evaluations = []
            
            for critere in bareme.get('critères', []):
                # Évaluer ce critère spécifique
                evaluation = self._evaluate_critere(
                    student_text,
                    correction_text,
                    critere
                )
                
                note_critere = evaluation['score'] * critere['points']
                total_note += note_critere
                
                criteres_evaluations.append({
                    'critere': critere['nom'],
                    'points_max': critere['points'],
                    'points_obtenus': round(note_critere, 2),
                    'score_pourcentage': round(evaluation['score'] * 100, 1),
                    'commentaire': evaluation['commentaire'],
                    'indicateurs': evaluation['indicateurs']
                })
            
            return {
                'note_totale': round(total_note, 2),
                'note_sur_20': round(total_note, 2),
                'criteres': criteres_evaluations,
                'evaluation_complete': True,
                'bareme_utilise': bareme['titre']
            }
            
        except Exception as e:
            logger.error(f"Erreur évaluation avec barème: {e}")
            return {
                'note_totale': 0,
                'error': str(e),
                'evaluation_complete': False
            }
    
    def _evaluate_critere(self, student_text: str, correction_text: str, critere: Dict) -> Dict:
        """Évaluer un critère spécifique avec IA"""
        try:
            prompt = f"""Évalue la copie élève selon le critère suivant:

Critère: {critere['nom']}
Description: {critere['description']}
Points max: {critere['points']}
Indicateurs: {', '.join(critere.get('indicateurs', []))}

Copie élève:
{student_text[:2000]}

Corrigé type:
{correction_text[:2000]}

Évalue de 0 à 1 (0 = insuffisant, 1 = excellent) et fournis:
- Un score numérique
- Un commentaire bref
- Les indicateurs respectés

Format JSON:
{{
    "score": 0.75,
    "commentaire": "Commentaire",
    "indicateurs": ["Indicateur 1", "Indicateur 2"]
}}"""
            
            response = self.ai_service.generate(prompt)
            
            try:
                import json
                evaluation = json.loads(response)
                return evaluation
            except json.JSONDecodeError:
                # Fallback : évaluation basique
                return self._basic_evaluation(student_text, correction_text, critere)
                
        except Exception as e:
            logger.error(f"Erreur évaluation critère: {e}")
            return self._basic_evaluation(student_text, correction_text, critere)
    
    def _basic_evaluation(self, student_text: str, correction_text: str, critere: Dict) -> Dict:
        """Évaluation basique sans IA"""
        # Comparaison simple de longueur
        student_words = len(student_text.split())
        correction_words = len(correction_text.split())
        
        score = min(1.0, student_words / max(correction_words, 1)) * 0.7
        
        return {
            'score': score,
            'commentaire': 'Évaluation automatique basique',
            'indicateurs': []
        }
    
    def get_bareme_for_exam(self, exam) -> Dict:
        """Récupérer ou générer un barème pour un examen"""
        try:
            # Chercher un barème existant
            from corrections.models import Bareme
            bareme = Bareme.objects.filter(exam=exam).first()
            
            if bareme:
                return bareme.to_dict()
            
            # Générer un nouveau barème
            return self.generate_bareme_ia(
                matiere=exam.matiere.nom,
                classe=exam.classe.nom,
                theme=exam.titre or exam.description,
                type_evaluation=exam.type_exam
            )
            
        except Exception as e:
            logger.error(f"Erreur récupération barème examen: {e}")
            return self._get_default_bareme(exam.matiere.nom, exam.titre)

# Instance globale
baremes_service = BaremesService()
