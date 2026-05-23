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
from .models import QuestionBank, Choice, QCMExam, QCMExamQuestion, QCMAnswer
from compositions.models import CompositionSession
from exams.models import Exam
from ai_engine.multi_ai import multi_ai
from subscriptions.decorators import qcm_pro_required, prof_required

logger = logging.getLogger(__name__)


@login_required
def qcm_paywall(request):
    """Page paywall : l'élève n'a pas d'abonnement actif."""
    from payments.models import PlanAbonnementScolaire
    etablissement = getattr(request.user, 'etablissement', None)
    plans = PlanAbonnementScolaire.objects.filter(is_actif=True, visible_sur_site=True).order_by('prix_mensuel')
    if etablissement:
        plans = plans.filter(etablissement=etablissement)
    return render(request, 'qcm/paywall.html', {'plans': plans})


@login_required
@qcm_pro_required
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
@qcm_pro_required
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
@qcm_pro_required
def submit_qcm(request):
    """Soumission et correction du QCM avec génération de bulletin professionnel."""
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
        resultat = QCMResultat.objects.create(
            eleve=request.user,
            matiere=ctx.get('matiere', ''),
            classe=ctx.get('classe', ''),
            theme=ctx.get('theme', ''),
            note_sur_20=note,
            bonnes_reponses=bonnes_reponses_count,
            total_questions=len(questions),
            questions_data={'questions': details_questions, 'reponses': reponses},
            feedback_ia=feedback,
        )
    except Exception as e:
        logger.error(f"Erreur création résultat QCM: {e}")
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


# ═══════════════════════════════════════════
#  DASHBOARD PROFESSEUR — GESTION DES QCM
# ═══════════════════════════════════════════

@login_required
@prof_required
def prof_liste_qcm(request):
    """Liste des QCM créés par ce professeur."""
    questions = (
        QuestionBank.objects
        .filter(createur=request.user)
        .prefetch_related('choices')
        .order_by('-created_at')
    )
    return render(request, 'qcm/prof_liste.html', {'questions': questions})


@login_required
@prof_required
def prof_creer_qcm(request):
    """Créer un QCM manuellement (questions + choix + corrigé type)."""
    matieres = Matiere.objects.all().order_by('nom')

    if request.method == 'POST':
        matiere_id = request.POST.get('matiere_id')
        difficulte = request.POST.get('difficulte', 'moyen')
        est_publique = request.POST.get('est_publique') == 'on'

        matiere = Matiere.objects.filter(id=matiere_id).first()

        textes = request.POST.getlist('texte_question[]')
        choix_a = request.POST.getlist('choix_a[]')
        choix_b = request.POST.getlist('choix_b[]')
        choix_c = request.POST.getlist('choix_c[]')
        choix_d = request.POST.getlist('choix_d[]')
        correctes = request.POST.getlist('correcte[]')

        if not textes or not any(t.strip() for t in textes):
            messages.error(request, "Ajoutez au moins une question.")
            return render(request, 'qcm/prof_creer.html', {'matieres': matieres})

        created = 0
        with transaction.atomic():
            for i, texte in enumerate(textes):
                if not texte.strip():
                    continue
                question = QuestionBank.objects.create(
                    matiere=matiere,
                    createur=request.user,
                    texte=texte.strip(),
                    difficulte=difficulte,
                    est_publique=est_publique,
                    generee_par_ia=False,
                )
                correcte = correctes[i].upper() if i < len(correctes) else 'A'
                for ordre, (label, choix_list) in enumerate([
                    ('A', choix_a), ('B', choix_b), ('C', choix_c), ('D', choix_d)
                ]):
                    texte_choix = choix_list[i].strip() if i < len(choix_list) else f'Choix {label}'
                    Choice.objects.create(
                        question=question,
                        texte=texte_choix or f'Choix {label}',
                        est_correct=(label == correcte),
                        ordre=ordre,
                    )
                created += 1

        messages.success(request, f"{created} question(s) créée(s) avec succès.")
        return redirect('qcm_prof_liste')

    return render(request, 'qcm/prof_creer.html', {'matieres': matieres})


