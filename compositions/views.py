from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from .models import CompositionSession, Resultat
from exams.models import Exam, ExamAssignment
import threading
import logging

logger = logging.getLogger(__name__)


def _run_correction_async(session_id):
    """Lance la correction IA dans un thread daemon — pas besoin de worker Redis."""
    from django.db import connection
    try:
        from .tasks import process_ia_correction
        process_ia_correction(session_id)
    except Exception as e:
        logger.error(f"[Thread] Erreur correction session {session_id}: {e}")
    finally:
        connection.close()


@login_required
def composition_room_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.role != 'eleve':
        return HttpResponseForbidden("Seuls les élèves peuvent accéder à la salle de composition.")

    # Vérifier l'assignation: individuelle ou par classe correspondante
    assigned_individual = ExamAssignment.objects.filter(
        exam=exam, eleve=request.user
    ).exists()

    # Via ExamAssignment de classe
    user_classe = (request.user.classe or '').strip()
    assigned_by_class = ExamAssignment.objects.filter(
        exam=exam,
        classe__nom__iexact=user_classe,
        eleve__isnull=True
    ).exists() if user_classe else False

    # Via exam.classe (chemin principal : prof crée un examen et sélectionne une classe)
    assigned_by_exam_classe = (
        exam.classe is not None and
        bool(user_classe) and
        exam.classe.nom.strip().lower() == user_classe.lower()
    )

    if not assigned_individual and not assigned_by_class and not assigned_by_exam_classe and not exam.est_public:
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

    # L'examen est accessible si publié ou en cours ET dans la fenêtre horaire
    now = timezone.now()
    exam_accessible = (
        exam.statut in [Exam.Statut.PUBLIE, Exam.Statut.EN_COURS]
        and exam.date_debut <= now <= exam.date_fin
    )

    if exam_accessible and session.statut == CompositionSession.Statut.EN_ATTENTE:
        session.cheat_count = 0
        session.cheat_logs = []
        session.save()
        session.start()

    # Vérifier que la session n'est pas exclue ou déjà soumise
    if session.statut == CompositionSession.Statut.EXCLU:
        return render(request, 'compositions/banned.html', {'session': session, 'exam': exam})
    if session.statut in [CompositionSession.Statut.SOUMIS, CompositionSession.Statut.CORRIGE, CompositionSession.Statut.EN_CORRECTION]:
        return redirect('result_detail', session_id=session.id)

    # Ne montrer que les fichiers d'épreuve et annexes, JAMAIS les corrigés types aux élèves
    files = exam.files.exclude(type_fichier='corrige_type')

    return render(request, 'compositions/room.html', {
        'exam': exam,
        'session': session,
        'files': files,
        'is_active': exam_accessible and session.statut == CompositionSession.Statut.EN_COURS,
    })


