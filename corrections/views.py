from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q

from exams.models import Exam, ExamFile
from compositions.models import CompositionSession, Resultat
from ai_engine.models import AICorrection
from .models import Bareme, CorrectionHumaine
from .corrige_type_service import corrige_type_service
from .correction_with_corrige_type import correction_with_corrige_service
from .baremes_service import baremes_service
import logging

logger = logging.getLogger(__name__)


@login_required
def correction_dashboard(request):
    # 1 requête au lieu de 3 pour les stats IA
    ai_stats = AICorrection.objects.aggregate(
        ai_total=Count('id'),
        ai_pending=Count('id', filter=Q(statut=AICorrection.Statut.EN_ATTENTE)),
        ai_done=Count('id', filter=Q(statut=AICorrection.Statut.TERMINE)),
    )
    ai_total = ai_stats['ai_total']
    ai_pending = ai_stats['ai_pending']
    ai_done = ai_stats['ai_done']

    # 1 requête au lieu de 3 pour les stats humaines
    humain_stats = CorrectionHumaine.objects.aggregate(
        humain_total=Count('id'),
        humain_pending=Count('id', filter=Q(statut=CorrectionHumaine.Statut.ASSIGNEE)),
        humain_done=Count('id', filter=Q(statut=CorrectionHumaine.Statut.TERMINEE)),
    )
    humain_total = humain_stats['humain_total']
    humain_pending = humain_stats['humain_pending']
    humain_done = humain_stats['humain_done']

    # Sessions soumises sans correction
    sessions_sans_correction = CompositionSession.objects.filter(
        statut=CompositionSession.Statut.SOUMIS
    ).select_related('exam', 'eleve').order_by('-submitted_at')[:10]

    # Corrections humaines assignées à cet utilisateur
    mes_corrections = CorrectionHumaine.objects.filter(
        correcteur=request.user,
        statut__in=[CorrectionHumaine.Statut.ASSIGNEE, CorrectionHumaine.Statut.EN_COURS]
    ).select_related('session__exam', 'session__eleve').order_by('date_limite')

    context = {
        'total_corrections': ai_total + humain_total,
        'pending_corrections': ai_pending + humain_pending,
        'completed_corrections': ai_done + humain_done,
        'ai_total': ai_total,
        'ai_pending': ai_pending,
        'ai_done': ai_done,
        'humain_total': humain_total,
        'humain_pending': humain_pending,
        'humain_done': humain_done,
        'sessions_sans_correction': sessions_sans_correction,
        'mes_corrections': mes_corrections,
    }
    return render(request, 'corrections/dashboard.html', context)


@login_required
def corrige_types_list(request):
    corrige_types = ExamFile.objects.filter(
        type_fichier=ExamFile.TypeFichier.CORRIGE_TYPE
    ).select_related('exam', 'exam__matiere', 'exam__classe').order_by('-uploaded_at')
    context = {'corrige_types': corrige_types}
    return render(request, 'corrections/corrige_types_list.html', context)


@login_required
def corrige_type_detail(request, id):
    corrige_file = get_object_or_404(
        ExamFile, id=id, type_fichier=ExamFile.TypeFichier.CORRIGE_TYPE
    )
    context = {'corrige_type': corrige_file, 'exam': corrige_file.exam}
    return render(request, 'corrections/corrige_type_detail.html', context)


@login_required
def upload_corrige_type(request):
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        fichier = request.FILES.get('fichier')

        if not exam_id or not fichier:
            return JsonResponse({'success': False, 'error': 'exam_id et fichier requis'}, status=400)

        exam = get_object_or_404(Exam, id=exam_id)

        ExamFile.objects.filter(exam=exam, type_fichier=ExamFile.TypeFichier.CORRIGE_TYPE).delete()

        corrige = ExamFile.objects.create(
            exam=exam,
            type_fichier=ExamFile.TypeFichier.CORRIGE_TYPE,
            fichier=fichier,
            nom_original=fichier.name,
        )
        corrige_type_service.invalidate_cache(exam.id)

        return JsonResponse({
            'success': True,
            'message': f'Corrigé type "{fichier.name}" uploadé pour {exam.titre}',
            'document_id': corrige.document_id,
        })

    exams = Exam.objects.filter(createur=request.user).order_by('-created_at')
    return render(request, 'corrections/upload_corrige_type.html', {'exams': exams})


