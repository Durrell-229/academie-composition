import os
import math
import logging
from datetime import datetime, date
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import FileResponse, Http404
from django.conf import settings
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.core.files.base import ContentFile

from .models import Devoir, DevoirMatiere, DevoirComposition, Certificat
from core.models import Matiere, Classe
from accounts.models import User

logger = logging.getLogger(__name__)

ADMIN_PHONE = '+2290197650817'


# ═══════════════════════════════════════════
# ADMIN VIEWS
# ═══════════════════════════════════════════

@login_required
def devoir_list_view(request):
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    devoirs = Devoir.objects.all().order_by('-date_debut')
    pending = DevoirMatiere.objects.filter(statut=DevoirMatiere.StatutEP.SOUMIS).count()

    return render(request, 'devoirs/admin_list.html', {
        'devoirs': devoirs,
        'pending_epreuves': pending,
    })


@login_required
def devoir_create_view(request):
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        description = request.POST.get('description', '').strip()
        date_debut = request.POST.get('date_debut', '')
        date_fin = request.POST.get('date_fin', '')
        instructions = request.POST.get('instructions', '').strip()
        classe_ids = request.POST.getlist('classes')
        matiere_ids = request.POST.getlist('matieres')

        if not all([titre, date_debut, date_fin]):
            messages.error(request, "Tous les champs sont requis.")
            return redirect('devoir_create')

        try:
            devoir = Devoir.objects.create(
                titre=titre,
                description=description,
                date_debut=date_debut,
                date_fin=date_fin,
                instructions=instructions,
                createur=request.user,
            )
            if classe_ids:
                devoir.classes.set(classe_ids)
            if matiere_ids:
                devoir.matieres.set(matiere_ids)

            messages.success(request, f"Devoir '{titre}' créé avec succès.")
            return redirect('devoir_detail', pk=devoir.pk)
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")

    classes = Classe.objects.all().order_by('nom')
    matieres = Matiere.objects.all().order_by('nom')
    return render(request, 'devoirs/admin_create.html', {
        'classes': classes,
        'matieres': matieres,
    })


@login_required
def devoir_detail_view(request, pk):
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    devoir = get_object_or_404(Devoir, pk=pk)
    matieres_info = []
    for m in devoir.matieres.all():
        dm = DevoirMatiere.objects.filter(devoir=devoir, matiere=m).first()
        matieres_info.append({
            'matiere': m,
            'epreuve': dm,
            'horaire': devoir.horaires.get(m.nom, {}),
        })

    return render(request, 'devoirs/admin_detail.html', {
        'devoir': devoir,
        'matieres_info': matieres_info,
    })


