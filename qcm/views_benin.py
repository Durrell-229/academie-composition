
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
            prompt=f"{prompt}\n\nGénère exactement {nb_questions} questions au format JSON array."
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