@login_required
@prof_required
def prof_editer_qcm(request, question_id):
    """Éditer une question QCM existante."""
    question = get_object_or_404(QuestionBank, id=question_id, createur=request.user)
    matieres = Matiere.objects.all().order_by('nom')
    choices = list(question.choices.order_by('ordre'))

    if request.method == 'POST':
        matiere_id = request.POST.get('matiere_id')
        question.texte = request.POST.get('texte', question.texte).strip()
        question.difficulte = request.POST.get('difficulte', question.difficulte)
        question.est_publique = request.POST.get('est_publique') == 'on'
        question.matiere = Matiere.objects.filter(id=matiere_id).first() or question.matiere
        question.save()

        correcte = request.POST.get('correcte', 'A').upper()
        labels = ['A', 'B', 'C', 'D']
        for i, choice in enumerate(choices):
            label = labels[i] if i < len(labels) else ''
            new_texte = request.POST.get(f'choix_{label.lower()}', '').strip()
            if new_texte:
                choice.texte = new_texte
            choice.est_correct = (label == correcte)
            choice.save()

        messages.success(request, "Question mise à jour.")
        return redirect('qcm_prof_liste')

    correcte_actuelle = next((c for c in choices if c.est_correct), None)
    correcte_label = ''
    if correcte_actuelle:
        idx = choices.index(correcte_actuelle)
        correcte_label = ['A', 'B', 'C', 'D'][idx] if idx < 4 else 'A'

    return render(request, 'qcm/prof_editer.html', {
        'question': question,
        'choices': choices,
        'matieres': matieres,
        'correcte_label': correcte_label,
    })


@login_required
@prof_required
def prof_supprimer_qcm(request, question_id):
    """Supprimer une question QCM."""
    question = get_object_or_404(QuestionBank, id=question_id, createur=request.user)
    if request.method == 'POST':
        question.delete()
        messages.success(request, "Question supprimée.")
    return redirect('qcm_prof_liste')


@login_required
@prof_required
def prof_upload_qcm(request):
    """
    Upload un fichier (PDF, TXT, image) contenant un QCM.
    L'IA extrait les questions, les choix et le corrigé type, puis les sauvegarde en base.
    """
    matieres = Matiere.objects.all().order_by('nom')

    if request.method == 'POST':
        fichier = request.FILES.get('fichier')
        matiere_id = request.POST.get('matiere_id')
        difficulte = request.POST.get('difficulte', 'moyen')
        est_publique = request.POST.get('est_publique') == 'on'
        matiere = Matiere.objects.filter(id=matiere_id).first()
        classe = request.POST.get('classe', '')

        if not fichier:
            messages.error(request, "Veuillez sélectionner un fichier.")
            return render(request, 'qcm/prof_upload.html', {'matieres': matieres})

        ext = fichier.name.lower().rsplit('.', 1)[-1] if '.' in fichier.name else ''
        raw_text = ''

        try:
            if ext == 'txt':
                raw_text = fichier.read().decode('utf-8', errors='replace')

            elif ext == 'pdf':
                import fitz
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    for chunk in fichier.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name
                try:
                    doc = fitz.open(tmp_path)
                    raw_text = '\n'.join(page.get_text() for page in doc)
                    doc.close()
                finally:
                    os.unlink(tmp_path)

            elif ext in ('jpg', 'jpeg', 'png', 'webp', 'bmp'):
                import tempfile, os, base64
                from ai_engine.ocr_service import OCRCorrectionService
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as tmp:
                    for chunk in fichier.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name
                try:
                    ocr = OCRCorrectionService()
                    result = ocr.extraire_texte_ocr(tmp_path)
                    raw_text = result.get('texte_extrait', '') or result.get('text', '')
                finally:
                    os.unlink(tmp_path)

            else:
                messages.error(request, "Format non supporté. Utilisez PDF, TXT, JPG ou PNG.")
                return render(request, 'qcm/prof_upload.html', {'matieres': matieres})

        except Exception as e:
            logger.error(f"Erreur extraction texte QCM upload: {e}")
            messages.error(request, f"Impossible de lire le fichier : {e}")
            return render(request, 'qcm/prof_upload.html', {'matieres': matieres})

        if not raw_text.strip():
            messages.error(request, "Le fichier ne contient pas de texte lisible.")
            return render(request, 'qcm/prof_upload.html', {'matieres': matieres})

        # Demander à l'IA de structurer le QCM
        try:
            qcm_json_text = multi_ai.parse_qcm_from_text(
                raw_text,
                matiere=matiere.nom if matiere else '',
                classe=classe,
            )
            questions_data = _parse_qcm_text(qcm_json_text, nb_questions=100)
        except Exception as e:
            logger.error(f"Erreur parsing IA QCM upload: {e}")
            messages.error(request, "L'IA n'a pas pu analyser le QCM. Vérifiez le format du fichier.")
            return render(request, 'qcm/prof_upload.html', {'matieres': matieres})

        if not questions_data:
            messages.error(request, "Aucune question détectée dans le fichier.")
            return render(request, 'qcm/prof_upload.html', {'matieres': matieres})

        created = 0
        with transaction.atomic():
            for q in questions_data:
                texte_q = q.get('question', '').strip()
                if not texte_q or 'non générée' in texte_q:
                    continue
                question = QuestionBank.objects.create(
                    matiere=matiere,
                    createur=request.user,
                    texte=texte_q,
                    difficulte=difficulte,
                    est_publique=est_publique,
                    generee_par_ia=True,
                )
                correcte = q.get('correcte', 'A').upper()
                for ordre, choix in enumerate(q.get('choix', [])):
                    label = choix.get('label', ['A', 'B', 'C', 'D'][ordre] if ordre < 4 else 'A')
                    Choice.objects.create(
                        question=question,
                        texte=choix.get('texte', f'Choix {label}'),
                        est_correct=(label.upper() == correcte),
                        ordre=ordre,
                    )
                created += 1

        messages.success(request, f"{created} question(s) importée(s) depuis {fichier.name}.")
        return redirect('qcm_prof_liste')

    return render(request, 'qcm/prof_upload.html', {'matieres': matieres})


