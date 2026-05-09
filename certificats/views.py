"""
Vues pour les certificats et examens
Adapté au système scolaire du Bénin
"""

import os
import qrcode
from io import BytesIO
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from .models import TypeCertificat, CertificatScolaire, ExamenSession, InscriptionExamen, CopieExamenPhysique, HistoriqueCertificat


@login_required
def type_certificat_list(request):
    """Liste des types de certificats"""
    types = TypeCertificat.objects.filter(is_actif=True)
    
    context = {
        'types': types,
    }
    return render(request, 'certificats/type_list.html', context)


@login_required
def type_certificat_create(request):
    """Création d'un type de certificat"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "Le type de certificat a été créé.")
        return redirect('certificats:type_certificat_list')
    
    return render(request, 'certificats/type_form.html', {'title': 'Nouveau type de certificat'})


@login_required
def certificat_list(request):
    """Liste des certificats"""
    query = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    
    certificats = CertificatScolaire.objects.select_related('eleve', 'type_certificat', 'etablissement')
    
    if query:
        certificats = certificats.filter(
            numero_certificat__icontains=query
        ) | certificats.filter(
            eleve__last_name__icontains=query
        )
    
    if statut:
        certificats = certificats.filter(statut=statut)
    
    context = {
        'certificats': certificats,
        'query': query,
    }
    return render(request, 'certificats/certificat_list.html', context)


@login_required
def certificat_create(request):
    """Création d'un certificat"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "Le certificat a été créé.")
        return redirect('certificats:certificat_list')
    
    return render(request, 'certificats/certificat_form.html', {'title': 'Nouveau certificat'})


@login_required
def certificat_detail(request, certificat_id):
    """Détail d'un certificat"""
    certificat = get_object_or_404(CertificatScolaire, id=certificat_id)
    
    context = {
        'certificat': certificat,
        'eleve': certificat.eleve,
        'classe': certificat.classe,
        'type_certificat': certificat.type_certificat,
        'etablissement': certificat.etablissement,
    }
    return render(request, 'certificats/certificat_detail.html', context)


@login_required
def certificat_pdf(request, certificat_id):
    """Génération du PDF du certificat"""
    certificat = get_object_or_404(CertificatScolaire, id=certificat_id)
    
    # Contexte pour le template
    context = {
        'certificat': certificat,
        'eleve': certificat.eleve,
        'classe': certificat.classe,
        'type_certificat': certificat.type_certificat,
        'etablissement': certificat.etablissement,
        'inscription': certificat.examen.inscriptions.filter(eleve=certificat.eleve).first() if certificat.examen else None,
    }
    
    # Rendu du template HTML
    html_string = render_to_string('certificats/certificat_template.html', context)
    
    # Génération du PDF avec xhtml2pdf
    try:
        from xhtml2pdf import pisa
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificat_{certificat.numero_certificat}.pdf"'
        
        # Créer le PDF
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        
        if pisa_status.err:
            return HttpResponse('Erreur lors de la génération du PDF', status=500)
        
        return response
        
    except ImportError:
        # Fallback si xhtml2pdf n'est pas installé
        return HttpResponse(html_string, content_type='text/html')


@login_required
def certificat_deliver(request, certificat_id):
    """Délivrer un certificat (générer QR code et marquer comme délivré)"""
    certificat = get_object_or_404(CertificatScolaire, id=certificat_id)
    
    if request.method == 'POST':
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Données à encoder dans le QR code
        qr_data = f"CERT:{certificat.numero_certificat}|CODE:{certificat.code_verification}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        # Sauvegarder le fichier
        from django.core.files.base import ContentFile
        filename = f'qr_{certificat.numero_certificat}.png'
        certificat.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        # Marquer comme délivré
        certificat.est_delivre = True
        certificat.date_delivrance = timezone.now().date()
        certificat.delivre_par = request.user
        certificat.save()
        
        messages.success(request, f"Le certificat {certificat.numero_certificat} a été délivré avec succès.")
        return redirect('certificats:certificat_detail', certificat_id=certificat.id)
    
    return render(request, 'certificats/certificat_deliver_confirm.html', {'certificat': certificat})


@login_required
def certificat_verify(request):
    """Vérifier un certificat par son code"""
    resultat = None
    certificat = None
    
    if request.method == 'POST':
        numero = request.POST.get('numero')
        code = request.POST.get('code')
        
        try:
            certificat = CertificatScolaire.objects.get(
                numero_certificat=numero,
                code_verification=code
            )
            
            # Enregistrer la vérification
            HistoriqueCertificat.objects.create(
                certificat=certificat,
                code_verification=code,
                resultat_verification=True,
                ip_verificateur=request.META.get('REMOTE_ADDR')
            )
            
            resultat = 'valide'
            
        except CertificatScolaire.DoesNotExist:
            resultat = 'invalide'
    
    context = {
        'resultat': resultat,
        'certificat': certificat,
    }
    return render(request, 'certificats/verify_form.html', context)


