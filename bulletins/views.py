from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
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
    
    # Générer le PDF s'il n'existe pas
    if not bulletin.file_pdf:
        if bulletin.type_bulletin == Bulletin.TypeBulletin.ADMINISTRATIF:
            BulletinService.generate_bulletin_administratif_pdf(bulletin)
        else:
            BulletinService.generate_bulletin_professionnel_pdf(bulletin)
        bulletin.refresh_from_db()
    
    if not bulletin.file_pdf:
        messages.error(request, "Erreur lors de la génération du PDF.")
        return redirect('bulletins:detail', bulletin_id=bulletin.id)
    
    response = HttpResponse(bulletin.file_pdf.read(), content_type='application/pdf')
    filename = f"bulletin_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def preview_bulletin(request, bulletin_id):
    """Aperçu HTML du bulletin avant téléchargement."""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")
    return render(request, 'bulletins/preview.html', {'bulletin': bulletin})