@login_required
def download_qcm_bulletin(request, resultat_id):
    """Générer et télécharger le bulletin PDF d'un résultat QCM."""
    from .models import QCMResultat
    from django.http import HttpResponse, Http404
    from django.template.loader import render_to_string
    from django.utils import timezone

    resultat = get_object_or_404(QCMResultat, id=resultat_id, eleve=request.user)

    note = float(resultat.note_sur_20)
    if note >= 18:
        mention = 'Excellent'
    elif note >= 16:
        mention = 'Très Bien'
    elif note >= 14:
        mention = 'Bien'
    elif note >= 12:
        mention = 'Assez Bien'
    elif note >= 10:
        mention = 'Passable'
    else:
        mention = 'Insuffisant'

    now = timezone.now()
    context = {
        'eleve': {
            'nom': resultat.eleve.last_name or resultat.eleve.email,
            'prenoms': resultat.eleve.first_name or '',
            'matricule': getattr(resultat.eleve, 'matricule', ''),
            'classe': resultat.classe,
        },
        'matiere': {
            'nom': resultat.matiere,
            'coef': 1,
            'note': resultat.note_sur_20,
            'observations': resultat.feedback_ia.get('remediation', '') if resultat.feedback_ia else '',
            'mention': mention,
        },
        'annee_scolaire': f"{now.year - 1}/{now.year}",
        'periode': 'QCM',
        'observations_classe': resultat.feedback_ia.get('appreciation', '') if resultat.feedback_ia else '',
        'date_jour': now.day,
        'date_mois': now.month,
        'date_annee': now.year,
    }

    html = render_to_string('bulletins/bulletin_qcm.html', context, request=request)

    try:
        from xhtml2pdf import pisa
        import io
        buffer = io.BytesIO()
        pisa.CreatePDF(html.encode('utf-8'), dest=buffer, encoding='utf-8')
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return HttpResponse(pdf_bytes, content_type='application/pdf',
                            headers={'Content-Disposition': f'attachment; filename="bulletin_qcm_{resultat.id}.pdf"'})
    except ImportError:
        pass

    try:
        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
        return HttpResponse(pdf_bytes, content_type='application/pdf',
                            headers={'Content-Disposition': f'attachment; filename="bulletin_qcm_{resultat.id}.pdf"'})
    except ImportError:
        pass

    return HttpResponse(html, content_type='text/html')
