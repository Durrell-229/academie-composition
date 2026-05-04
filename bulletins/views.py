from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
import logging
from .models import Bulletin
from .services import BulletinService

@login_required
def index(request):
    if getattr(request.user, 'role', '') == 'eleve':
        bulletins = Bulletin.objects.filter(eleve=request.user)
    else:
        bulletins = Bulletin.objects.all()
    return render(request, 'bulletins/index.html', {'bulletins': bulletins})

@login_required
def detail(request, bulletin_id):
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")
    return render(request, 'bulletins/detail.html', {'bulletin': bulletin})

@login_required
def generate_bulletin(request, bulletin_id):
    """Génère le bulletin PDF selon le type (administratif ou professionnel)."""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")
    
    if bulletin.type_bulletin == Bulletin.TypeBulletin.ADMINISTRATIF:
        pdf_content = BulletinService.generate_bulletin_administratif_pdf(bulletin)
    else:
        pdf_content = BulletinService.generate_bulletin_professionnel_pdf(bulletin)
    
    if pdf_content is None:
        messages.error(request, "Erreur lors de la génération du bulletin PDF.")
        return redirect('bulletins:detail', bulletin_id=bulletin.id)
    
    messages.success(request, "Bulletin PDF généré avec succès.")
    return redirect('bulletins:detail', bulletin_id=bulletin.id)

@login_required
def download_bulletin_pdf(request, bulletin_id):
    """Téléchargement direct du bulletin PDF."""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")
    
    # Générer le PDF s'il n'existe pas ou si le fichier physique est manquant
    if not bulletin.file_pdf:
        logger = logging.getLogger(__name__)
        try:
            if bulletin.type_bulletin == Bulletin.TypeBulletin.ADMINISTRATIF:
                pdf_content = BulletinService.generate_bulletin_administratif_pdf(bulletin)
            elif bulletin.type_bulletin == Bulletin.TypeBulletin.QCM:
                pdf_content = BulletinService.generate_bulletin_qcm_pdf(bulletin)
            else:
                pdf_content = BulletinService.generate_bulletin_professionnel_pdf(bulletin)
            
            bulletin.refresh_from_db()
            
            if not bulletin.file_pdf:
                messages.error(request, "Impossible de générer le bulletin PDF.")
                return redirect('bulletins:detail', bulletin_id=bulletin.id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur génération PDF bulletin {bulletin_id}: {e}")
            messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
            return redirect('bulletins:detail', bulletin_id=bulletin.id)
    
    # Vérifier que le fichier physique existe
    try:
        if not bulletin.file_pdf.storage.exists(bulletin.file_pdf.name):
            # Fichier manquant, régénérer
            logger = logging.getLogger(__name__)
            logger.warning(f"Fichier PDF manquant pour bulletin {bulletin_id}, régénération...")
            bulletin.file_pdf.delete(save=False)
            
            if bulletin.type_bulletin == Bulletin.TypeBulletin.ADMINISTRATIF:
                BulletinService.generate_bulletin_administratif_pdf(bulletin)
            elif bulletin.type_bulletin == Bulletin.TypeBulletin.QCM:
                BulletinService.generate_bulletin_qcm_pdf(bulletin)
            else:
                BulletinService.generate_bulletin_professionnel_pdf(bulletin)
            
            bulletin.refresh_from_db()
            
            if not bulletin.file_pdf or not bulletin.file_pdf.storage.exists(bulletin.file_pdf.name):
                messages.error(request, "Le fichier PDF n'est plus disponible.")
                return redirect('bulletins:detail', bulletin_id=bulletin.id)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur vérification fichier bulletin {bulletin_id}: {e}")
        messages.error(request, "Erreur lors de l'accès au fichier PDF.")
        return redirect('bulletins:detail', bulletin_id=bulletin.id)
    
    # Télécharger le fichier
    try:
        response = HttpResponse(bulletin.file_pdf.read(), content_type='application/pdf')
        filename = f"bulletin_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lecture fichier bulletin {bulletin_id}: {e}")
        messages.error(request, "Erreur lors du téléchargement du fichier.")
        return redirect('bulletins:detail', bulletin_id=bulletin.id)

@login_required
def preview_bulletin(request, bulletin_id):
    """Aperçu HTML du bulletin avant téléchargement."""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")
    return render(request, 'bulletins/preview.html', {'bulletin': bulletin})


def verify_and_download(request, token):
    """
    Endpoint PUBLIC pour verification via QR code.
    Permet de télécharger le bulletin PDF en scannant le QR.
    Pas d'authentification requise — le token sert de clé de sécurité.
    """
    bulletin = get_object_or_404(Bulletin, verification_token=token)
    logger = logging.getLogger(__name__)

    # Générer le PDF s'il n'existe pas ou si le fichier physique est manquant
    need_regeneration = False
    
    if not bulletin.file_pdf:
        need_regeneration = True
    else:
        # Vérifier que le fichier physique existe
        try:
            if not bulletin.file_pdf.storage.exists(bulletin.file_pdf.name):
                need_regeneration = True
                bulletin.file_pdf.delete(save=False)
        except Exception as e:
            logger.error(f"Erreur vérification fichier QR {token}: {e}")
            need_regeneration = True
            bulletin.file_pdf.delete(save=False)
    
    if need_regeneration:
        try:
            if bulletin.type_bulletin == Bulletin.TypeBulletin.ADMINISTRATIF:
                BulletinService.generate_bulletin_administratif_pdf(bulletin)
            elif bulletin.type_bulletin == Bulletin.TypeBulletin.QCM:
                try:
                    BulletinService.generate_bulletin_qcm_pdf(bulletin)
                except Exception as e:
                    logger.error(f"Erreur génération QCM PDF: {e}")
                    BulletinService.generate_bulletin_professionnel_pdf(bulletin)
            else:
                BulletinService.generate_bulletin_professionnel_pdf(bulletin)
            
            bulletin.refresh_from_db()
        except Exception as e:
            logger.error(f"Erreur génération PDF via QR {token}: {e}")
            return HttpResponse("Erreur lors de la génération du PDF.", status=500)

    if not bulletin.file_pdf:
        return HttpResponse("Bulletin PDF non disponible.", status=500)
    
    # Télécharger le fichier
    try:
        response = HttpResponse(bulletin.file_pdf.read(), content_type='application/pdf')
        filename = f"bulletin_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.error(f"Erreur lecture fichier via QR {token}: {e}")
        return HttpResponse("Erreur lors du téléchargement.", status=500)