@login_required
def baremes_list(request):
    baremes = Bareme.objects.select_related('exam', 'exam__matiere', 'cree_par').order_by('-created_at')
    context = {'baremes': baremes}
    return render(request, 'corrections/baremes_list.html', context)


@login_required
@require_POST
def trigger_ai_correction(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id)

    if hasattr(session, 'ai_correction'):
        existing = session.resultat.ai_correction if hasattr(session, 'resultat') else None
        if existing and existing.statut == AICorrection.Statut.TERMINE:
            return JsonResponse({'success': False, 'error': 'Correction IA déjà terminée'}, status=400)

    files = list(session.submission_files.all())
    text_response = ' '.join(a.content for a in session.answers.all())

    try:
        result = correction_with_corrige_service.correct_student_copy(session, files, text_response)
        return JsonResponse({'success': result.get('success', False), 'note': result.get('note'), 'message': result.get('error', 'Correction lancée')})
    except Exception as e:
        logger.error(f"Erreur trigger correction IA session {session_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def assign_human_correction(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id)
    correcteur_id = request.POST.get('correcteur_id')
    date_limite_str = request.POST.get('date_limite')

    if not correcteur_id:
        return JsonResponse({'success': False, 'error': 'correcteur_id requis'}, status=400)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    correcteur = get_object_or_404(User, id=correcteur_id)

    date_limite = None
    if date_limite_str:
        from django.utils.dateparse import parse_datetime
        date_limite = parse_datetime(date_limite_str)

    correction, created = CorrectionHumaine.objects.get_or_create(
        session=session,
        defaults={
            'correcteur': correcteur,
            'assigne_par': request.user,
            'date_limite': date_limite,
        }
    )
    if not created:
        correction.correcteur = correcteur
        correction.assigne_par = request.user
        correction.date_limite = date_limite
        correction.save()

    session.statut = CompositionSession.Statut.EN_CORRECTION
    session.save(update_fields=['statut'])

    return JsonResponse({'success': True, 'correction_id': str(correction.id)})


@login_required
def human_correction_form(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id)
    correction = get_object_or_404(CorrectionHumaine, session=session, correcteur=request.user)

    if request.method == 'POST':
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire', '')

        if not note:
            messages.error(request, 'La note est obligatoire.')
            return redirect('corrections:human_correction_form', session_id=session_id)

        try:
            note_val = float(note)
        except ValueError:
            messages.error(request, 'Note invalide.')
            return redirect('corrections:human_correction_form', session_id=session_id)

        details = []
        criteres = request.POST.getlist('critere_nom')
        points = request.POST.getlist('critere_points')
        commentaires_critere = request.POST.getlist('critere_commentaire')
        for i, nom in enumerate(criteres):
            details.append({
                'critere': nom,
                'points_obtenus': float(points[i]) if i < len(points) else 0,
                'commentaire': commentaires_critere[i] if i < len(commentaires_critere) else '',
            })

        correction.terminer(note_val, commentaire, details)
        session.statut = CompositionSession.Statut.CORRIGE
        session.save(update_fields=['statut'])

        messages.success(request, 'Correction enregistrée avec succès.')
        return redirect('corrections:dashboard')

    bareme = baremes_service.get_bareme_for_exam(session.exam)
    files = session.submission_files.all()
    answers = session.answers.all()

    context = {
        'session': session,
        'correction': correction,
        'bareme': bareme,
        'files': files,
        'answers': answers,
    }
    return render(request, 'corrections/human_correction_form.html', context)
