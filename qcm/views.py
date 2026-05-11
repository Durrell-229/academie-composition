import json
import math
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
        theme = request.POST.get('theme', '').strip()

        if not theme:
            messages.error(request, "Veuillez préciser un thème ou chapitre pour des questions cohérentes.")
            return render(request, 'qcm/start.html')

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

    # Correction : calcul déterministe et STRICT basé sur les réponses stockées
    bonnes_reponses_count = 0
    total = len(questions)
    for i, q in enumerate(questions):
        rep = request.POST.get(f'reponse_{i}', '')
        if _check_answer(q, rep):
            bonnes_reponses_count += 1

    # Note stricte : pas d'arrondi supérieur, on tronque à 1 décimale
    note_raw = (bonnes_reponses_count / total) * 20 if total > 0 else 0
    note = math.floor(note_raw * 10) / 10  # tronque à 1 décimale (ex: 13.99 → 13.9)

    # Générer le feedback (IA optionnelle + fallback déterministe)
    appreciation_levels = [
        (0, 5, 'Insuffisant'),
        (5, 8, 'Passable'),
        (8, 10, 'Assez Bien'),
        (10, 14, 'Bien'),
        (14, 18, 'Très Bien'),
        (18, 21, 'Excellent'),
    ]
    appreciation = 'Insuffisant'
    for low, high, label in appreciation_levels:
        if low <= note < high:
            appreciation = label
            break

    feedback = {
        'note': note,
        'bonnes_reponses': bonnes_reponses_count,
        'total_questions': total,
        'appreciation': appreciation,
        'details': [],
        'points_forts': [],
        'axes_amelioration': [],
        'remediation': 'Continuez à réviser pour améliorer vos résultats.',
    }

    # Tentative IA pour enrichir le feedback (sans bloquer si timeout)
    try:
        qcm_original = ctx.get('qcm_original', '')
        if not qcm_original:
            qcm_original = '\n\n'.join([
                f"{q.get('question', '')}\n" + '\n'.join([f"{c.get('label', '')}) {c.get('texte', '')}" for c in q.get('choix', [])])
                for q in questions
            ])
        ai_feedback = multi_ai.correct_qcm(reponses_text, qcm_original, ctx)
        feedback['remediation'] = ai_feedback.get('remediation', feedback['remediation'])
        feedback['points_forts'] = ai_feedback.get('points_forts', [])
        feedback['axes_amelioration'] = ai_feedback.get('axes_amelioration', [])
        if ai_feedback.get('appreciation'):
            feedback['appreciation'] = ai_feedback['appreciation']
    except Exception as e:
        logger.warning(f"IA feedback skipped: {e}")

    # Préparer les détails des questions/réponses
    for i, q in enumerate(questions):
        rep = request.POST.get(f'reponse_{i}', '')
        est_correct = _check_answer(q, rep)
        details_questions.append({
            'question': q.get('question', ''),
            'reponse_eleve': rep,
            'correct': est_correct,
        })

    try:
        with transaction.atomic():
            from bulletins.coefficients_benin import get_coefficient
            from bulletins.services import BulletinService

            # Récupérer la classe et déterminer la série
            classe_nom = ctx.get('classe', '')
            serie = BulletinService._extract_serial(classe_nom)
            matiere_nom = ctx.get('matiere', '')

            # Calculer le coefficient exact de la matière pour cette série/classe
            coefficient = get_coefficient(matiere_nom, serie)

            # 1. Créer le Bulletin professionnel
            annee_scolaire = timezone.now().strftime('%Y-%Y')
            bulletin = Bulletin.objects.create(
                eleve=request.user,
                classe=classe_nom,
                annee_scolaire=annee_scolaire,
                periode=Bulletin.Periode.QCM,
                type_bulletin=Bulletin.TypeBulletin.QCM,
                moyenne_generale=note,
                rang=1,
                effectif_total=1,
                appreciation_ia=feedback.get('appreciation', '') or feedback.get('remediation', ''),
                decision_conseil='Évaluation QCM complétée',
            )

            # 2. Créer la ligne du bulletin AVEC le coefficient exact
            BulletinLigne.objects.create(
                bulletin=bulletin,
                matiere=matiere_nom,
                note=note,
                note_max=20,
                coefficient=coefficient,
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
                matiere=matiere_nom,
                classe=classe_nom,
                theme=ctx.get('theme', ''),
                note_sur_20=note,
                bonnes_reponses=bonnes_reponses_count,
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
    """Parse le texte ou JSON généré par l'IA en structure de questions."""
    # 1. Essayer de parser en JSON d'abord
    try:
        clean = text.strip()
        # Enlever les backticks markdown si présents
        if '```json' in clean:
            clean = clean.split('```json')[1].split('```')[0]
        elif '```' in clean:
            clean = clean.split('```')[1].split('```')[0]

        data = json.loads(clean.strip())
        if 'questions' in data and isinstance(data['questions'], list):
            questions = []
            for i, q in enumerate(data['questions']):
                q_text = q.get('question', '').strip()
                choix_raw = q.get('choix', {})
                correcte = q.get('correcte', '').strip().upper()
                choix = []
                for label in ['A', 'B', 'C', 'D']:
                    choix.append({'label': label, 'texte': choix_raw.get(label, f'Choix {label}')})

                if q_text:
                    questions.append({
                        'id': str(uuid.uuid4())[:8],
                        'question': q_text,
                        'choix': choix,
                        'correcte': correcte,
                    })
            if questions:
                return questions[:nb_questions]
    except (json.JSONDecodeError, KeyError, IndexError):
        pass

    # 2. Fallback : parser le format texte Q1. A) B) C) D)
    questions = []
    lines = text.strip().split('\n')
    current_q = None
    current_choices = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Détection nouvelle question : Q1. Q2. etc. ou 1. 2. etc.
        import re
        q_match = re.match(r'^(?:Q)?(\d+)\.\s+(.+)', line)
        if q_match:
            if current_q:
                current_q['choix'] = current_choices
                questions.append(current_q)
            current_q = {'question': q_match.group(2).strip(), 'id': str(uuid.uuid4())[:8]}
            current_choices = []
        elif line.startswith(('A)', 'B)', 'C)', 'D)', 'a)', 'b)', 'c)', 'd)')):
            label = line[0].upper()
            texte = line[2:].strip()
            current_choices.append({'label': label, 'texte': texte})

    if current_q:
        current_q['choix'] = current_choices
        questions.append(current_q)

    # 3. Compléter si moins de questions que demandé
    while len(questions) < nb_questions:
        questions.append({
            'id': str(uuid.uuid4())[:8],
            'question': f'Question {len(questions) + 1} (non générée par l\'IA)',
            'choix': [
                {'label': 'A', 'texte': 'Choix A'},
                {'label': 'B', 'texte': 'Choix B'},
                {'label': 'C', 'texte': 'Choix C'},
                {'label': 'D', 'texte': 'Choix D'},
            ]
        })

    return questions[:nb_questions]


def _check_answer(question, reponse):
    """Vérifie si une réponse est correcte en comparant avec la réponse stockée."""
    correcte = question.get('correcte', '').strip().upper()
    if not correcte:
        return False
    return reponse.strip().upper() == correcte


@login_required
def download_qcm_bulletin(request, resultat_id):
    """Télécharger le bulletin PDF d'un résultat QCM."""
    from .models import QCMResultat
    from django.http import FileResponse, Http404
    from bulletins.services import BulletinService
    from bulletins.models import Bulletin, BulletinLigne
    from bulletins.coefficients_benin import get_coefficient
    from django.utils import timezone
    from django.db import transaction

    resultat = get_object_or_404(QCMResultat, id=resultat_id, eleve=request.user)

    # Créer le bulletin s'il n'existe pas
    if not resultat.bulletin:
        try:
            with transaction.atomic():
                # Récupérer la série
                serie = BulletinService._extract_serial(resultat.classe)
                coefficient = get_coefficient(resultat.matiere, serie)

                # Créer le bulletin
                annee_scolaire = timezone.now().strftime('%Y-%Y')
                bulletin = Bulletin.objects.create(
                    eleve=resultat.eleve,
                    classe=resultat.classe,
                    annee_scolaire=annee_scolaire,
                    periode=Bulletin.Periode.QCM,
                    type_bulletin=Bulletin.TypeBulletin.QCM,
                    moyenne_generale=resultat.note_sur_20,
                    rang=1,
                    effectif_total=1,
                    appreciation_ia=resultat.feedback_ia.get('appreciation', '') or resultat.feedback_ia.get('remediation', ''),
                    decision_conseil='Évaluation QCM complétée',
                )

                # Créer la ligne du bulletin
                BulletinLigne.objects.create(
                    bulletin=bulletin,
                    matiere=resultat.matiere,
                    note=resultat.note_sur_20,
                    note_max=20,
                    coefficient=coefficient,
                    moyenne_classe=resultat.note_sur_20,
                    appreciation=resultat.feedback_ia.get('remediation', ''),
                )

                # Lier le bulletin au résultat QCM
                resultat.bulletin = bulletin
                resultat.save()

                logger.info(f"Bulletin QCM créé pour {resultat.eleve.email}: {bulletin.id}")
        except Exception as e:
            logger.error(f"Erreur création bulletin QCM: {e}")
            raise Http404("Erreur lors de la création du bulletin")

    # Régénérer le PDF si le fichier n'existe pas
    if not resultat.bulletin.file_pdf:
        try:
            BulletinService.generate_bulletin_qcm_pdf(resultat.bulletin)
            if not resultat.bulletin.file_pdf:
                logger.error(f"PDF généré mais file_pdf est vide pour bulletin {resultat.bulletin.id}")
                raise Http404("Erreur lors de la génération du PDF")
        except Exception as e:
            logger.error(f"Erreur régénération PDF bulletin QCM: {e}", exc_info=True)
            raise Http404(f"Erreur lors de la génération du PDF: {str(e)}")

    return FileResponse(
        resultat.bulletin.file_pdf.open('rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=resultat.bulletin.file_pdf.name.split('/')[-1]
    )
