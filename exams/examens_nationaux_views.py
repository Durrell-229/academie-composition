from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.conf import settings
from .models import (
    ExamenNational, ExamenComposition, ExamenBulletin, ExamenBulletinLigne,
    ExamenReponseEleve
)
from bulletins.reportlab_generator import generer_bulletin_examen, add_qr_to_pdf
from bulletins.coefficients_benin import get_coefficient as get_benin_coefficient
from bulletins.services import BulletinService


@login_required
def examen_list_view(request):
    """Liste des examens nationaux pour l'élève ou l'admin."""
    if request.user.role == 'eleve':
        examens = ExamenNational.objects.filter(
            classes__nom=request.user.classe
        ).distinct() if request.user.classe else ExamenNational.objects.none()
    else:
        examens = ExamenNational.objects.all()

    return render(request, 'examens_nationaux/examen_list.html', {'examens': examens})


@login_required
def examen_detail_view(request, examen_id):
    """Détail d'un examen national — notes par matière pour un élève."""
    examen = get_object_or_404(ExamenNational, id=examen_id)

    if request.user.role == 'eleve':
        composition = get_object_or_404(ExamenComposition, examen=examen, eleve=request.user)
        reponses = ExamenReponseEleve.objects.filter(
            examen_matiere__examen=examen,
            eleve=request.user
        ).select_related('examen_matiere__matiere')
    else:
        composition = None
        reponses = []

    return render(request, 'examens_nationaux/examen_detail.html', {
        'examen': examen,
        'composition': composition,
        'reponses': reponses,
    })


@login_required
def generate_examen_bulletin(request, examen_id):
    """
    Génère le bulletin d'examen national PDF pour un élève.
    Utilise reportlab pour le style officiel.
    """
    examen = get_object_or_404(ExamenNational, id=examen_id)

    if request.user.role == 'eleve':
        composition = get_object_or_404(ExamenComposition, examen=examen, eleve=request.user)
    elif request.user.role in ('admin', 'conseiller'):
        composition = None  # Admin peut générer pour n'importe qui
    else:
        return HttpResponseForbidden("Accès refusé.")

    # Récupérer les notes par matière
    reponses = ExamenReponseEleve.objects.filter(
        examen_matiere__examen=examen
    ).select_related('examen_matiere__matiere')

    if request.user.role == 'eleve':
        reponses = reponses.filter(eleve=request.user)

    # Construire les données pour le generator
    eleve = composition.eleve if composition else request.user
    classe = eleve.classe or ''
    serie = BulletinService._extract_serial(classe)

    matieres_data = []
    total_moy_coeff = 0
    total_coeffs = 0

    for rep in reponses:
        note = rep.note_finale or rep.note_ia or 0
        matiere_nom = rep.examen_matiere.matiere.nom
        coeff_officiel = get_benin_coefficient(matiere_nom, serie)
        coeff = max(coeff_officiel, 1)

        moy_coeff = note * coeff
        total_moy_coeff += moy_coeff
        total_coeffs += coeff

        matieres_data.append({
            'discipline': matiere_nom,
            'devoir': None,
            'compose': float(note),
            'moy_mat': float(note),
            'coeff': coeff,
            'moy_coeff': float(moy_coeff),
            'rang': '-',
            'appreciation': rep.appreciation_ia or '',
        })

    moyenne_calculee = round(total_moy_coeff / total_coeffs, 2) if total_coeffs > 0 else 0

    # Déterminer la décision
    if moyenne_calculee >= 10:
        decision = "ADMIS"
    else:
        decision = "AJOURNÉ"

    # Observations jury
    observations_jury = [
        {"label": "Félicitations du jury", "valeur": "" if moyenne_calculee < 16 else "X"},
        {"label": "Encouragements", "valeur": "" if moyenne_calculee < 12 else "X"},
        {"label": "Admis", "valeur": "" if moyenne_calculee < 10 else "X"},
        {"label": "Ajourné", "valeur": "" if moyenne_calculee >= 10 else "X"},
    ]

    data = {
        'type_examen': examen.get_type_examen_display(),
        'annee_scolaire': examen.annee_scolaire,
        'eleve': {
            'nom': eleve.last_name.upper(),
            'prenom': eleve.first_name,
            'sexe': eleve.sexe or 'M',
            'matricule': eleve.matricule or 'N/A',
            'classe': classe,
            'serie': serie.upper() if serie != 'bepc' else '',
            'effectif': composition.rang if composition else 0,
        },
        'semestre': f"SESSION {examen.annee_scolaire.split('-')[0]}",
        'matieres': matieres_data,
        'totaux': {
            'moy_generale': moyenne_calculee,
            'rang': composition.rang if composition else '-',
            'effectif': composition.rang if composition else '?',
            'retard': 0,
            'absence': 0,
            'justifie': 0,
            'non_justifie': 0,
        },
        'observations_jury': observations_jury,
        'observations_profs': '',
        'decision': decision,
        'verification_token': str(composition.id) if composition else str(examen.id),
    }

    # Générer le PDF
    pdf_bytes = generer_bulletin_examen(data)

    # Ajouter le QR code
    site_url = getattr(settings, 'SITE_URL', 'https://academie.onrender.com')
    if composition:
        download_url = f"{site_url}/examens-nationaux/bulletin/{composition.id}/download/"
    else:
        download_url = f"{site_url}/examens-nationaux/{examen.id}/download/"

    pdf_bytes = add_qr_to_pdf(pdf_bytes, download_url)

    # Sauvegarder si bulletin existe
    if composition:
        bulletin, _ = ExamenBulletin.objects.get_or_create(
            examen=examen,
            eleve=eleve,
            defaults={
                'moyenne_generale': moyenne_calculee,
                'rang': composition.rang,
                'decision_conseil': decision,
            }
        )
        from django.core.files.base import ContentFile
        filename = f"bulletin_{examen.type_examen}_{eleve.last_name}_{examen.annee_scolaire}.pdf"
        bulletin.file_pdf.save(filename, ContentFile(pdf_bytes), save=True)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"bulletin_{examen.type_examen}_{eleve.last_name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def download_examen_bulletin(request, composition_id):
    """
    Endpoint PUBLIC pour télécharger un bulletin d'examen via QR code.
    """
    composition = get_object_or_404(ExamenComposition, id=composition_id)

    # Chercher le bulletin existant
    bulletin = ExamenBulletin.objects.filter(
        examen=composition.examen,
        eleve=composition.eleve
    ).first()

    if bulletin and bulletin.file_pdf:
        response = HttpResponse(bulletin.file_pdf.read(), content_type='application/pdf')
        filename = f"bulletin_{composition.examen.type_examen}_{composition.eleve.last_name}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # Sinon générer
    # On fait une requête interne pour générer
    from django.test import RequestFactory
    factory = RequestFactory()
    fake_request = factory.get('/')
    fake_request.user = composition.eleve

    response = generate_examen_bulletin(fake_request, composition.examen.id)
    return response
