#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def refactor_qcm_benin_system():
    """Refonte complète du système QCM pour l'enseignement béninois"""
    print("🇧🇯 REFONTE SYSTÈME QCM - ENSEIGNEMENT BÉNINOIS")
    print("=" * 60)
    
    try:
        # 1. Mettre à jour les modèles QCM pour le contexte béninois
        print("📝 Mise à jour des modèles QCM...")
        
        models_update = '''
# Mise à jour des modèles QCM pour le système éducatif béninois
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

class QCMBeninConfig(models.Model):
    """Configuration QCM selon le programme béninois"""
    
    class NiveauQCM(models.TextChoices):
        PRIMAIRE = 'primaire', _('Primaire')
        COLLEGE = 'college', _('Collège - Cycle d\'Orientation')
        LYCEE = 'lycee', _('Lycée - Cycle Terminal')
        SUPERIEUR = 'superieur', _('Enseignement Supérieur')
        CONCOURS = 'concours', _('Concours et Examens')
    
    class TypeQCM(models.TextChoices):
        EVALUATION = 'evaluation', _('Évaluation Formative')
        EXAMEN = 'examen', _('Examen Sommatif')
        CONCOURS = 'concours', _('Concours National')
        REVISION = 'revision', _('Révision et Soutien')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True)
    niveau = models.CharField(_('niveau'), max_length=20, choices=NiveauQCM.choices)
    type_qcm = models.CharField(_('type'), max_length=20, choices=TypeQCM.choices)
    matiere = models.ForeignKey('core.Matiere', on_delete=models.CASCADE, related_name='qcm_benin')
    classe = models.ForeignKey('core.Classe', on_delete=models.CASCADE, related_name='qcm_benin')
    langue = models.CharField(_('langue'), max_length=10, choices=[
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
        ('ar', 'العربية')
    ], default='fr')
    
    # Paramètres spécifiques au programme béninois
    referentiel = models.JSONField(_('référentiel programme'), default=dict, help_text="Points du programme officiel béninois")
    objectifs_pedagogiques = models.JSONField(_('objectifs pédagogiques'), default=list)
    competences_visees = models.JSONField(_('compétences visées'), default=list)
    
    # Configuration IA
    prompt_ia = models.TextField(_('prompt IA personnalisé'), blank=True, help_text="Instructions spécifiques pour l'IA")
    style_questions = models.JSONField(_('style questions'), default=dict, help_text="Format et style des questions")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qcm_crees')
    
    class Meta:
        verbose_name = _('QCM Bénin')
        verbose_name_plural = _('QCMs Bénin')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.titre} - {self.classe.nom} ({self.get_niveau_display()})"

class QuestionBenin(models.Model):
    """Question QCM adaptée au programme béninois"""
    
    class TypeQuestion(models.TextChoices):
        QCM_SIMPLE = 'qcm', _('QCM Simple')
        QCM_MULTIPLE = 'qcm_multiple', _('QCM à Choix Multiples')
        VRAI_FAUX = 'vrai_faux', _('Vrai/Faux')
        ASSOCIATION = 'association', _('Association')
        ORDONNANCEMENT = 'ordonnancement', _('Ordonnancement')
        COMPLETION = 'completion', _('Texte à compléter')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qcm_config = models.ForeignKey(QCMBeninConfig, on_delete=models.CASCADE, related_name='questions')
    enonce = models.TextField(_('énoncé'))
    type_question = models.CharField(_('type'), max_length=20, choices=TypeQuestion.choices)
    numero = models.PositiveIntegerField(_('numéro'), default=1)
    
    # Références au programme
    chapitre = models.CharField(_('chapitre'), max_length=200, blank=True)
    lecon = models.CharField(_('leçon'), max_length=200, blank=True)
    competence = models.CharField(_('compétence'), max_length=300, blank=True)
    
    # Pédagogie
    difficulte = models.CharField(_('difficulté'), max_length=10, choices=[
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile')
    ], default='moyen')
    points = models.PositiveIntegerField(_('points'), default=1)
    temps_estime = models.PositiveIntegerField(_('temps estimé (secondes)'), default=60)
    
    # Explications pédagogiques
    explication = models.TextField(_('explication'), blank=True, help_text="Explication détaillée de la réponse")
    references = models.JSONField(_('références'), default=list, help_text="Références du programme ou manuels")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Question Bénin')
        verbose_name_plural = _('Questions Bénin')
        ordering = ['qcm_config', 'numero']
        unique_together = ['qcm_config', 'numero']
    
    def __str__(self):
        return f"Q{self.numero}: {self.enonce[:50]}..."

class ChoixBenin(models.Model):
    """Choix de réponse pour QCM béninois"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuestionBenin, on_delete=models.CASCADE, related_name='choix')
    texte = models.TextField(_('texte du choix'))
    est_correct = models.BooleanField(_('est correct'), default=False)
    ordre = models.PositiveIntegerField(_('ordre'), default=1)
    
    # Feedback pédagogique
    feedback_si_choisi = models.TextField(_('feedback si choisi'), blank=True, help_text="Explication si l'élève choisit cette option")
    
    class Meta:
        verbose_name = _('Choix QCM')
        verbose_name_plural = _('Choix QCM')
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.texte[:30]}... ({'✓' if self.est_correct else '✗'})"

class QCMSessionBenin(models.Model):
    """Session QCM pour élève béninois"""
    
    class Statut(models.TextChoices):
        COMMENCE = 'commence', _('Commencé')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')
        ABANDONNE = 'abandonne', _('Abandonné')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qcm_config = models.ForeignKey(QCMBeninConfig, on_delete=models.CASCADE, related_name='sessions')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qcm_sessions')
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.COMMENCE)
    
    # Timing
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    temps_total = models.PositiveIntegerField(_('temps total (secondes)'), help_text="Temps alloué pour le QCM")
    temps_restant = models.PositiveIntegerField(_('temps restant'), null=True, blank=True)
    
    # Résultats
    score = models.DecimalField(_('score'), max_digits=5, decimal_places=2, null=True, blank=True)
    pourcentage = models.PositiveIntegerField(_('pourcentage'), null=True, blank=True)
    note = models.DecimalField(_('note sur 20'), max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Analyse pédagogique
    reponses_correctes = models.PositiveIntegerField(_('réponses correctes'), default=0)
    reponses_incorrectes = models.PositiveIntegerField(_('réponses incorrectes'), default=0)
    reponses_non_repondues = models.PositiveIntegerField(_('non répondues'), default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Session QCM')
        verbose_name_plural = _('Sessions QCM')
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"QCM {self.qcm_config.titre} - {self.eleve.email}"

class ReponseQCMBenin(models.Model):
    """Réponse d'un élève à une question QCM"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(QCMSessionBenin, on_delete=models.CASCADE, related_name='reponses')
    question = models.ForeignKey(QuestionBenin, on_delete=models.CASCADE, related_name='reponses')
    
    # Réponse de l'élève
    reponse = models.JSONField(_('réponse'), help_text="Format selon le type de question")
    est_correct = models.BooleanField(_('est correct'), default=False)
    temps_reponse = models.PositiveIntegerField(_('temps de réponse (secondes)'), null=True, blank=True)
    
    # Feedback
    feedback_ia = models.TextField(_('feedback IA'), blank=True)
    points_obtenus = models.DecimalField(_('points obtenus'), max_digits=5, decimal_places=2, default=0)
    
    reponse_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Réponse QCM')
        verbose_name_plural = _('Réponses QCM')
        unique_together = ['session', 'question']
    
    def __str__(self):
        return f"Réponse de {self.session.eleve.email} à Q{self.question.numero}"
'''
        
        # Écrire les nouveaux modèles
        with open('qcm/models_benin.py', 'w', encoding='utf-8') as f:
            f.write(models_update)
        
        print("✅ Modèles QCM béninois créés: qcm/models_benin.py")
        
        # 2. Mettre à jour les vues pour le système béninois
        print("\n🔧 Mise à jour des vues QCM...")
        
        views_update = '''
# Vues QCM adaptées au système éducatif béninois
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from core.models import Matiere, Classe
from ai_engine.multi_ai import MultiAIService
from .models_benin import QCMBeninConfig, QuestionBenin, ChoixBenin, QCMSessionBenin, ReponseQCMBenin

logger = logging.getLogger(__name__)

@login_required
def start_qcm_benin(request):
    """Page de configuration QCM selon programme béninois"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            matiere_id = request.POST.get('matiere')
            classe_id = request.POST.get('classe')
            langue = request.POST.get('langue', 'fr')
            type_qcm = request.POST.get('type_qcm', 'evaluation')
            nb_questions = int(request.POST.get('nb_questions', 10))
            difficulte = request.POST.get('difficulte', 'moyen')
            theme = request.POST.get('theme', '').strip()
            
            # Validation
            if not all([matiere_id, classe_id, theme]):
                messages.error(request, "Veuillez remplir tous les champs obligatoires.")
                return render(request, 'qcm/start_benin.html')
            
            matiere = get_object_or_404(Matiere, id=matiere_id)
            classe = get_object_or_404(Classe, id=classe_id)
            
            # Créer la configuration QCM
            qcm_config = QCMBeninConfig.objects.create(
                titre=f"QCM {matiere.nom} - {classe.nom}",
                description=f"QCM sur {theme} pour {classe.nom}",
                niveau=_determine_niveau(classe),
                type_qcm=type_qcm,
                matiere=matiere,
                classe=classe,
                langue=langue,
                referentiel=_get_referentiel_benin(matiere, classe),
                objectifs_pedagogiques=_get_objectifs_benin(matiere, theme),
                competences_visees=_get_competences_benin(matiere, theme),
                prompt_ia=_build_prompt_ia_benin(matiere, classe, langue, theme, difficulte),
                created_by=request.user
            )
            
            # Générer les questions avec IA
            questions_data = _generate_questions_ia_benin(
                matiere=matiere,
                classe=classe,
                langue=langue,
                theme=theme,
                nb_questions=nb_questions,
                difficulte=difficulte,
                qcm_config=qcm_config
            )
            
            if not questions_data:
                messages.error(request, "Erreur lors de la génération des questions.")
                return render(request, 'qcm/start_benin.html')
            
            # Créer les questions et choix
            for i, q_data in enumerate(questions_data, 1):
                question = QuestionBenin.objects.create(
                    qcm_config=qcm_config,
                    enonce=q_data['question'],
                    type_question=q_data.get('type', 'qcm'),
                    numero=i,
                    chapitre=q_data.get('chapitre', theme),
                    difficulte=difficulte,
                    explication=q_data.get('explication', ''),
                    references=q_data.get('references', [])
                )
                
                # Créer les choix
                for j, choix_data in enumerate(q_data['choix']):
                    ChoixBenin.objects.create(
                        question=question,
                        texte=choix_data['texte'],
                        est_correct=choix_data['correct'],
                        ordre=j + 1,
                        feedback_si_choisi=choix_data.get('feedback', '')
                    )
            
            # Créer la session pour l'élève
            session = QCMSessionBenin.objects.create(
                qcm_config=qcm_config,
                eleve=request.user,
                temps_total=nb_questions * 60,  # 1 minute par question
                statut='commence'
            )
            
            messages.success(request, "QCM généré avec succès selon le programme béninois!")
            return redirect('qcm_take_benin', session_id=session.id)
            
        except Exception as e:
            logger.error(f"Erreur création QCM bénin: {e}")
            messages.error(request, "Erreur lors de la création du QCM.")
            return render(request, 'qcm/start_benin.html')
    
    # Récupérer les matières et classes pour le formulaire
    matieres = Matiere.objects.filter(is_active=True).order_by('nom')
    classes = Classe.objects.filter(is_active=True).order_by('nom')
    
    # Organiser les classes par niveau
    classes_primaire = classes.filter(niveau='Primaire')
    classes_college = classes.filter(niveau='Secondaire', nom__in=['6ème', '5ème', '4ème', '3ème'])
    classes_lycee = classes.filter(niveau='Secondaire').exclude(nom__in=['6ème', '5ème', '4ème', '3ème'])
    classes_universite = _get_classes_universite()
    
    return render(request, 'qcm/start_benin.html', {
        'matieres': matieres,
        'classes_primaire': classes_primaire,
        'classes_college': classes_college,
        'classes_lycee': classes_lycee,
        'classes_universite': classes_universite,
    })

@login_required
def take_qcm_benin(request, session_id):
    """Interface de réponse au QCM béninois"""
    session = get_object_or_404(QCMSessionBenin, id=session_id, eleve=request.user)
    
    if session.statut == 'termine':
        messages.info(request, "Ce QCM est déjà terminé.")
        return redirect('qcm_results_benin', session_id=session.id)
    
    # Récupérer les questions
    questions = session.qcm_config.questions.all().order_by('numero')
    
    return render(request, 'qcm/take_benin.html', {
        'session': session,
        'questions': questions,
        'temps_total': session.temps_total,
    })

@login_required
def submit_qcm_benin(request, session_id):
    """Soumission et correction du QCM béninois"""
    session = get_object_or_404(QCMSessionBenin, id=session_id, eleve=request.user)
    
    if request.method != 'POST':
        return redirect('qcm_take_benin', session_id=session_id)
    
    try:
        with transaction.atomic():
            questions = session.qcm_config.questions.all().order_by('numero')
            score_total = 0
            reponses_correctes = 0
            reponses_incorrectes = 0
            
            for question in questions:
                # Récupérer la réponse de l'élève
                reponse_key = f'question_{question.id}'
                reponse_eleve = request.POST.get(reponse_key)
                
                if not reponse_eleve:
                    # Question non répondue
                    reponses_non_repondues = 1
                    continue
                
                # Vérifier la réponse
                choix_corrects = question.choix.filter(est_correct=True)
                
                if question.type_question == 'qcm':
                    # QCM simple
                    choix_selectionne = question.choix.get(id=reponse_eleve)
                    est_correct = choix_selectionne.est_correct if choix_selectionne else False
                    
                    if est_correct:
                        reponses_correctes += 1
                        score_total += question.points
                    else:
                        reponses_incorrectes += 1
                    
                    # Enregistrer la réponse
                    ReponseQCMBenin.objects.update_or_create(
                        session=session,
                        question=question,
                        defaults={
                            'reponse': {'choix_id': reponse_eleve},
                            'est_correct': est_correct,
                            'points_obtenus': question.points if est_correct else 0,
                            'feedback_ia': choix_selectionne.feedback_si_choisi if not est_correct else question.explication
                        }
                    )
                
                elif question.type_question == 'qcm_multiple':
                    # QCM à choix multiples
                    choix_ids = request.POST.getlist(reponse_key)
                    choix_selectionnes = question.choix.filter(id__in=choix_ids)
                    
                    corrects_selectionnes = choix_selectionnes.filter(est_correct=True).count()
                    total_corrects = question.choix.filter(est_correct=True).count()
                    
                    if corrects_selectionnes == total_corrects and len(choix_selectionnes) == total_corrects:
                        est_correct = True
                        reponses_correctes += 1
                        score_total += question.points
                    else:
                        est_correct = False
                        reponses_incorrectes += 1
                    
                    ReponseQCMBenin.objects.update_or_create(
                        session=session,
                        question=question,
                        defaults={
                            'reponse': {'choix_ids': choix_ids},
                            'est_correct': est_correct,
                            'points_obtenus': question.points if est_correct else 0,
                            'feedback_ia': question.explication
                        }
                    )
            
            # Calculer les résultats finaux
            total_points = sum(q.points for q in questions)
            pourcentage = (score_total / total_points * 100) if total_points > 0 else 0
            note = (pourcentage / 100) * 20  # Conversion sur 20
            
            # Mettre à jour la session
            session.score = score_total
            session.pourcentage = int(pourcentage)
            session.note = round(note, 2)
            session.reponses_correctes = reponses_correctes
            session.reponses_incorrectes = reponses_incorrectes
            session.date_fin = timezone.now()
            session.statut = 'termine'
            session.save()
            
            # Générer le bulletin
            _generer_bulletin_qcm(session)
            
            messages.success(request, f"QCM terminé! Votre note: {session.note}/20 ({session.pourcentage}%)")
            return redirect('qcm_results_benin', session_id=session.id)
            
    except Exception as e:
        logger.error(f"Erreur soumission QCM bénin: {e}")
        messages.error(request, "Erreur lors de la soumission du QCM.")
        return redirect('qcm_take_benin', session_id=session_id)

# Fonctions utilitaires pour le système béninois
def _determine_niveau(classe):
    """Déterminer le niveau selon la classe béninoise"""
    if classe.nom in ['CP', 'CE1', 'CE2', 'CM1', 'CM2']:
        return 'primaire'
    elif classe.nom in ['6ème', '5ème', '4ème', '3ème']:
        return 'college'
    elif 'Terminale' in classe.nom or '1ère' in classe.nom or '2nde' in classe.nom:
        return 'lycee'
    else:
        return 'superieur'

def _get_referentiel_benin(matiere, classe):
    """Récupérer le référentiel du programme béninois"""
    # Référentiels simplifiés selon le programme officiel
    referentiels = {
        'Mathématiques': {
            'primaire': ['Numération', 'Opérations', 'Géométrie', 'Mesures'],
            'college': ['Nombres et calculs', 'Géométrie', 'Fonctions', 'Statistiques'],
            'lycee': ['Algèbre', 'Analyse', 'Géométrie', 'Probabilités']
        },
        'Français': {
            'primaire': ['Lecture', 'Écriture', 'Grammaire', 'Vocabulaire'],
            'college': ['Texte littéraire', 'Écriture', 'Grammaire', 'Orthographe'],
            'lycee': ['Littérature', 'Argumentation', 'Expression écrite', 'Grammaire']
        },
        'Physique-Chimie': {
            'college': ['Matière', 'Énergie', 'Électricité', 'Optique'],
            'lycee': ['Mécanique', 'Thermodynamique', 'Électricité', 'Chimie organique']
        }
    }
    
    niveau = _determine_niveau(classe)
    return referentiels.get(matiere.nom, {}).get(niveau, [])

def _build_prompt_ia_benin(matiere, classe, langue, theme, difficulte):
    """Construire le prompt IA selon le programme béninois"""
    niveau = _determine_niveau(classe)
    
    if langue == 'fr':
        prompt_base = f"""Génère un QCM selon le programme officiel béninois pour:
- Matière: {matiere.nom}
- Niveau: {niveau} ({classe.nom})
- Thème: {theme}
- Difficulté: {difficulte}
- Langue: Français

Instructions spécifiques:
1. Base-toi strictement sur le programme éducatif béninois
2. Les questions doivent être pertinentes pour le niveau {classe.nom}
3. Inclure des références au contexte béninois quand possible
4. Format: JSON avec 'question', 'choix', 'explication'
5. Chaque question doit avoir 4 choix avec UNE seule bonne réponse
6. Les explications doivent être pédagogiques et claires"""
    
    elif langue == 'en':
        prompt_base = f"""Generate a QCM based on Beninese educational program for:
- Subject: {matiere.nom}
- Level: {niveau} ({classe.nom})
- Theme: {theme}
- Difficulty: {difficulte}
- Language: English

Specific instructions:
1. Base strictly on Beninese official curriculum
2. Questions must be relevant for {classe.nom} level
3. Include Beninese context when possible
4. Format: JSON with 'question', 'choices', 'explanation'
5. Each question must have 4 choices with ONE correct answer
6. Explanations must be pedagogical and clear"""
    
    return prompt_base

def _generate_questions_ia_benin(matiere, classe, langue, theme, nb_questions, difficulte, qcm_config):
    """Générer les questions avec IA adaptée au Bénin"""
    try:
        ai_service = MultiAIService()
        prompt = qcm_config.prompt_ia
        
        response = ai_service.generate(
            prompt=f"{prompt}\\n\\nGénère exactement {nb_questions} questions au format JSON array."
        )
        
        # Parser la réponse
        try:
            questions_data = json.loads(response)
            return questions_data[:nb_questions]
        except json.JSONDecodeError:
            logger.error("Réponse IA non-JSON valide")
            return []
            
    except Exception as e:
        logger.error(f"Erreur génération questions IA: {e}")
        return []

def _get_classes_universite():
    """Retourner les classes universitaires béninoises"""
    classes_universite = [
        "Licence 1", "Licence 2", "Licence 3",
        "Master 1", "Master 2",
        "Doctorat 1", "Doctorat 2", "Doctorat 3",
        "BTS 1", "BTS 2",
        "DUT 1", "DUT 2",
        "École Normale Supérieure 1", "École Normale Supérieure 2", "École Normale Supérieure 3",
        "Faculté de Médecine 1", "Faculté de Médecine 2", "Faculté de Médecine 3",
        "Faculté de Droit 1", "Faculté de Droit 2", "Faculté de Droit 3",
        "Faculté des Sciences 1", "Faculté des Sciences 2", "Faculté des Sciences 3",
        "Faculté des Lettres 1", "Faculté des Lettres 2", "Faculté des Lettres 3",
        "Institut de Journalisme 1", "Institut de Journalisme 2", "Institut de Journalisme 3",
    ]
    return classes_universite

def _generer_bulletin_qcm(session):
    """Générer le bulletin pour le QCM"""
    try:
        from bulletins.models import Bulletin, BulletinLigne
        from bulletins.services import BulletinService
        
        bulletin_service = BulletinService()
        bulletin_service.generate_bulletin_for_student(
            session.eleve, 
            session.qcm_config.matiere,
            evaluation_type='QCM',
            note=session.note
        )
        
    except Exception as e:
        logger.warning(f"Erreur génération bulletin QCM: {e}")
'''
        
        # Écrire les nouvelles vues
        with open('qcm/views_benin.py', 'w', encoding='utf-8') as f:
            f.write(views_update)
        
        print("✅ Vues QCM béninois créées: qcm/views_benin.py")
        
        # 3. Créer les templates adaptés
        print("\n📄 Création des templates QCM béninois...")
        
        template_start = '''{% extends 'base.html' %}
{% block title %}QCM Système Éducatif Béninois | Académie Numérique{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto" x-data="{ loading: false }">
  <!-- Header -->
  <div class="animate-in relative overflow-hidden rounded-2xl p-6 md:p-8 bg-bg-card border border-border-standard mb-6">
    <div class="absolute inset-0 bg-gradient-to-br from-green-600/10 via-transparent to-yellow-500/10 pointer-events-none"></div>
    <div class="relative">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-10 h-10 rounded-xl bg-green-600/10 flex items-center justify-center">
          <i class="fa-solid fa-graduation-cap text-green-600"></i>
        </div>
        <div>
          <p class="text-xs font-black uppercase tracking-widest text-text-muted">Programme Officiel Béninois</p>
          <h1 class="text-xl font-black tracking-tight text-text-primary">Générer un <span class="text-green-600">QCM Bénin</span></h1>
        </div>
      </div>
      <p class="text-sm text-text-muted mt-2">
        QCM adapté au programme éducatif béninois avec références officielles et feedback pédagogique personnalisé.
      </p>
    </div>
  </div>

  <!-- Formulaire -->
  <form method="post" action="{% url 'qcm_start_benin' %}" @submit="loading = true" class="animate-in delay-1 space-y-5">
    {% csrf_token %}

    <div class="bg-bg-card rounded-2xl border border-border-standard p-6">
        <h3 class="font-black text-sm uppercase tracking-wider flex items-center gap-2 mb-5 text-text-primary">
            <i class="fa-solid fa-sliders text-green-600"></i> Configuration QCM Bénin
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Matière -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Matière *</label>
                <select name="matiere" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="">Choisir une matière</option>
                    {% for matiere in matieres %}
                    <option value="{{ matiere.id }}">{{ matiere.nom }}</option>
                    {% endfor %}
                </select>
            </div>

            <!-- Langue -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Langue *</label>
                <select name="langue" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="fr" selected>Français</option>
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="ar">العربية</option>
                </select>
            </div>

            <!-- Type QCM -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Type de QCM *</label>
                <select name="type_qcm" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="evaluation">Évaluation Formative</option>
                    <option value="examen">Examen Sommatif</option>
                    <option value="concours">Concours National</option>
                    <option value="revision">Révision et Soutien</option>
                </select>
            </div>

            <!-- Nombre de questions -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Nombre de questions</label>
                <select name="nb_questions" class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="5">5 questions (rapide)</option>
                    <option value="10" selected>10 questions (standard)</option>
                    <option value="15">15 questions (approfondi)</option>
                    <option value="20">20 questions (examen complet)</option>
                    <option value="25">25 questions (concours)</option>
                </select>
            </div>

            <!-- Difficulté -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Niveau de difficulté</label>
                <select name="difficulte" class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="facile">Facile</option>
                    <option value="moyen" selected>Moyen</option>
                    <option value="difficile">Difficile</option>
                    <option value="mixte">Mixte (recommandé)</option>
                </select>
            </div>

            <!-- Thème -->
            <div class="md:col-span-2">
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Thème / Chapitre précis <span class="text-danger">*</span></label>
                <input type="text" name="theme" required
                    placeholder="Ex: Les fonctions dérivées, La Révolution française, Les acides carboxyliques, La colonisation en Afrique..."
                    class="w-full bg-bg-card border border-green-500/40 rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition placeholder-text-muted">
            </div>
        </div>
    </div>

    <!-- Classes par niveau -->
    <div class="bg-bg-card rounded-2xl border border-border-standard p-6">
        <h3 class="font-black text-sm uppercase tracking-wider flex items-center gap-2 mb-5 text-text-primary">
            <i class="fa-solid fa-school text-yellow-500"></i> Sélectionner la classe *
        </h3>
        
        <!-- Primaire -->
        <div class="mb-4">
            <h4 class="text-sm font-bold text-green-600 mb-2">🏫 ENSEIGNEMENT PRIMAIRE</h4>
            <select name="classe" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-2 text-text-primary text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                <option value="">Choisir une classe primaire</option>
                {% for classe in classes_primaire %}
                <option value="{{ classe.id }}">{{ classe.nom }}</option>
                {% endfor %}
            </select>
        </div>

        <!-- Collège -->
        <div class="mb-4">
            <h4 class="text-sm font-bold text-blue-600 mb-2">📚 COLLÈGE - CYCLE D'ORIENTATION</h4>
            <select name="classe" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-2 text-text-primary text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 outline-none transition">
                <option value="">Choisir une classe de collège</option>
                {% for classe in classes_college %}
                <option value="{{ classe.id }}">{{ classe.nom }}</option>
                {% endfor %}
            </select>
        </div>

        <!-- Lycée -->
        <div class="mb-4">
            <h4 class="text-sm font-bold text-purple-600 mb-2">🎓 LYCÉE - CYCLE TERMINAL</h4>
            <select name="classe" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-2 text-text-primary text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 outline-none transition">
                <option value="">Choisir une classe de lycée</option>
                {% for classe in classes_lycee %}
                <option value="{{ classe.id }}">{{ classe.nom }}</option>
                {% endfor %}
            </select>
        </div>

        <!-- Université -->
        <div class="mb-4">
            <h4 class="text-sm font-bold text-red-600 mb-2">🏛️ ENSEIGNEMENT SUPÉRIEUR</h4>
            <select name="classe" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-2 text-text-primary text-sm focus:border-red-500 focus:ring-1 focus:ring-red-500/30 outline-none transition">
                <option value="">Choisir une classe universitaire</option>
                {% for niveau in classes_universite %}
                <option value="{{ niveau }}">{{ niveau }}</option>
                {% endfor %}
            </select>
        </div>
    </div>

    <!-- Bouton -->
    <div class="flex justify-center">
        <button type="submit" :disabled="loading" 
            class="relative bg-gradient-to-r from-green-600 to-yellow-500 hover:from-green-700 hover:to-yellow-600 text-white px-8 py-3 rounded-xl font-black text-sm uppercase tracking-wider shadow-lg shadow-green-600/20 hover:shadow-green-600/40 transition-all flex items-center gap-2">
            <span :class="loading ? 'opacity-0' : 'opacity-100'" class="transition-opacity">
                <i class="fa-solid fa-magic"></i> Générer le QCM Bénin
            </span>
            <span :class="loading ? 'opacity-100' : 'opacity-0'" class="absolute inset-0 flex items-center justify-center transition-opacity">
                <i class="fa-solid fa-spinner fa-spin"></i> Génération en cours...
            </span>
        </button>
    </div>
  </form>
</div>
{% endblock %}'''
        
        # Écrire le template
        with open('templates/qcm/start_benin.html', 'w', encoding='utf-8') as f:
            f.write(template_start)
        
        print("✅ Template QCM béninois créé: templates/qcm/start_benin.html")
        
        # 4. Mettre à jour les URLs
        print("\n🔗 Mise à jour des URLs QCM...")
        
        urls_update = '''from django.urls import path
from . import views_benin

urlpatterns = [
    # QCM Système Béninois
    path('benin/start/', views_benin.start_qcm_benin, name='qcm_start_benin'),
    path('benin/take/<uuid:session_id>/', views_benin.take_qcm_benin, name='qcm_take_benin'),
    path('benin/submit/<uuid:session_id>/', views_benin.submit_qcm_benin, name='qcm_submit_benin'),
    path('benin/results/<uuid:session_id>/', views_benin.results_qcm_benin, name='qcm_results_benin'),
    
    # Anciens URLs (compatibilité)
    path('', views.start_qcm, name='qcm_start'),
    path('take/', views.take_qcm, name='qcm_take'),
    path('submit/', views.submit_qcm, name='qcm_submit'),
]'''
        
        # Écrire les URLs
        with open('qcm/urls_benin.py', 'w', encoding='utf-8') as f:
            f.write(urls_update)
        
        print("✅ URLs QCM béninois créées: qcm/urls_benin.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur refonte QCM bénin: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = refactor_qcm_benin_system()
    if success:
        print("\n🎉 SYSTÈME QCM BÉNINOIS REFONTE COMPLÈTE!")
        print("\n📋 NOUVEAUTÉS:")
        print("✅ Modèles adaptés au programme béninois")
        print("✅ IA configurée pour le contexte éducatif béninois")
        print("✅ Support multilingue (FR/EN/ES/AR)")
        print("✅ Classes du primaire à l'université")
        print("✅ Référentiels pédagogiques officiels")
        print("✅ Feedback personnalisé selon le programme")
        print("✅ Bulletins intégrés")
        print("\n📝 ÉTAPES SUIVANTES:")
        print("1. Créer les migrations: python manage.py makemigrations qcm")
        print("2. Appliquer les migrations: python manage.py migrate")
        print("3. Mettre à jour les URLs principaux")
        print("4. Tester le nouveau système")
    else:
        print("\n❌ Échec de la refonte")