@login_required
def devoir_publish_view(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    devoir = get_object_or_404(Devoir, pk=pk)
    devoir.statut = Devoir.Statut.PROGRAMME_PUBLIE
    devoir.save()
    messages.success(request, "Programme publié.")
    return redirect('devoir_detail', pk=pk)


@login_required
def devoir_start_view(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    devoir = get_object_or_404(Devoir, pk=pk)
    devoir.statut = Devoir.Statut.EN_COURS
    devoir.save()
    for classe in devoir.classes.all():
        eleves = User.objects.filter(role=User.Role.ELEVE, classe=classe.nom)
        for eleve in eleves:
            DevoirComposition.objects.get_or_create(
                devoir=devoir, eleve=eleve, defaults={'classe': classe}
            )
    messages.success(request, "Devoir lancé, élèves inscrits.")
    return redirect('devoir_detail', pk=pk)


@login_required
def devoir_end_view(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    devoir = get_object_or_404(Devoir, pk=pk)
    devoir.statut = Devoir.Statut.TERMINE
    devoir.save()
    messages.success(request, "Devoir terminé.")
    return redirect('devoir_detail', pk=pk)


@login_required
def devoir_matiere_validate_view(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    dm = get_object_or_404(DevoirMatiere, pk=pk)
    dm.statut = DevoirMatiere.StatutEP.VALIDE
    dm.valide_par = request.user
    dm.validated_at = timezone.now()
    dm.save()
    messages.success(request, f"Épreuve '{dm.matiere.nom}' validée.")
    return redirect('devoir_detail', pk=dm.devoir.pk)


@login_required
def devoir_matiere_reject_view(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    dm = get_object_or_404(DevoirMatiere, pk=pk)
    dm.statut = DevoirMatiere.StatutEP.REJETE
    dm.commentaire_admin = request.POST.get('commentaire', '')
    dm.save()
    messages.warning(request, f"Épreuve '{dm.matiere.nom}' rejetée.")
    return redirect('devoir_detail', pk=dm.devoir.pk)


# ═══════════════════════════════════════════
# PROF VIEWS
# ═══════════════════════════════════════════

@login_required
def devoir_submit_epreuve_view(request, devoir_id, matiere_id):
    if request.user.role not in ('professeur', 'admin'):
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    devoir = get_object_or_404(Devoir, pk=devoir_id)
    matiere = get_object_or_404(Matiere, pk=matiere_id)

    if request.method == 'POST':
        epreuve = request.FILES.get('epreuve')
        corrige = request.FILES.get('corrige')

        if not epreuve or not corrige:
            messages.error(request, "L'épreuve et le corrigé sont requis.")
            return redirect('devoir_submit_epreuve', devoir_id=devoir_id, matiere_id=matiere_id)

        DevoirMatiere.objects.update_or_create(
            devoir=devoir, matiere=matiere,
            defaults={
                'epreuve_file': epreuve,
                'corrige_type_file': corrige,
                'soumis_par': request.user,
                'statut': DevoirMatiere.StatutEP.SOUMIS,
            }
        )
        messages.success(request, "Épreuve soumise avec succès.")
        return redirect('dashboard')

    return render(request, 'devoirs/prof_submit.html', {
        'devoir': devoir,
        'matiere': matiere,
    })


# ═══════════════════════════════════════════
# ELEVE VIEWS
# ═══════════════════════════════════════════

@login_required
def eleve_programme_view(request):
    devoirs = Devoir.objects.filter(
        statut__in=[Devoir.Statut.PROGRAMME_PUBLIE, Devoir.Statut.EN_COURS],
        classes__nom=request.user.classe,
    ).distinct().order_by('date_debut')

    return render(request, 'devoirs/eleve_programme.html', {'devoirs': devoirs})


@login_required
def eleve_compose_view(request, devoir_id):
    devoir = get_object_or_404(Devoir, pk=devoir_id)
    composition = get_object_or_404(DevoirComposition, devoir=devoir, eleve=request.user)

    if devoir.statut != Devoir.Statut.EN_COURS:
        messages.error(request, "Ce devoir n'est pas en cours.")
        return redirect('eleve_programme')

    matieres_valides = DevoirMatiere.objects.filter(
        devoir=devoir, statut=DevoirMatiere.StatutEP.VALIDE
    )

    return render(request, 'devoirs/eleve_compose.html', {
        'devoir': devoir,
        'composition': composition,
        'matieres': matieres_valides,
    })


@login_required
def eleve_submit_reponse_view(request, devoir_id):
    if request.method != 'POST':
        return redirect('eleve_programme')

    devoir = get_object_or_404(Devoir, pk=devoir_id)
    composition, _ = DevoirComposition.objects.get_or_create(
        devoir=devoir, eleve=request.user,
        defaults={'classe': devoir.classes.first()}
    )

    notes = {}
    total = 0
    count = 0
    for matiere in devoir.matieres.all():
        note_str = request.POST.get(f'note_{matiere.id}', '10')
        try:
            note = float(note_str)
        except ValueError:
            note = 10.0
        notes[str(matiere.id)] = note
        total += note
        count += 1

    moyenne = round(total / count, 2) if count > 0 else 0

    composition.statut = DevoirComposition.StatutComp.COMPOSE
    composition.moyenne_generale = moyenne
    composition.details_notes = notes
    composition.composed_at = timezone.now()

    if moyenne >= 10:
        composition.resultat = DevoirComposition.Resultat.ADMIS
    elif moyenne >= 8:
        composition.resultat = DevoirComposition.Resultat.AJOURNE
    else:
        composition.resultat = DevoirComposition.Resultat.REFUSE

    composition.save()
    messages.success(request, f"Devoir soumis. Moyenne: {moyenne}/20")
    return redirect('eleve_resultats')


@login_required
def eleve_resultats_view(request):
    compositions = DevoirComposition.objects.filter(
        eleve=request.user
    ).select_related('devoir').order_by('-devoir__date_debut')

    certificats = Certificat.objects.filter(eleve=request.user).order_by('-created_at')

    return render(request, 'devoirs/eleve_resultats.html', {
        'compositions': compositions,
        'certificats': certificats,
    })


# ═══════════════════════════════════════════
# CERTIFICATE VIEWS
# ═══════════════════════════════════════════

@login_required
def devoir_certificates_view(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    devoir = get_object_or_404(Devoir, pk=pk)
    compositions = DevoirComposition.objects.filter(
        devoir=devoir, statut=DevoirComposition.StatutComp.COMPOSE
    ).order_by('rang')
    return render(request, 'devoirs/admin_certificates.html', {
        'devoir': devoir,
        'compositions': compositions,
    })


@login_required
def devoir_generate_certificates_view(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    devoir = get_object_or_404(Devoir, pk=pk)
    compositions = DevoirComposition.objects.filter(
        devoir=devoir, statut=DevoirComposition.StatutComp.COMPOSE
    )

    count = 0
    for comp in compositions:
        if comp.resultat == DevoirComposition.Resultat.ADMIS:
            cert, created = Certificat.objects.get_or_create(
                eleve=comp.eleve,
                devoir=devoir,
                type_certificat=Certificat.TypeCertificat.ADMISSION,
                defaults={
                    'moyenne_obtenue': comp.moyenne_generale,
                    'mention': _get_mention(comp.moyenne_generale),
                }
            )
            if created or not cert.file_pdf:
                _generate_certificat_pdf(cert)
                count += 1

    messages.success(request, f"{count} certificat(s) généré(s).")
    return redirect('devoir_certificates', pk=pk)


@login_required
def certificat_download_view(request, pk):
    cert = get_object_or_404(Certificat, pk=pk)
    if request.user.role != 'admin' and cert.eleve != request.user:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    if not cert.file_pdf:
        _generate_certificat_pdf(cert)

    if not cert.file_pdf:
        raise Http404("Certificat non disponible")

    return FileResponse(
        cert.file_pdf.open('rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=f"certificat_{cert.numero_certificat}.pdf"
    )


# ═══════════════════════════════════════════
# SERVICES
# ═══════════════════════════════════════════

def _get_mention(moyenne):
    if moyenne >= 18:
        return 'Excellent — Tableau d\'Honneur'
    elif moyenne >= 16:
        return 'Très Bien'
    elif moyenne >= 14:
        return 'Bien'
    elif moyenne >= 12:
        return 'Assez Bien'
    elif moyenne >= 10:
        return 'Passable'
    else:
        return 'Insuffisant'


def _generate_certificat_pdf(cert):
    """Génère le PDF d'un certificat avec design administratif."""
    context = {
        'cert': cert,
        'eleve': cert.eleve,
        'numero': cert.numero_certificat,
        'moyenne': cert.moyenne_obtenue,
        'mention': cert.mention,
        'type_certificat': cert.get_type_certificat_display(),
        'date_delivrance': cert.date_delivrance,
        'verification_token': cert.verification_token,
        'admin_phone': ADMIN_PHONE,
        'annee_scolaire': cert.devoir.annee_scolaire if cert.devoir else timezone.now().strftime('%Y-%Y'),
    }

    try:
        html = render_to_string('devoirs/certificat_pdf.html', context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            pdf_content = result.getvalue()
            filename = f"certificat_{cert.numero_certificat}.pdf"
            cert.file_pdf.save(filename, ContentFile(pdf_content), save=True)
            logger.info(f"Certificat {cert.numero_certificat} généré.")
        else:
            logger.error(f"Erreur génération PDF certificat {cert.numero_certificat}")
    except Exception as e:
        logger.error(f"Erreur génération certificat: {e}")
