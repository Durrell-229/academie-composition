from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from django.utils import timezone
from datetime import timedelta
import logging
from .models import Exam, ExamFile
from core.models import Matiere, Classe

from core.constants import CLASSE_CHOICES, MATIERE_CHOICES

logger = logging.getLogger(__name__)

@login_required
def exam_list_view(request):
    matieres = Matiere.objects.filter(is_active=True).order_by('nom')
    classes = Classe.objects.filter(is_active=True).order_by('nom')
    
    # Filter exams based on user role
    if request.user.role == 'eleve':
        # Students only see exams for their class that are published or in progress
        # Chercher dans les classes où le nom correspond exactement à la classe de l'élève
        exams = Exam.objects.filter(
            classe__nom__iexact=request.user.classe.strip(),
            statut__in=['publie', 'en_cours']
        ).distinct() if request.user.classe and request.user.classe.strip() else Exam.objects.none()
    elif request.user.role in ['professeur', 'conseiller']:
        # Profs/conseillers see their own exams + all published
        exams = Exam.objects.filter(
            createur=request.user
        ) | Exam.objects.filter(statut__in=['publie', 'en_cours'])
        exams = exams.distinct()
    else:
        # Admins see all exams
        exams = Exam.objects.all()
    
    return render(request, 'exams/exam_list.html', {
        'exams': exams,
        'matieres': matieres,
        'classes': classes,
        'user': request.user,
    })

@login_required
def exam_create_view(request):
    if request.user.role not in ['professeur', 'admin']:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
    
    matieres = Matiere.objects.filter(is_active=True).order_by('nom')
    classes = Classe.objects.filter(is_active=True).order_by('nom')
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        matiere_id = request.POST.get('matiere')
        classe_id = request.POST.get('classe')
        duree = request.POST.get('duree') or 60  # Défaut 60 min
        date_debut_str = request.POST.get('date_debut')
        
        from django.utils import timezone
        from datetime import timedelta
        
        if date_debut_str:
            date_debut = timezone.datetime.fromisoformat(date_debut_str)
            if timezone.is_naive(date_debut):
                date_debut = timezone.make_aware(date_debut)
        else:
            date_debut = timezone.now()
            
        date_fin = date_debut + timedelta(minutes=int(duree))
        
        # Création de l'examen
        exam = Exam.objects.create(
            titre=titre,
            description=request.POST.get('description', ''),
            matiere_id=matiere_id if matiere_id else None,
            classe_id=classe_id if classe_id else None,
            type_exam=request.POST.get('type_exam', 'composition'),
            duree_minutes=int(duree),
            date_debut=date_debut,
            date_fin=date_fin,
            coefficient=float(request.POST.get('coefficient', 1)),
            instructions=request.POST.get('instructions', ''),
            anti_cheat_active='anti_cheat_active' in request.POST,
            camera_required='camera_required' in request.POST,
            fullscreen_required='fullscreen_required' in request.POST,
            createur=request.user,
            statut='publie',
        )
        
        # Gestion de l'upload des fichiers
        if request.FILES.get('file_epreuve'):
            f = request.FILES.get('file_epreuve')
            ExamFile.objects.create(
                exam=exam,
                type_fichier='epreuve',
                fichier=f,
                nom_original=f.name
            )
            
        if request.FILES.get('file_corrige'):
            f = request.FILES.get('file_corrige')
            ExamFile.objects.create(
                exam=exam,
                type_fichier='corrige_type',
                fichier=f,
                nom_original=f.name
            )
            
        messages.success(request, f"L'épreuve '{titre}' a été créée avec succès.")
        return redirect('dashboard')

    return render(request, 'exams/exam_form.html', {
        'matieres': matieres,
        'classes': classes,
        'user': request.user,
    })

@login_required
def exam_detail_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    files = ExamFile.objects.filter(exam=exam)
    return render(request, 'exams/exam_detail.html', {
        'exam': exam,
        'files': files,
        'user': request.user,
    })


