import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Safe imports for optional dependencies
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    from mistralai.client import Mistral
    HAS_MISTRAL = True
except ImportError:
    HAS_MISTRAL = False


class SmartOrchestrator:
    def __init__(self):
        # Initialisation des clients (Clés récupérées depuis l'environnement pour la sécurité en prod)
        self.groq_client = None
        self.mistral_client = None
        
        groq_key = os.environ.get("GROQ_API_KEY", "")
        mistral_key = os.environ.get("MISTRAL_API_KEY", "")
        
        if HAS_GROQ and groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
            except Exception as e:
                logger.warning(f"Impossible d'initialiser Groq: {e}")
        
        if HAS_MISTRAL and mistral_key:
            try:
                self.mistral_client = Mistral(api_key=mistral_key)
            except Exception as e:
                logger.warning(f"Impossible d'initialiser Mistral: {e}")
        
    def generate_qcm_questions(self, topic: str, grade: str) -> str:
        """Génère uniquement le sujet (questions)."""
        prompt = f"Crée un QCM sur le sujet: {topic} pour la classe: {grade}. Affiche uniquement les questions et les choix. Ne donne aucune réponse."
        return self._call_llm(prompt)

    def generate_qcm_correction(self, topic: str, grade: str) -> str:
        """Génère uniquement la correction."""
        prompt = f"Donne la correction détaillée et la remédiation pour le QCM sur le sujet: {topic} pour la classe: {grade}."
        return self._call_llm(prompt)

    def _call_llm(self, prompt: str) -> str:
        """Méthode utilitaire interne pour appeler Groq ou Mistral."""
        # 1. Tentative Groq
        if self.groq_client:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                logger.warning(f"Erreur Groq: {e}")
        
        # 2. Repli Mistral
        if self.mistral_client:
            try:
                response = self.mistral_client.chat.complete(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Erreur Mistral: {e}")
        
        # 3. Aucune IA disponible
        logger.critical("Toutes les IA ont échoué ou ne sont pas configurées.")
        return "Désolé, aucune IA n'est disponible pour traiter cette demande."

    def correct_copy(self, base64_image: str, corrige_text: str) -> str:
        """Correction de copie via Mistral Vision (Images)."""
        if not self.mistral_client:
            return "Erreur IA (Vision): Client Mistral non configuré."
        
        try:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Corrige cette copie d'examen en fonction de ce corrigé type: {corrige_text}. Donne la note sur 20, les erreurs, la remédiation et des conseils."},
                    {"type": "image_url", "image_url": base64_image}
                ]
            }]
            response = self.mistral_client.chat.complete(
                model="mistral-small-latest", messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur correction vision: {str(e)}")
            return f"Erreur IA (Vision): {str(e)}"

    def correct_text(self, student_text: str, correction_type: str) -> str:
        """Correction de texte avec retour JSON strict pour calcul de note."""
        prompt = f"""
        Tu es un correcteur expert. Analyse le texte suivant basé sur ce corrigé type: '{correction_type}'.
        Tu DOIS répondre UNIQUEMENT avec un objet JSON valide, sans aucune phrase introductive, sans texte avant ou après.
        Format attendu:
        {{
            "note": 15,
            "corrections": "Explications détaillées ici...",
            "remediation": "Conseils ici..."
        }}
        Texte élève: {student_text}
        """
        if not self.mistral_client:
            return '{"note": 0, "corrections": "IA non configurée", "remediation": "Contactez l\'administrateur"}'
        
        try:
            response = self.mistral_client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()
            # Nettoyage additionnel : si l'IA ajoute des balises Markdown, on les retire
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            return content.strip()
        except Exception as e:
            logger.error(f"Erreur correction texte JSON: {str(e)}")
            return '{"note": 0, "corrections": "Erreur technique IA", "remediation": "Réessayer"}'
