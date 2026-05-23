"""
Service IA multi-provider avec fallback automatique.
Ordre de tentative : Groq → Gemini → Mistral → DeepSeek
"""
import os
import json
import logging
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class MultiAIService:
    """
    Service IA avec fallback automatique.
    Correction de copies : NVIDIA (vision/OCR) → Groq → Gemini → Mistral → DeepSeek
    Autres tâches (QCM, feedback) : Groq → Gemini → Mistral → DeepSeek
    """

    NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    NVIDIA_CORRECTION_MODEL = "meta/llama-3.3-70b-instruct"

    def __init__(self):
        self.nvidia_key = getattr(settings, 'NVIDIA_API_KEY', '') or os.environ.get('NVIDIA_API_KEY', '')
        self.groq_key = getattr(settings, 'GROQ_API_KEY', '') or os.environ.get('GROQ_API_KEY', '')
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        self.mistral_key = getattr(settings, 'MISTRAL_API_KEY', '') or os.environ.get('MISTRAL_API_KEY', '')
        self.deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', '') or os.environ.get('DEEPSEEK_API_KEY', '')

    def generate(self, prompt: str, expect_json: bool = False) -> str:
        """
        Envoie un prompt à l'IA disponible.
        Tente chaque fournisseur dans l'ordre jusqu'à succès.
        """
        providers = [
            ('Groq', self._call_groq),
            ('Gemini', self._call_gemini),
            ('Mistral', self._call_mistral),
            ('DeepSeek', self._call_deepseek),
        ]

        for name, fn in providers:
            try:
                result = fn(prompt)
                if result:
                    logger.info(f"[MultiAI] Succès via {name}")
                    return result
            except Exception as e:
                logger.warning(f"[MultiAI] Échec {name}: {e}")
                continue

        logger.error("[MultiAI] Tous les fournisseurs IA ont échoué.")
        if expect_json:
            return '{"note": null, "appreciation": "Correction impossible : aucun service IA disponible. Vérifiez vos clés API (GROQ_API_KEY, GEMINI_API_KEY, NVIDIA_API_KEY) dans le fichier .env.", "details": [], "points_forts_global": "", "axes_amelioration": "Configurez au moins une clé API valide pour activer la correction automatique.", "erreur_technique": true}'
        return "L'IA est temporairement indisponible. Vérifiez les clés API dans le fichier .env."

    def _call_nvidia_nemotron(self, prompt: str) -> Optional[str]:
        """
        Appel NVIDIA Nemotron-4-340B pour la correction de copies.
        Le texte OCR a déjà été extrait par nemotron-ocr-v1 en amont (dans tasks.py).
        """
        if not self.nvidia_key or 'ta_cle' in self.nvidia_key:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.nvidia_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.NVIDIA_CORRECTION_MODEL,
                "messages": [
                    {"role": "system", "content": "Tu es un correcteur d'examens expert et strict. Réponds UNIQUEMENT en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 4096,
            }
            resp = requests.post(self.NVIDIA_API_URL, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"[MultiAI] Échec NVIDIA Nemotron: {e}")
            return None

    def _call_groq(self, prompt: str) -> Optional[str]:
        if not self.groq_key or 'ta_cle' in self.groq_key:
            return None
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                max_tokens=4096,
            )
            return resp.choices[0].message.content
        except ImportError:
            logger.debug("groq non installé")
            return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        if not self.gemini_key or 'ta_cle' in self.gemini_key:
            return None
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)
            resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return resp.text
        except Exception:
            pass
        try:
            import google.generativeai as old_genai
            old_genai.configure(api_key=self.gemini_key)
            model = old_genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt).text
        except Exception:
            return None

    def _call_mistral(self, prompt: str) -> Optional[str]:
        if not self.mistral_key or 'ta_cle' in self.mistral_key:
            return None
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            resp = client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
        except ImportError:
            logger.debug("mistralai non installé")
            return None

    def _call_deepseek(self, prompt: str) -> Optional[str]:
        if not self.deepseek_key or 'ta_cle' in self.deepseek_key:
            return None
        try:
            headers = {
                'Authorization': f'Bearer {self.deepseek_key}',
                'Content-Type': 'application/json',
            }
            data = {
                'model': 'deepseek-chat',
                'messages': [{"role": "user", "content": prompt}],
            }
            resp = requests.post(
                'https://api.deepseek.com/chat/completions',
                headers=headers, json=data, timeout=60
            )
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except Exception:
            return None

    def correct_copy(self, corrige_type_text: str, copie_text: str, exam_info: dict, image_paths: list = None) -> dict:
        """
        Corrige une copie d'élève.
        Flux : nemotron-ocr-v1 (OCR images) → nemotron-4-340b-instruct (correction) → fallback Groq/Gemini
        Le paramètre image_paths est conservé pour compatibilité mais l'OCR est fait dans tasks.py.
        """
        note_max = exam_info.get('note_maximale', 20)
        corrige_doc_id = exam_info.get('corrige_doc_id', 'NON_SPECIFIE')
        copie_doc_ids = exam_info.get('copie_doc_ids', [])
        session_id = exam_info.get('session_id', 'NON_SPECIFIE')

        # En-tête de traçabilité pour l'IA
        tracking_header = f"""[TRAÇABILITÉ IA]
- ID Session: {session_id}
- ID Corrigé type: {corrige_doc_id}
- ID Copie(s) élève: {', '.join(copie_doc_ids) if copie_doc_ids else 'Aucun fichier'}

CORRIGE UNIQUEMENT la copie identifiée ci-dessus en utilisant le corrigé type identifié ci-dessus.
NE JAMAIS mélanger avec une autre copie ou un autre corrigé.
"""

        prompt = f"""Tu es un correcteur d'examens professionnel et strict pour les grandes écoles du Bénin.

{tracking_header}

INFORMATIONS DE L'EXAMEN :
- Titre : {exam_info.get('titre', 'Épreuve')}
- Matière : {exam_info.get('matiere', 'Non spécifiée')}
- Note maximale : {note_max}
- Niveau : {exam_info.get('niveau', 'Secondaire')}

CORRIGÉ TYPE (référence absolue pour la correction) — ID: {corrige_doc_id}:
---
{corrige_type_text}
---

COPIE DE L'ÉLÈVE — IDs: {', '.join(copie_doc_ids) if copie_doc_ids else 'Réponses texte directes'}:
---
{copie_text.strip() if copie_text.strip() else "[OCR en cours ou copie manuscrite — évalue selon les éléments disponibles. Si aucun contenu n'est lisible, attribue une note partielle et signale le problème d'extraction dans l'appréciation.]"}
---

INSTRUCTIONS CRITIQUES DE CORRECTION :
1. Analyse rigoureusement chaque partie de la copie par rapport au corrigé type.
2. Sois STRICT et EXIGEANT comme un correcteur de concours.
3. Évalue :
   - La justesse des connaissances (exactitude des faits, formules, définitions)
   - La méthodologie (raisonnement logique, démarche scientifique)
   - La clarté de l'expression (qualité de rédaction, orthographe, structure)
   - La complétude (toutes les questions traitées)
4. Attribue une note précise et justifiée sur {note_max}.
5. Identifie les points forts réels et les lacunes spécifiques.

FORMAT DE RÉPONSE EXIGÉ (JSON valide UNIQUEMENT) :
{{
  "note": <nombre précis entre 0 et {note_max}>,
  "appreciation": "<appréciation globale professionnelle et constructive en 3-4 lignes>",
  "details": [
    {{"question": "<partie ou question traitée>", "points": <nombre>, "max_points": <nombre>, "commentaire": "<explication détaillée de la note>"}}
  ],
  "points_forts_global": "<3 points forts spécifiques identifiés dans la copie>",
  "axes_amelioration": "<3 axes concrets d'amélioration pour l'élève>",
  "niveau_maitrise": "<Excellent|Très Bien|Bien|Assez Bien|Passable|Insuffisant>",
  "recommandations": "<conseils personnalisés pour progresser>"
}}"""

        # ── NVIDIA Nemotron-4-340B en premier (correction après OCR) ──
        raw = None
        if self.nvidia_key and 'ta_cle' not in self.nvidia_key:
            logger.info("[MultiAI] Correction via NVIDIA Nemotron-4-340B")
            raw = self._call_nvidia_nemotron(prompt)
            if raw:
                logger.info("[MultiAI] Succès correction NVIDIA Nemotron")

        # ── Fallback sur Groq/Gemini/Mistral ─────────────────────────
        if not raw:
            logger.info("[MultiAI] Nemotron indisponible — fallback Groq/Gemini/Mistral")
            raw = self.generate(prompt, expect_json=True)

        try:
            clean = raw.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0]
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0]
            return json.loads(clean.strip())
        except Exception:
            return {
                "note": 0,
                "appreciation": f"Erreur de parsing IA. Réponse brute: {raw[:500]}",
                "details": [],
                "points_forts_global": "",
                "axes_amelioration": "Vérifiez les clés API."
            }

    def generate_qcm(self, matiere: str, classe: str, nb_questions: int = 10,
                     difficulte: str = 'moyen', theme: str = '') -> str:
        """Génère un QCM complet strictement sur le chapitre demandé."""
        from qcm.referentiel_programmes import get_referentiel_context, get_langue_for_matiere

        if not theme:
            theme = f"Programme général de {matiere} pour {classe}"

        theme_str = theme.strip()

        # Récupérer le contexte du programme officiel béninois
        referentiel_context = get_referentiel_context(classe, matiere)

        # Déterminer la langue du QCM selon la matière
        langue_code = get_langue_for_matiere(matiere)
        if langue_code == 'en':
            langue_qcm = 'ANGLAIS'
            instruction_langue = 'CRITIQUE : TOUTES les questions, choix de réponses et explications doivent être rédigées EXCLUSIVEMENT EN ANGLAIS. N\'utilise AUCUN mot en français.'
        elif langue_code == 'es':
            langue_qcm = 'ESPAGNOL'
            instruction_langue = 'CRITIQUE : TOUTES les questions, choix de réponses et explications doivent être rédigées EXCLUSIVEMENT EN ESPAGNOL. N\'utilise AUCUN mot en français.'
        elif langue_code == 'de':
            langue_qcm = 'ALLEMAND'
            instruction_langue = 'CRITIQUE : TOUTES les questions, choix de réponses et explications doivent être rédigées EXCLUSIVEMENT EN ALLEMAND. N\'utilise AUCUN mot en français.'
        else:
            langue_qcm = 'FRANÇAIS'
            instruction_langue = 'TOUTES les questions, choix de réponses et explications doivent être rédigés EXCLUSIVEMENT EN FRANÇAIS.'

        prompt = f"""Tu es un professeur expert en {matiere} pour la classe de {classe}.

LANGUE : {instruction_langue}

{referentiel_context}

CHAPITRE CIBLE : {theme_str}

CONTRAINTE ABSOLUE :
- TOUTES les questions doivent porter EXCLUSIVEMENT sur le chapitre "{theme_str}" ou sur les chapitres du programme officiel listés ci-dessus
- NE JAMAIS poser de questions sur un chapitre hors-programme
- NE JAMAIS inventer de notions qui ne sont pas dans les chapitres officiels
- Niveau de difficulté : {difficulte}
- Sois STRICT et RIGOUREUX comme un vrai examen
- Utilise des exemples et contextes béninois quand c'est pertinent (villes : Cotonou, Porto-Novo, Parakou ; histoire du Bénin ; faune et flore locales)

OBJECTIF :
Génère exactement {nb_questions} questions QCM sur "{theme_str}".

RÈGLES STRICTES :
1. Chaque question a exactement 4 choix : A, B, C, D
2. Une SEULE bonne réponse par question
3. Questions précises, pédagogiques, adaptées au niveau {classe}
4. Les distracteurs (mauvaises réponses) doivent être plausibles mais clairement incorrects
5. Numérote les questions de 1 à {nb_questions}
6. La bonne réponse doit être JUSTE et sans ambiguïté
7. {instruction_langue}

FORMAT DE RÉPONSE EXIGÉ — JSON valide UNIQUEMENT, rien d'autre :
```json
{{
  "questions": [
    {{
      "question": "Texte de la question 1 ?",
      "choix": {{
        "A": "Texte du choix A",
        "B": "Texte du choix B",
        "C": "Texte du choix C",
        "D": "Texte du choix D"
      }},
      "correcte": "A"
    }}
  ]
}}
```

Le champ "correcte" indique la lettre (A, B, C ou D) de la bonne réponse.
Retourne UNIQUEMENT le JSON, sans texte avant ni après."""

        return self.generate(prompt, expect_json=True)

    def correct_qcm(self, reponses: str, qcm_original: str, ctx: dict) -> dict:
        """Génère un feedback pédagogique pour un QCM (la note est calculée séparément)."""
        questions = ctx.get('questions', [])
        nb_questions = len(questions)
        nb_reponses = len([r for r in reponses.split('\n') if ':' in r])

        # Langue du feedback
        matiere_lower = ctx.get('matiere', '').lower()
        if matiere_lower in ('anglais', 'anglais lv1', 'anglais lv2', 'english'):
            instruction_langue = 'Rédige le feedback EXCLUSIVEMENT EN ANGLAIS.'
        elif matiere_lower in ('arabe',):
            instruction_langue = 'Rédige le feedback EN ARABE.'
        else:
            instruction_langue = 'Rédige le feedback EN FRANÇAIS.'

        prompt = f"""Tu es un correcteur STRICT et EXIGEANT, spécialiste en {ctx.get('matiere', 'matière')}.

{instruction_langue}

QCM original généré :
---
{qcm_original}
---

Réponses de l'élève :
---
{reponses}
---

INSTRUCTIONS DE CORRECTION STRICTES :
1. Sois SÉVÈRE — ne donne des points QUE pour les réponses exactement correctes
2. Une réponse partiellement correcte mais inexacte = 0 point
3. Identifie les lacunes réelles de l'élève

Retourne UNIQUEMENT un JSON valide sans texte autour :
{{
  "note": 0,
  "bonnes_reponses": 0,
  "total_questions": {nb_questions},
  "appreciation": "<appreciation stricte et honnête>",
  "details": [],
  "points_forts": ["...", "..."],
  "axes_amelioration": ["...", "..."],
  "remediation": "<conseils précis et exigeants pour progresser>"
}}"""

        raw = self.generate(prompt, expect_json=True)
        try:
            clean = raw.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0]
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0]
            return json.loads(clean.strip())
        except Exception:
            # Fallback: calcul manuel basique
            bonnes = 0
            total = len(questions)
            if total > 0:
                bonnes = nb_reponses  # estimation basique
            note = round((bonnes / total) * 20, 1) if total > 0 else 0
            return {
                "note": note,
                "bonnes_reponses": bonnes,
                "total_questions": total,
                "appreciation": "À revoir",
                "details": [],
                "points_forts": [],
                "axes_amelioration": ["Révisez le programme"],
                "remediation": "Consultez votre cours et réessayez."
            }


    def parse_qcm_from_text(self, raw_text: str, matiere: str = '', classe: str = '') -> str:
        """
        Analyse un texte brut (extrait de PDF, TXT, image OCR) et le reformate
        en JSON QCM structuré (même format que generate_qcm).
        """
        context = f" pour {classe} en {matiere}" if matiere or classe else ""
        prompt = f"""Tu es un expert en pédagogie{context}.

Voici un texte brut extrait d'un document QCM (peut être imparfait, contenir des erreurs OCR, etc.) :
---
{raw_text[:6000]}
---

MISSION :
1. Identifie toutes les questions QCM dans ce texte
2. Pour chaque question, identifie ses choix (A, B, C, D ou numérotés)
3. Identifie la bonne réponse si elle est présente (souvent marquée par *, ✓, (correct), ou listée en fin de document)
4. Si la bonne réponse n'est pas explicite, détermine-la toi-même en tant qu'expert

RÈGLES :
- Chaque question doit avoir exactement 4 choix A, B, C, D
- Une seule bonne réponse par question
- Si le texte a moins de 4 choix pour une question, invente des distracteurs plausibles
- Corrige les fautes d'OCR évidentes

Retourne UNIQUEMENT un JSON valide, rien d'autre :
{{
  "questions": [
    {{
      "question": "Texte exact de la question ?",
      "choix": {{
        "A": "Texte du choix A",
        "B": "Texte du choix B",
        "C": "Texte du choix C",
        "D": "Texte du choix D"
      }},
      "correcte": "A"
    }}
  ]
}}"""

        return self.generate(prompt, expect_json=True)


# Instance globale réutilisable
multi_ai = MultiAIService()