@login_required
def download_exam_file(request, file_id):
    """Télécharger un fichier d'examen (épreuve ou corrigé) avec vérification."""
    exam_file = get_object_or_404(ExamFile, id=file_id)
    exam = exam_file.exam
    
    # CORRECTION TYPE: Strict access control - NEVER allow students to see answer keys
    if exam_file.type_fichier == 'corrige_type':
        if request.user.role not in ['admin', 'conseiller', 'professeur']:
            logger.warning(f"Élève {request.user.email} a tenté d'accéder au corrigé type de {exam}")
            messages.error(request, "Accès interdit : les corrigés types sont confidentiels.")
            return redirect('dashboard')
        # Even professors can only see their own corrigés
        if request.user.role == 'professeur' and exam.createur != request.user:
            messages.error(request, "Accès refusé au corrigé.")
            return redirect('dashboard')
    
    # ÉPREUVE: Allow if student has access to the exam
    if exam_file.type_fichier == 'epreuve':
        if request.user.role == 'eleve':
            # Check if exam is in progress and for student's class
            now = timezone.now()
            if not (exam.date_debut <= now <= exam.date_fin):
                messages.error(request, "Cet examen n'est pas disponible.")
                return redirect('dashboard')
            if exam.classe and request.user.classe and exam.classe.nom != request.user.classe:
                messages.error(request, "Cet examen n'est pas pour votre classe.")
                return redirect('dashboard')
        elif request.user.role not in ['admin', 'conseiller']:
            if exam.createur != request.user:
                messages.error(request, "Accès refusé.")
                return redirect('dashboard')
    
    # Vérifier si le fichier existe
    try:
        if not exam_file.fichier.storage.exists(exam_file.fichier.name):
            logger.warning(f"Fichier {exam_file.type_fichier} manquant pour ExamFile {file_id}")
            messages.error(request, "Fichier non disponible sur le serveur.")
            return redirect('dashboard')
    except Exception as e:
        logger.error(f"Erreur vérification fichier examen: {e}")
        messages.error(request, "Erreur lors de l'accès au fichier.")
        return redirect('dashboard')
    
    # Servir le fichier
    try:
        response = FileResponse(
            exam_file.fichier.open('rb'),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = f'inline; filename="{exam_file.nom_original}"'
        return response
    except Exception as e:
        logger.error(f"Erreur lecture fichier examen: {e}")
        messages.error(request, "Erreur lors du téléchargement.")
        return redirect('dashboard')


# ═══════════════════════════════════════════════════════════════
# VUES DE VALIDATION ADMIN
# ═══════════════════════════════════════════════════════════════

@login_required
def exam_approve_view(request, exam_id):
    """Approuver une épreuve (Admin uniquement)"""
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé. Seuls les administrateurs peuvent approuver les épreuves.")
        return redirect('exam_detail', exam_id=exam_id)
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        exam.approval_status = 'approved'
        exam.approved_by = request.user
        exam.save()
        
        # Notification au créateur
        from notifications.models import Notification
        Notification.objects.create(
            recipient=exam.createur,
            title=f"✅ Votre épreuve '{exam.titre}' a été approuvée",
            message=f"L'administrateur {request.user.full_name} a validé votre épreuve. Vous pouvez maintenant la publier.",
            type='SUCCESS',
        )
        
        messages.success(request, f"L'épreuve '{exam.titre}' a été approuvée avec succès.")
        logger.info(f"Examen {exam_id} approuvé par {request.user.email}")
    
    return redirect('exam_detail', exam_id=exam_id)


@login_required
def exam_reject_view(request, exam_id):
    """Rejeter une épreuve (Admin uniquement)"""
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé. Seuls les administrateurs peuvent rejeter les épreuves.")
        return redirect('exam_detail', exam_id=exam_id)
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        commentaire = request.POST.get('commentaire', '')
        exam.approval_status = 'rejected'
        exam.rejection_comment = commentaire
        exam.save()
        
        # Notification au créateur
        from notifications.models import Notification
        Notification.objects.create(
            recipient=exam.createur,
            title=f"❌ Votre épreuve '{exam.titre}' a été rejetée",
            message=f"L'administrateur {request.user.get_full_name()} a rejeté votre épreuve." + 
                    (f" Raison: {commentaire}" if commentaire else ""),
            type='WARNING',
        )
        
        messages.warning(request, f"L'épreuve '{exam.titre}' a été rejetée.")
        logger.info(f"Examen {exam_id} rejeté par {request.user.email}. Raison: {commentaire}")
    
    return redirect('exam_detail', exam_id=exam_id)


@login_required
def exam_publish_view(request, exam_id):
    """Publier une épreuve approuvée (Admin ou créateur)"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Vérifier les permissions
    if request.user.role != 'admin' and exam.createur != request.user:
        messages.error(request, "Accès refusé. Vous ne pouvez pas publier cette épreuve.")
        return redirect('exam_detail', exam_id=exam_id)
    
    # Vérifier que l'épreuve est approuvée
    if exam.approval_status != 'approved':
        messages.error(request, "Cette épreuve doit être approuvée par un administrateur avant d'être publiée.")
        return redirect('exam_detail', exam_id=exam_id)
    
    if request.method == 'POST':
        exam.statut = 'publie'
        exam.save()
        
        # Notifier les élèves concernés
        if exam.classe:
            from accounts.models import User
            from notifications.models import Notification
            
            eleves = User.objects.filter(
                role='eleve',
                is_active=True,
                classe=exam.classe.nom
            )
            
            for eleve in eleves:
                Notification.objects.create(
                    recipient=eleve,
                    title=f"📚 Nouvelle épreuve disponible : {exam.titre}",
                    message=f"Une nouvelle épreuve de {exam.matiere.nom} est disponible. Durée: {exam.duree_minutes} minutes.",
                    type='INFO',
                )
        
        messages.success(request, f"L'épreuve '{exam.titre}' a été publiée avec succès.")
        logger.info(f"Examen {exam_id} publié par {request.user.email}")
    
    return redirect('exam_detail', exam_id=exam_id)