@login_required
def submit_paper_view(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    exam = session.exam
    
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

        # Correction IA en thread daemon (pas besoin de Redis worker)
        thread = threading.Thread(target=_run_correction_async, args=(str(session.id),), daemon=True)
        thread.start()

        # Show confirmation page with bulletin access
        return render(request, 'bulletins/confirmation_devoir.html', {
            'exam_title': exam.titre,
            'session': session,
        })

    return render(request, 'compositions/submit_paper.html', {'session': session})

@login_required
def result_view(request, session_id):
    # Admin peut voir toutes les sessions
    if request.user.is_staff or getattr(request.user, 'role', '') == 'admin':
        session = get_object_or_404(CompositionSession, id=session_id)
    else:
        # Élève ne voit que ses propres sessions
        session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    
    resultat = getattr(session, 'resultat', None)
    circle_offset = 94
    if resultat and resultat.note_sur:
        circle_offset = round(94 * (1 - float(resultat.note) / float(resultat.note_sur)), 2)
    return render(request, 'compositions/result.html', {
        'session': session,
        'resultat': resultat,
        'circle_offset': circle_offset,
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

        if session.statut == CompositionSession.Statut.EXCLU:
            return JsonResponse({'status': 'excluded', 'message': 'Session déjà exclue', 'cheat_count': session.cheat_count})

        # Enregistrer le log
        cheat_log = AntiCheatLog.objects.create(
            session=session,
            type_event=event_type,
            description=description,
        )

        # Pondération anti-faux-positifs:
        #   low      → log seulement, pas d'incrément (erreurs accidentelles)
        #   medium   → +1 (comportement suspect délibéré)
        #   high     → +2 (triche probable)
        #   critical → ban immédiat
        severity_weight = {'low': 0, 'medium': 1, 'high': 2, 'critical': 99}
        weight = severity_weight.get(severity, 1)

        if weight == 99:
            session.statut = CompositionSession.Statut.EXCLU
            session.save()
            return JsonResponse({
                'status': 'excluded',
                'message': 'Exclusion immédiate pour triche flagrante',
                'cheat_count': session.cheat_count,
            })

        session.cheat_count += weight
        cheat_count = session.cheat_count

        if cheat_count >= 10:
            session.statut = CompositionSession.Statut.EXCLU
            session.save()
            return JsonResponse({
                'status': 'excluded',
                'message': f'Exclusion après {cheat_count} violations répétées',
                'cheat_count': cheat_count,
            })

        if cheat_count >= 7:
            warning_level = 'final_warning'
            message = f'🚨 Dernier avertissement ! {cheat_count}/10 violations — exclusion imminente'
        elif cheat_count >= 1:
            warning_level = 'warning'
            message = f'⚠ Alerte : {cheat_count}/10 violations enregistrées'
        else:
            warning_level = 'info'
            message = 'Comportement noté'

        session.save()

        return JsonResponse({
            'status': 'logged',
            'warning_level': warning_level,
            'message': message,
            'cheat_count': cheat_count,
            'log_id': str(cheat_log.id),
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


@require_POST
@login_required
def nemotron_analyze_screenshot(request):
    """
    API pour analyser les screenshots avec Nemotron IA.
    Système de banissement intelligent:
    - 3 violations HIGH/CRITICAL = BAN
    - 8 violations LOW/MEDIUM = BAN
    - Avertissements progressifs avant ban
    """
    try:
        from .nemotron_proctor import nemotron_proctor
        from .models import AntiCheatLog

        session_id = request.POST.get('session_id')
        screenshot = request.FILES.get('screenshot')

        if not session_id or not screenshot:
            return JsonResponse({
                'success': False,
                'error': 'session_id et screenshot requis'
            }, status=400)

        session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)

        if session.statut != CompositionSession.Statut.EN_COURS:
            return JsonResponse({
                'success': False,
                'error': 'Session non active'
            }, status=400)

        # Lire l'image
        image_data = screenshot.read()

        # Récupérer le compteur actuel de violations
        current_violations = getattr(session, 'cheat_count', 0)

        # Analyser avec Nemotron (AVEC compteur de violations)
        result = nemotron_proctor.analyze_screenshot(
            image_data, 
            str(session.id),
            current_violations
        )

        # Sauvegarder l'analyse dans les logs
        if result.get('success'):
            analysis = result.get('analysis', {})
            risk_level = analysis.get('risk_level', 'low')
            action = result.get('action', 'MONITOR')

            # Créer le log
            AntiCheatLog.objects.create(
                session=session,
                type_event=AntiCheatLog.TypeEvent.SUSPICIOUS_MOVEMENT,
                description=f"Nemotron [{risk_level.upper()}]: {analysis.get('details', 'Analyse IA')}",
            )

            # Mettre à jour le compteur de violations (entiers uniquement — PositiveIntegerField)
            if risk_level == 'critical':
                session.cheat_count += 2
            elif risk_level == 'high':
                session.cheat_count += 1
            elif risk_level == 'medium':
                session.cheat_count += 1

            # VÉRIFIER SI BANISSEMENT NÉCESSAIRE
            should_ban = False
            ban_reason = ""

            # 3 violations HIGH/CRITICAL = BAN
            if session.cheat_count >= 3 and risk_level in ['high', 'critical']:
                should_ban = True
                ban_reason = f"Triche répétée détectée ({session.cheat_count} violations)"
            # 8 violations accumulées = BAN
            elif session.cheat_count >= 8:
                should_ban = True
                ban_reason = f"Nombreuses anomalies ({session.cheat_count} violations)"

            if should_ban:
                session.statut = CompositionSession.Statut.EXCLU
                result['banned'] = True
                result['ban_reason'] = ban_reason
                logger.warning(f"🚫 ÉLÈVE BANNI: {request.user.email} - {ban_reason}")
            else:
                result['banned'] = False
                # Avertissements progressifs
                if session.cheat_count >= 2:
                    result['warning'] = f"⚠️ Avertissement: comportement suspect ({session.cheat_count}/8 avant exclusion)"
                if session.cheat_count >= 5:
                    result['warning'] = f"🚨 DERNIER AVERTISSEMENT: ({session.cheat_count}/8 avant exclusion)"

            session.save()

            logger.info(f"👁️ Nemotron [{risk_level}] pour {request.user.email} - Action: {action} - Violations: {session.cheat_count}")

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Erreur analyse Nemotron: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@login_required
def submit_from_room(request):
    """
    API pour soumettre une composition directement depuis la room
    """
    try:
        session_id = request.POST.get('session_id')
        if not session_id:
            return JsonResponse({'success': False, 'error': 'session_id requis'}, status=400)
        
        session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
        
        if session.statut in ['soumis', 'corrige', 'exclu']:
            return JsonResponse({'success': False, 'error': 'Session déjà terminée'}, status=400)
        
        # Handle file uploads
        from .models import StudentSubmissionFile, StudentAnswer
        uploaded_files = request.FILES.getlist('copies')
        
        if uploaded_files:
            for i, f in enumerate(uploaded_files):
                if f.size > 10 * 1024 * 1024:  # 10MB max
                    continue
                if not f.content_type.startswith('image/') and not f.content_type == 'application/pdf':
                    continue
                    
                StudentSubmissionFile.objects.create(
                    session=session,
                    fichier=f,
                    page_number=i+1
                )
        
        # Save text response
        reponse_texte = request.POST.get('reponse_texte', '').strip()
        if reponse_texte:
            StudentAnswer.objects.create(
                session=session,
                question_number=1,
                content=reponse_texte
            )
        
        # Submit the session
        session.submit()

        # Correction IA en thread daemon
        thread = threading.Thread(target=_run_correction_async, args=(str(session.id),), daemon=True)
        thread.start()

        return JsonResponse({
            'success': True,
            'message': 'Composition soumise avec succès',
            'redirect_url': f'/compositions/result/{session.id}/'
        })
        
    except Exception as e:
        logger.error(f"Erreur soumission depuis room: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _build_composition_bulletin_context(resultat):
    """
    Construit le contexte au format bulletin_scolaire à partir d'un Resultat de composition.
    Compatible avec templates/bulletins/bulletin.html.
    """
    session = resultat.session
    eleve = session.eleve
    exam = session.exam

    # Matière principale de l'examen
    matiere_nom = exam.matiere.nom if exam.matiere else exam.titre
    coef = float(exam.coefficient or 1)
    note = float(resultat.note or 0)
    note_sur = float(resultat.note_sur or 20)
    # Ramener sur 20 si nécessaire
    moy_20 = round(note * 20 / note_sur, 2) if note_sur else note
    moy_coef = round(moy_20 * coef, 2)

    # Rang
    rang_str = str(resultat.classement or '')
    if resultat.total_participants:
        rang_str = f"{resultat.classement} / {resultat.total_participants}"

    matieres = [{
        'nom': matiere_nom,
        'coef': int(coef) if coef == int(coef) else coef,
        'interro': '',
        'dev1': note if note_sur == 20 else f"{note}/{int(note_sur)}",
        'dev2': '',
        'dev3': '',
        'moyenne': moy_20,
        'moy_coef': moy_coef,
        'rang': rang_str,
        'appreciation': resultat.appreciation or '',
    }]

    # Mention → avis
    mention = (resultat.mention or '').lower()
    note_norm = moy_20
    avis = {
        'felicitations': note_norm >= 18,
        'tableau_honneur': 16 <= note_norm < 18,
        'encouragement': 14 <= note_norm < 16,
        'avertissement': note_norm < 10,
        'blame': False,
    }

    # Décision
    if note_norm >= 10:
        decision = 'passe'
    else:
        decision = 'redouble'

    # Année scolaire depuis la date de l'examen
    annee_debut = exam.date_debut.year if exam.date_debut else timezone.now().year
    annee = {'debut': str(annee_debut)[-2:], 'fin': str(annee_debut + 1)[-2:]}

    # Nom complet
    if hasattr(eleve, 'get_full_name') and callable(eleve.get_full_name):
        nom_prenoms = eleve.get_full_name()
    else:
        nom_prenoms = getattr(eleve, 'username', '')

    return {
        'logo_benin': '/static/images/armoiries_benin.png',
        'etablissement': {'bp': '', 'tel': '', 'ville': 'Cotonou'},
        'annee': annee,
        'trimestre': 1,
        'eleve': {
            'nom_prenoms': nom_prenoms,
            'date_naissance': getattr(eleve, 'date_naissance', '') or '',
            'lieu_naissance': getattr(eleve, 'lieu_naissance', '') or '',
            'sexe': getattr(eleve, 'sexe', '') or '',
            'classe': getattr(eleve, 'classe', None) and str(eleve.classe) or '',
            'effectif': resultat.total_participants or '',
            'matricule': getattr(eleve, 'matricule', '') or getattr(eleve, 'username', ''),
            'statut': '',
        },
        'matieres': matieres,
        'totaux': {
            'coef': int(coef) if coef == int(coef) else coef,
            'moy_coef': moy_coef,
        },
        'moyenne_trimestre': moy_20,
        'resultats': {
            'moyenne': str(moy_20).replace('.', ','),
            'rang': rang_str,
            'plus_forte': '',
            'plus_faible': '',
            'moyenne_classe': '',
            'mention': resultat.get_mention_display() if hasattr(resultat, 'get_mention_display') else mention,
        },
        'avis': avis,
        'decision': decision,
        'fait_a': 'Cotonou',
        'fait_le': resultat.corrige_at.strftime('%d/%m/%Y') if resultat.corrige_at else '',
    }


@login_required
def bulletin_composition_html(request, session_id):
    """
    Affiche le bulletin d'une composition au format officiel béninois (HTML).
    URL : /compositions/<session_id>/bulletin/
    """
    session = get_object_or_404(CompositionSession, id=session_id)
    if request.user.role == 'eleve' and session.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")

    resultat = get_object_or_404(Resultat, session=session)
    context = _build_composition_bulletin_context(resultat)
    return render(request, 'bulletins/bulletin.html', context)


@login_required
def bulletin_composition_pdf(request, session_id):
    """
    Génère le bulletin d'une composition au format PDF officiel béninois.
    URL : /compositions/<session_id>/bulletin/pdf/
    """
    from django.template.loader import render_to_string

    session = get_object_or_404(CompositionSession, id=session_id)
    if request.user.role == 'eleve' and session.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")

    resultat = get_object_or_404(Resultat, session=session)
    context = _build_composition_bulletin_context(resultat)
    html_string = render_to_string('bulletins/bulletin.html', context, request=request)

    eleve = session.eleve
    filename = f"bulletin_{getattr(eleve, 'last_name', 'eleve')}_{session.exam.titre[:15].replace(' ', '_')}.pdf"

    # WeasyPrint en priorité
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_bytes = WeasyHTML(
            string=html_string,
            base_url=request.build_absolute_uri('/')
        ).write_pdf()
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="{filename}"'
        return resp
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"WeasyPrint bulletin composition: {e}, fallback xhtml2pdf")

    # Fallback xhtml2pdf
    try:
        from io import BytesIO
        from xhtml2pdf import pisa
        buf = BytesIO()
        pisa_status = pisa.CreatePDF(html_string, dest=buf, encoding='utf-8')
        if pisa_status.err:
            return HttpResponse("Erreur lors de la génération du PDF.", status=500)
        resp = HttpResponse(buf.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="{filename}"'
        return resp
    except Exception as e:
        logger.error(f"xhtml2pdf bulletin composition: {e}")
        return HttpResponse(f"Impossible de générer le PDF : {e}", status=500)


def download_composition_bulletin(request, resultat_id):
    """
    Endpoint PUBLIC pour télécharger le bulletin d'une composition via QR code.
    Pas d'authentification requise — le resultat ID (UUID) sert de clé.
    """
    resultat = get_object_or_404(Resultat, id=resultat_id)

    if not resultat.bulletin_pdf:
        return HttpResponse("Bulletin PDF non disponible.", status=404)

    response = HttpResponse(resultat.bulletin_pdf.read(), content_type='application/pdf')
    eleve = resultat.session.eleve
    filename = f"bulletin_{eleve.last_name}_{resultat.session.exam.titre[:10]}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def serve_exam_file(request, file_id):
    """
    Vue protégée pour servir les fichiers d'examen.
    Les élèves ne peuvent PAS accéder aux corrigés types.
    """
    from exams.models import ExamFile
    from django.http import HttpResponse, HttpResponseForbidden
    import mimetypes

    exam_file = get_object_or_404(ExamFile, id=file_id)

    # Si c'est un corrigé type et que l'utilisateur est un élève → INTERDIT
    if exam_file.type_fichier == 'corrige_type' and request.user.role == 'eleve':
        return HttpResponseForbidden("Accès interdit. Les corrigés types ne sont pas accessibles aux élèves.")

    # Servir le fichier
    try:
        # Lire le fichier
        file_content = exam_file.fichier.read()
        
        # Détecter le content type
        content_type, _ = mimetypes.guess_type(exam_file.nom_original)
        if not content_type:
            content_type = 'application/pdf'
        
        # Créer la réponse avec les bons headers pour iframe
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{exam_file.nom_original}"'
        response['X-Frame-Options'] = 'SAMEORIGIN'  # Permettre l'iframe sur le même domaine
        
        return response
    except Exception as e:
        return HttpResponse(f"Erreur lors de l'accès au fichier: {str(e)}", status=500)
