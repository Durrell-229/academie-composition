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
        matiere_nom = request.POST.get('matiere', '')
        classe = request.POST.get('classe', '')
        nb_questions = int(request.POST.get('nb_questions', 10))
        difficulte = request.POST.get('difficulte', 'moyen')
        theme = request.POST.get('theme', '')

        # Chercher par nom
        matiere = Matiere.objects.filter(nom=matiere_nom).first()

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
            'matiere_slug': matiere_nom,
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
    """Soumission et correction du QCM avec génération de bulletin professionnel."""
    from bulletins.models import Bulletin, BulletinLigne
    from bulletins.services import BulletinService
    from .models import QCMResultat
    from django.utils import timezone

    if request.method != 'POST':
        return redirect('qcm_start')

    ctx = request.session.get('qcm_context', {})
    questions = ctx.get('questions', [])

    # Récupérer les réponses
    reponses = {}
    details_questions = []
    bonnes_reponses = 0
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
        qcm_original = '\n\n'.join([f"{q.get('question', '')}\n" + '\n'.join([f"{c.get('label', '')}) {c.get('texte', '')}" for c in q.get('choix', [])]) for q in questions])

    feedback = multi_ai.correct_qcm(reponses_text, qcm_original, ctx)
    note = feedback.get('note', 0)
    bonnes_reponses = feedback.get('bonnes_reponses', 0)

    # Préparer les détails des questions/réponses
    for i, q in enumerate(questions):
        rep = request.POST.get(f'reponse_{i}', '')
        est_correct = _check_answer(q, rep)
        if est_correct:
            bonnes_reponses_detail = bonnes_reponses  # approximation
        details_questions.append({
            'question': q.get('question', ''),
            'reponse_eleve': rep,
            'correct': est_correct,
        })

    try:
        with transaction.atomic():
            # 1. Créer le Bulletin professionnel
            annee_scolaire = timezone.now().strftime('%Y-%Y')
            bulletin = Bulletin.objects.create(
                eleve=request.user,
                classe=ctx.get('classe', ''),
                annee_scolaire=annee_scolaire,
                periode=Bulletin.Periode.QCM,
                type_bulletin=Bulletin.TypeBulletin.PROFESSIONNEL,
                moyenne_generale=note,
                rang=1,
                effectif_total=1,
                appreciation_ia=feedback.get('appreciation', '') or feedback.get('remediation', ''),
                decision_conseil='Évaluation QCM complétée',
            )

            # 2. Créer la ligne du bulletin
            BulletinLigne.objects.create(
                bulletin=bulletin,
                matiere=ctx.get('matiere', ''),
                note=note,
                note_max=20,
                moyenne_classe=note,
                appreciation=feedback.get('remediation', ''),
            )

            # 3. Générer le PDF
            try:
                BulletinService.generate_bulletin_qcm_pdf(bulletin)
            except Exception as e:
                logger.error(f"Erreur génération PDF bulletin QCM: {e}")

            # 4. Créer le QCMResultat
            resultat = QCMResultat.objects.create(
                eleve=request.user,
                matiere=ctx.get('matiere', ''),
                classe=ctx.get('classe', ''),
                theme=ctx.get('theme', ''),
                note_sur_20=note,
                bonnes_reponses=feedback.get('bonnes_reponses', len([r for r in reponses.values() if r])),
                total_questions=len(questions),
                questions_data={'questions': details_questions, 'reponses': reponses},
                feedback_ia=feedback,
                bulletin=bulletin,
            )
    except Exception as e:
        logger.error(f"Erreur création bulletin QCM: {e}")
        resultat = None

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
        'resultat_id': resultat.id if resultat else None,
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
    """Vérifie si une réponse est correcte selon les connaissances académiques."""
    from ai_engine.multi_ai import multi_ai

    choix = question.get('choix', [])
    question_text = question.get('question', '')

    # Construire le prompt pour l'IA
    prompt_check = f"""Question: {question_text}
Choix:
A) {choix[0]['texte'] if len(choix) > 0 else ''}
B) {choix[1]['texte'] if len(choix) > 1 else ''}
C) {choix[2]['texte'] if len(choix) > 2 else ''}
D) {choix[3]['texte'] if len(choix) > 3 else ''}

Réponse de l'élève: {reponse}

Quelle est la bonne réponse (A, B, C ou D) ? Retourne UNIQUEMENT la lettre de la bonne réponse, rien d'autre."""

    try:
        bonne_reponse = multi_ai.generate(prompt_check).strip().upper()
        # Extraire juste la lettre
        for lettre in ['A', 'B', 'C', 'D']:
            if lettre in bonne_reponse:
                return reponse.upper() == lettre
        return False
    except Exception:
        return False


@login_required
def download_qcm_bulletin(request, resultat_id):
    """Télécharger le bulletin PDF d'un résultat QCM."""
    from .models import QCMResultat
    from django.http import FileResponse, Http404

    resultat = get_object_or_404(QCMResultat, id=resultat_id, eleve=request.user)

    if not resultat.bulletin or not resultat.bulletin.file_pdf:
        raise Http404("Bulletin non disponible")

    return FileResponse(
        resultat.bulletin.file_pdf.open('rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=resultat.bulletin.file_pdf.name.split('/')[-1]
    )
