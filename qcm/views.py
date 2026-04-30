import json
import uuid
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from core.models import Matiere
from .models import QuestionBank, Choice, QCMExam, QCMExamQuestion, QCMAnswer, QCMAnswer
from compositions.models import CompositionSession
from exams.models import Exam
from ai_engine.multi_ai import multi_ai

logger = logging.getLogger(__name__)


@login_required
def start_qcm(request):
    """Page de configuration et génération d'un QCM par IA."""
    if request.method == 'POST':
        matiere_slug = request.POST.get('matiere', '')
        classe = request.POST.get('classe', '')
        nb_questions = int(request.POST.get('nb_questions', 10))
        difficulte = request.POST.get('difficulte', 'moyen')
        theme = request.POST.get('theme', '')

        matiere = Matiere.objects.filter(slug=matiere_slug).first()

        try:
            # Générer le QCM via IA
            qcm_text = multi_ai.generate_qcm(matiere.nom if matiere else 'Général', classe, nb_questions, difficulte, theme)
        except Exception as e:
            logger.error(f"Erreur génération QCM: {e}")
            messages.error(request, "Erreur lors de la génération du QCM. Veuillez réessayer plus tard.")
            return render(request, 'qcm/start.html')

        # Parser les questions depuis le texte généré
        questions_data = _parse_qcm_text(qcm_text, nb_questions)

        if not questions_data:
            messages.error(request, "Le QCM généré est vide. Veuillez réessayer.")
            return render(request, 'qcm/start.html')

        # Stocker en session pour la page de réponse
        request.session['qcm_context'] = {
            'matiere': matiere.nom if matiere else 'Général',
            'matiere_slug': matiere_slug,
            'classe': classe,
            'nb_questions': nb_questions,
            'difficulte': difficulte,
            'theme': theme,
            'questions': questions_data,
        }

        return render(request, 'qcm/take.html', {
            'questions': questions_data,
            'matiere': matiere.nom if matiere else 'Général',
            'classe': classe,
            'nb_questions': nb_questions,
            'theme': theme,
        })

    return render(request, 'qcm/start.html')


@login_required
def take_qcm(request):
    """Page de réponse au QCM avec interface de clic."""
    ctx = request.session.get('qcm_context')
    if not ctx or 'questions' not in ctx:
        messages.error(request, "Aucun QCM en cours. Veuillez d'abord générer un QCM.")
        return redirect('qcm_start')
    
    return render(request, 'qcm/take.html', {
        'questions': ctx['questions'],
        'matiere': ctx['matiere'],
        'classe': ctx.get('classe', ''),
        'nb_questions': ctx['nb_questions'],
        'theme': ctx.get('theme', ''),
    })


@login_required
def submit_qcm(request):
    """Soumission et correction du QCM."""
    if request.method != 'POST':
        return redirect('qcm_start')

    ctx = request.session.get('qcm_context', {})
    questions = ctx.get('questions', [])
    
    # Récupérer les réponses
    reponses = {}
    for i, q in enumerate(questions):
        q_id = q.get('id', f'Q{i+1}')
        rep = request.POST.get(f'reponse_{i}', '')
        if rep:
            reponses[f'Q{i+1}'] = rep
    
    # Construire le texte des réponses pour l'IA
    reponses_text = '\n'.join([f'{k}: {v}' for k, v in reponses.items()])
    
    # Correction IA
    qcm_original = ctx.get('qcm_original', '')
    if not qcm_original:
        # Reconstruire le QCM original depuis les questions
        qcm_original = '\n\n'.join([f"{q.get('question', '')}\n" + '\n'.join([f"{c.get('label', '')}) {c.get('texte', '')}" for c in q.get('choix', [])]) for q in questions])
    
    feedback = multi_ai.correct_qcm(reponses_text, qcm_original, ctx)
    note = feedback.get('note', 0)
    
    # Sauvegarder en DB si un examen QCM est associé
    qcm_exam_id = ctx.get('qcm_exam_id')
    session_id = ctx.get('session_id')
    
    if qcm_exam_id and session_id:
        try:
            with transaction.atomic():
                qcm_exam = QCMExam.objects.get(id=qcm_exam_id)
                session = CompositionSession.objects.get(id=session_id)
                
                # Sauvegarder chaque réponse
                for i, q in enumerate(questions):
                    q_id = q.get('db_id')  # ID de QuestionBank si stocké
                    if q_id:
                        reponse = request.POST.get(f'reponse_{i}', '')
                        est_correct = _check_answer(q, reponse)
                        points = float(qcm_exam.points_bonne_reponse) if est_correct else 0
                        
                        QCMAnswer.objects.update_or_create(
                            session=session,
                            question_id=q_id,
                            defaults={
                                'choix_selectionnes': reponse.split(', ') if reponse else [],
                                'est_correct': est_correct,
                                'points_obtenus': points,
                            }
                        )
        except Exception as e:
            logger.error(f"Erreur sauvegarde QCM: {e}")
    
    # Nettoyer la session
    request.session.pop('qcm_context', None)
    request.session.pop('qcm_generated', None)

    return render(request, 'qcm/result.html', {
        'feedback': feedback,
        'note': note,
        'matiere': ctx.get('matiere', ''),
        'classe': ctx.get('classe', ''),
        'reponses': reponses,
        'questions': questions,
    })


def _parse_qcm_text(text, nb_questions):
    """Parse le texte généré par l'IA en structure de questions."""
    questions = []
    lines = text.strip().split('\n')
    current_q = None
    current_choices = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Détection nouvelle question : Q1. Q2. etc.
        if line.startswith('Q') and '.' in line[:4]:
            if current_q:
                current_q['choix'] = current_choices
                questions.append(current_q)
            current_q = {'question': line.split('.', 1)[1].strip() if '.' in line else line, 'id': str(uuid.uuid4())[:8]}
            current_choices = []
        elif line.startswith(('A)', 'B)', 'C)', 'D)', 'a)', 'b)', 'c)', 'd)')):
            label = line[0].upper()
            texte = line[2:].strip()
            current_choices.append({'label': label, 'texte': texte})
    
    if current_q:
        current_q['choix'] = current_choices
        questions.append(current_q)
    
    # Compléter si moins de questions que demandé
    while len(questions) < nb_questions:
        questions.append({
            'id': str(uuid.uuid4())[:8],
            'question': f'Question {len(questions) + 1} (non générée)',
            'choix': [
                {'label': 'A', 'texte': 'Choix A'},
                {'label': 'B', 'texte': 'Choix B'},
                {'label': 'C', 'texte': 'Choix C'},
                {'label': 'D', 'texte': 'Choix D'},
            ]
        })
    
    return questions[:nb_questions]


def _check_answer(question, reponse):
    """Vérifie si une réponse est correcte (version simple)."""
    # Cette fonction sera améliorée quand l'IA retournera les bonnes réponses
    return False
