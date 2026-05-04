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
    exams = Exam.objects.all()
    matieres = Matiere.objects.filter(is_active=True).order_by('nom')
    classes = Classe.objects.filter(is_active=True).order_by('nom')
    return render(request, 'exams/exam_list.html', {
        'exams': exams,
        'matieres': matieres,
        'classes': classes,
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
            matiere_id=matiere_id,
            classe_id=classe_id,
            duree_minutes=int(duree),
            date_debut=date_debut,
            date_fin=date_fin,
            createur=request.user,
            statut='publie'
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
    })

@login_required
def exam_detail_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    files = ExamFile.objects.filter(exam=exam)
    return render(request, 'exams/exam_detail.html', {'exam': exam, 'files': files})


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