@login_required
def examen_list(request):
    """Liste des sessions d'examens"""
    examens = ExamenSession.objects.select_related('etablissement')
    
    context = {
        'examens': examens,
    }
    return render(request, 'certificats/examen_list.html', context)


@login_required
def examen_create(request):
    """Création d'une session d'examen"""
    if request.method == 'POST':
        messages.success(request, "La session d'examen a été créée.")
        return redirect('certificats:examen_list')
    
    return render(request, 'certificats/examen_form.html', {'title': 'Nouvelle session d\'examen'})


@login_required
def examen_detail(request, examen_id):
    """Détail d'une session d'examen"""
    examen = get_object_or_404(ExamenSession, id=examen_id)
    inscriptions = examen.inscriptions.select_related('eleve', 'classe')
    
    context = {
        'examen': examen,
        'inscriptions': inscriptions,
    }
    return render(request, 'certificats/examen_detail.html', context)


@login_required
def examen_publish_results(request, examen_id):
    """Publier les résultats d'un examen"""
    examen = get_object_or_404(ExamenSession, id=examen_id)
    
    if request.method == 'POST':
        examen.resultats_publies = True
        examen.save()
        messages.success(request, "Les résultats ont été publiés.")
        return redirect('certificats:examen_detail', examen_id=examen.id)
    
    return render(request, 'certificats/examen_publish_confirm.html', {'examen': examen})


@login_required
def inscription_list(request, examen_id):
    """Liste des inscriptions à un examen"""
    examen = get_object_or_404(ExamenSession, id=examen_id)
    inscriptions = examen.inscriptions.select_related('eleve', 'classe')
    
    context = {
        'examen': examen,
        'inscriptions': inscriptions,
    }
    return render(request, 'certificats/inscription_list.html', context)


@login_required
def inscription_create(request):
    """Création d'une inscription à un examen"""
    if request.method == 'POST':
        messages.success(request, "L'inscription a été créée.")
        return redirect('certificats:examen_list')
    
    return render(request, 'certificats/inscription_form.html', {'title': 'Nouvelle inscription'})


@login_required
def inscription_detail(request, inscription_id):
    """Détail d'une inscription"""
    inscription = get_object_or_404(InscriptionExamen, id=inscription_id)
    copies = inscription.copies.select_related('matiere')
    
    context = {
        'inscription': inscription,
        'copies': copies,
    }
    return render(request, 'certificats/inscription_detail.html', context)


@login_required
def copie_list(request):
    """Liste des copies physiques"""
    copies = CopieExamenPhysique.objects.select_related('inscription__eleve', 'matiere')
    
    context = {
        'copies': copies,
    }
    return render(request, 'certificats/copie_list.html', context)


@login_required
def copie_upload(request):
    """Upload d'une copie physique"""
    if request.method == 'POST':
        messages.success(request, "La copie a été uploadée avec succès.")
        return redirect('certificats:copie_list')
    
    return render(request, 'certificats/copie_upload_form.html', {'title': 'Upload de copie'})


@login_required
def copie_detail(request, copie_id):
    """Détail d'une copie"""
    copie = get_object_or_404(CopieExamenPhysique, id=copie_id)
    
    context = {
        'copie': copie,
    }
    return render(request, 'certificats/copie_detail.html', context)


@login_required
def copie_correct_ia(request, copie_id):
    """Corriger une copie avec l'IA (OCR)"""
    copie = get_object_or_404(CopieExamenPhysique, id=copie_id)
    
    if request.method == 'POST':
        # Appeler le service IA pour l'OCR et la correction
        # Cette fonction sera implémentée dans le service IA
        from ai_engine.services import OCRCorrectionService
        
        service = OCRCorrectionService()
        resultat = service.corriger_copie(copie)
        
        if resultat['success']:
            copie.texte_extrait = resultat['texte_extrait']
            copie.correction_ia = resultat['correction']
            copie.note_suggeree_ia = resultat['note_suggeree']
            copie.corrige_par_ia = True
            copie.date_correction_ia = timezone.now()
            copie.statut = 'corrigee'
            copie.save()
            
            messages.success(request, "La copie a été corrigée par l'IA.")
        else:
            messages.error(request, f"Erreur lors de la correction: {resultat.get('error', 'Erreur inconnue')}")
        
        return redirect('certificats:copie_detail', copie_id=copie.id)
    
    return render(request, 'certificats/copie_correct_form.html', {'copie': copie})


@login_required
def copie_verify(request, copie_id):
    """Vérifier et valider une copie corrigée par l'IA"""
    copie = get_object_or_404(CopieExamenPhysique, id=copie_id)
    
    if request.method == 'POST':
        note_finale = request.POST.get('note_finale')
        appreciation = request.POST.get('appreciation')
        
        copie.note_finale = note_finale
        copie.appreciation = appreciation
        copie.verifie_par = request.user
        copie.date_verification = timezone.now()
        copie.statut = 'verifiee'
        copie.save()
        
        messages.success(request, "La copie a été vérifiée et validée.")
        return redirect('certificats:copie_detail', copie_id=copie.id)
    
    return render(request, 'certificats/copie_verify_form.html', {'copie': copie})
