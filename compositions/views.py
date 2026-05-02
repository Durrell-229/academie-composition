from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import CompositionSession
from exams.models import Exam, ExamAssignment


@login_required
def composition_room_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.role != 'eleve':
        return HttpResponseForbidden("Seuls les élèves peuvent accéder à la salle de composition.")

    assigned = ExamAssignment.objects.filter(
        exam=exam, eleve=request.user
    ).exists() or ExamAssignment.objects.filter(
        exam=exam, classe__isnull=False
    ).exists()

    if not assigned and not exam.est_public:
        return HttpResponseForbidden("Vous n'êtes pas assigné à cette épreuve.")

    session, created = CompositionSession.objects.get_or_create(
        exam=exam,
        eleve=request.user,
        defaults={
            'mode': 'en_ligne',
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:512],
        }
    )

    if exam.is_en_cours and session.statut == CompositionSession.Statut.EN_ATTENTE:
        session.start()

    files = exam.files.filter(type_fichier='epreuve')

    return render(request, 'compositions/room.html', {
        'exam': exam,
        'session': session,
        'files': files,
        'is_active': exam.is_en_cours and session.statut == CompositionSession.Statut.EN_COURS,
    })


@login_required
def submit_paper_view(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    
    if session.statut in ['soumis', 'corrige', 'exclu']:
        from django.contrib import messages
        messages.error(request, "Cette composition a déjà été soumise ou est exclue.")
        return redirect('result_detail', session_id=session.id)
    
    if request.method == 'POST':
        from .models import StudentSubmissionFile
        from django.contrib import messages
        
        # Handle file uploads
        uploaded_files = request.FILES.getlist('copies')
        if uploaded_files:
            # Validate files
            for f in uploaded_files:
                if f.size > 10 * 1024 * 1024:  # 10MB max per file
                    messages.error(request, "Chaque fichier ne doit pas dépasser 10 Mo.")
                    return render(request, 'compositions/submit_paper.html', {'session': session})
                if not f.content_type.startswith('image/'):
                    messages.error(request, "Seules les images sont acceptées pour les copies.")
                    return render(request, 'compositions/submit_paper.html', {'session': session})
            
            for i, f in enumerate(uploaded_files):
                StudentSubmissionFile.objects.create(
                    session=session,
                    fichier=f,
                    page_number=i+1
                )
        
        # Also save text response if provided
        reponse_texte = request.POST.get('reponse_texte', '').strip()
        if reponse_texte:
            from .models import StudentAnswer
            StudentAnswer.objects.create(
                session=session,
                question_number=1,
                content=reponse_texte
            )
        
        # Submit the session
        session.submit()
        
        # Correction IA asynchrone via Redis
        from .tasks import process_ia_correction
        process_ia_correction.delay(str(session.id))
        
        messages.success(request, "Votre composition a été soumise avec succès. La correction IA est en cours.")
        return redirect('result_detail', session_id=session.id)

    return render(request, 'compositions/submit_paper.html', {'session': session})

@login_required
def result_view(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    resultat = getattr(session, 'resultat', None)
    return render(request, 'compositions/result.html', {
        'session': session,
        'resultat': resultat,
    })

@login_required
def ia_corrections_list_view(request):
    from .models import Resultat
    if request.user.role == 'eleve':
        resultats = Resultat.objects.filter(session__eleve=request.user, corrige_par_ia=True)
    elif request.user.role == 'professeur':
        resultats = Resultat.objects.filter(session__exam__createur=request.user, corrige_par_ia=True)
    else: # admin
        resultats = Resultat.objects.filter(corrige_par_ia=True)
        
    return render(request, 'compositions/ia_corrections.html', {'resultats': resultats})


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import AntiCheatLog

@require_POST
@login_required
def log_cheat_event(request):
    """API pour enregistrer les événements anti-triche."""
    import json
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        event_type = data.get('event_type', '')
        description = data.get('description', '')
        severity = data.get('severity', 'low')
        
        if not session_id or not event_type:
            return JsonResponse({'error': 'session_id et event_type requis'}, status=400)
        
        session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
        
        # Enregistrer le log
        cheat_log = AntiCheatLog.objects.create(
            session=session,
            type_event=event_type,
            description=description,
        )
        
        # Incrémenter le compteur de triche
        session.cheat_count += 1
        
        # Actions selon la sévérité et le nombre
        if severity == 'high' or session.cheat_count >= 5:
            session.statut = CompositionSession.Statut.EXCLU
            session.save()
            return JsonResponse({
                'status': 'excluded',
                'message': 'Exclusion pour triche répétée',
                'cheat_count': session.cheat_count
            })
        
        # Avertissements progressifs
        if session.cheat_count == 3:
            warning_level = 'final_warning'
            message = 'Dernier avertissement avant exclusion !'
        elif session.cheat_count >= 2:
            warning_level = 'warning'
            message = f'Avertissement ({session.cheat_count}/5 avant exclusion)'
        else:
            warning_level = 'info'
            message = 'Comportement suspect détecté'
        
        session.save()
        
        return JsonResponse({
            'status': 'logged',
            'warning_level': warning_level,
            'message': message,
            'cheat_count': session.cheat_count,
            'log_id': str(cheat_log.id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
def upload_screenshot(request):
    """API pour recevoir les screenshots périodiques anti-triche."""
    try:
        session_id = request.POST.get('session_id')
        screenshot = request.FILES.get('screenshot')

        if not session_id or not screenshot:
            return JsonResponse({'status': 'error', 'message': 'session_id et screenshot requis'}, status=400)

        session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)

        if session.statut != CompositionSession.Statut.EN_COURS:
            return JsonResponse({'status': 'error', 'message': 'Session non active'}, status=400)

        # Créer un log avec screenshot
        cheat_log = AntiCheatLog.objects.create(
            session=session,
            type_event=AntiCheatLog.TypeEvent.SUSPICIOUS_MOVEMENT,
            description='Screenshot périodique automatique',
        )
        cheat_log.screenshot.save(
            f'screenshot_{session.id.hex[:8]}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.png',
            screenshot,
            save=True
        )

        return JsonResponse({'status': 'ok', 'log_id': str(cheat_log.id)})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
