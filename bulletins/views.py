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
    """
    Aperçu HTML du vrai bulletin béninois avec toolbar d'action.
    Rend le template PDF directement dans le navigateur — ce que tu vois = ce qui s'imprime.
    """
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès non autorisé.")

    import hashlib
    from .coefficients_benin import get_coefficient as get_benin_coefficient

    # Essayer d'importer QRService
    try:
        from api.services.qr_service import QRService
        qr_data_uri = QRService.generate_bulletin_qr(bulletin)
    except Exception:
        qr_data_uri = None

    lignes = list(bulletin.lignes.all())
    eleve = bulletin.eleve
    classe = bulletin.classe or (eleve.classe if eleve else '')
    serie = BulletinService._extract_serial(classe)

    for ligne in lignes:
        coeff_officiel = get_benin_coefficient(ligne.matiere, serie)
        if ligne.coefficient < coeff_officiel:
            ligne.coefficient = coeff_officiel

    total_moy_coeff = sum(l.note * l.coefficient for l in lignes) if lignes else 0
    total_coeffs = sum(l.coefficient for l in lignes) if lignes else 1

    context = {
        'bulletin': bulletin,
        'eleve': eleve,
        'classe': classe,
        'serie': serie,
        'periode': bulletin.get_periode_display(),
        'moyenne': bulletin.moyenne_generale,
        'rang': bulletin.rang,
        'effectif': bulletin.effectif_total,
        'observation': bulletin.observation_conseil or "Travail satisfaisant. Continue dans cette voie.",
        'decision': bulletin.decision_conseil,
        'annee_scolaire': bulletin.annee_scolaire,
        'lignes': lignes,
        'total_moy_coeff': round(total_moy_coeff, 2),
        'total_coeffs': round(total_coeffs, 2),
        'absences_just': bulletin.absences or 0,
        'heures_just': bulletin.heures_absences or 0,
        'absences_nonjust': 0,
        'heures_nonjust': 0,
        'heures_perdues': bulletin.heures_absences or 0,
        'retards': bulletin.retards or 0,
        'verification_token': bulletin.verification_token,
        'qr_data_uri': qr_data_uri,
        # Comportement
        'comportement_assiduite': 'B',
        'comportement_discipline': 'B',
        'comportement_travail': 'B',
        'comportement_presentation': 'B',
        'comportement_ponctualite': 'B',
        # QCM context (pour bulletin_qcm_pdf.html)
        'matiere': '',
        'titre_qcm': '',
        'bonnes_reponses': 0,
        'mauvaises_reponses': 0,
        'total_questions': 0,
        'taux_reussite': 0,
        'moyenne': bulletin.moyenne_generale,
        'professeur': '',
        'annee_scolaire': bulletin.annee_scolaire,
        'questions': [],
        'feedback': None,
        'appreciation': bulletin.appreciation_ia or '',
    }

    # Enrichir le contexte QCM si nécessaire
    if bulletin.type_bulletin == Bulletin.TypeBulletin.QCM:
        template = 'bulletins/bulletin_qcm_pdf.html'
        qcm_resultat = bulletin.qcm_resultats.first() if hasattr(bulletin, 'qcm_resultats') else None
        ligne = bulletin.lignes.first()
        matiere_nom = ligne.matiere if ligne else ''
        br = qcm_resultat.bonnes_reponses if qcm_resultat else 0
        tq = qcm_resultat.total_questions if qcm_resultat else 0
        taux = round((br * 100 / tq), 1) if tq > 0 else 0
        context.update({
            'matiere': matiere_nom,
            'titre_qcm': bulletin.appreciation_ia or f'Évaluation QCM — {matiere_nom}',
            'bonnes_reponses': br,
            'mauvaises_reponses': tq - br,
            'total_questions': tq,
            'taux_reussite': taux,
            'professeur': f'Professeur de {matiere_nom}',
        })
    else:
        template = 'bulletins/bulletin_administratif_pdf.html'
        # Ajouter note_ok/note_nok aux lignes pour la coloration
        for ligne in lignes:
            try:
                n = float(str(ligne.note).replace(',', '.'))
                ligne.note_ok = n >= 10
                ligne.note_nok = n < 10
            except (ValueError, TypeError):
                ligne.note_ok = False
                ligne.note_nok = False

    # Injecter le toolbar flottant dans le HTML rendu
    from django.template.loader import render_to_string
    from django.urls import reverse
    bulletin_html = render_to_string(template, context, request=request)

    toolbar = f"""
    <div style="position:fixed;top:0;left:0;right:0;z-index:9999;background:#1e293b;color:#fff;padding:10px 20px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 12px rgba(0,0,0,0.4);font-family:Arial,sans-serif;font-size:13px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-weight:bold;color:#94a3b8;">📄 Aperçu Bulletin</span>
            <span style="color:#64748b;">—</span>
            <span>{eleve.last_name if eleve else ''} {eleve.first_name if eleve else ''}</span>
            <span style="background:#334155;padding:2px 8px;border-radius:4px;font-size:11px;">{bulletin.get_periode_display()} — {bulletin.annee_scolaire}</span>
        </div>
        <div style="display:flex;gap:10px;">
            <a href="{reverse('bulletins:detail', kwargs={'bulletin_id': bulletin_id})}"
               style="background:#475569;color:#fff;padding:7px 16px;border-radius:6px;text-decoration:none;font-size:12px;">
               ← Retour
            </a>
            <a href="{reverse('bulletins:generate', kwargs={'bulletin_id': bulletin_id})}"
               style="background:#2563eb;color:#fff;padding:7px 16px;border-radius:6px;text-decoration:none;font-size:12px;">
               ⚡ Générer PDF
            </a>
            <a href="{reverse('bulletins:download', kwargs={'bulletin_id': bulletin_id})}"
               style="background:#16a34a;color:#fff;padding:7px 16px;border-radius:6px;text-decoration:none;font-size:12px;">
               ⬇ Télécharger PDF
            </a>
            <button onclick="window.print()"
               style="background:#7c3aed;color:#fff;padding:7px 16px;border-radius:6px;border:none;cursor:pointer;font-size:12px;">
               🖨 Imprimer
            </button>
        </div>
    </div>
    <div style="height:44px;"></div>
    <style>@media print {{ div[style*="position:fixed"] {{ display:none !important; }} div[style*="height:44px"] {{ display:none !important; }} }}</style>
    """

    full_html = bulletin_html.replace('<body>', f'<body>{toolbar}', 1)
    return HttpResponse(full_html)


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
