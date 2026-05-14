from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.contrib import messages
import logging
from .models import Bulletin, BulletinLigne
from .services import BulletinService, get_logo_data_uri


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
        return HttpResponseForbidden("Acces non autorise.")
    return render(request, 'bulletins/detail.html', {'bulletin': bulletin})


@login_required
def generate_bulletin(request, bulletin_id):
    """Genere le bulletin PDF a partir de l'image bulletin.png."""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Acces non autorise.")

    pdf_content = BulletinService.generate_bulletin_from_image_pdf(bulletin)

    if pdf_content is None:
        messages.error(request, "Erreur lors de la generation du bulletin PDF.")
        return redirect('bulletins:detail', bulletin_id=bulletin.id)

    from django.core.files.base import ContentFile
    bulletin.file_pdf.save(f'bulletin_{bulletin.id}.pdf', ContentFile(pdf_content), save=True)
    messages.success(request, "Bulletin PDF genere avec succes.")
    return redirect('bulletins:detail', bulletin_id=bulletin.id)


@login_required
def download_bulletin_pdf(request, bulletin_id):
    """Telechargement direct du bulletin PDF."""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Acces non autorise.")

    logger = logging.getLogger(__name__)

    if not bulletin.file_pdf:
        try:
            BulletinService.generate_bulletin_from_image_pdf(bulletin)
            bulletin.refresh_from_db()
            if not bulletin.file_pdf:
                messages.error(request, "Impossible de generer le bulletin PDF.")
                return redirect('bulletins:detail', bulletin_id=bulletin.id)
        except Exception as e:
            logger.error("Erreur generation PDF bulletin %s: %s", bulletin_id, e)
            messages.error(request, "Erreur lors de la generation du PDF.")
            return redirect('bulletins:detail', bulletin_id=bulletin.id)

    try:
        if not bulletin.file_pdf.storage.exists(bulletin.file_pdf.name):
            logger.warning("Fichier PDF manquant pour bulletin %s, regeneration...", bulletin_id)
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
        logger.error("Erreur verification fichier bulletin %s: %s", bulletin_id, e)
        messages.error(request, "Erreur lors de l'acces au fichier PDF.")
        return redirect('bulletins:detail', bulletin_id=bulletin.id)

    try:
        response = HttpResponse(bulletin.file_pdf.read(), content_type='application/pdf')
        filename = "bulletin_%s_%s_%s.pdf" % (
            bulletin.eleve.last_name, bulletin.periode, bulletin.annee_scolaire
        )
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response
    except Exception as e:
        logger.error("Erreur lecture fichier bulletin %s: %s", bulletin_id, e)
        messages.error(request, "Erreur lors du telechargement du fichier.")
        return redirect('bulletins:detail', bulletin_id=bulletin.id)


@login_required
def preview_bulletin(request, bulletin_id):
    """Apercu PDF du bulletin officiel."""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Acces non autorise.")

    logger = logging.getLogger(__name__)

    try:
        pdf_content = BulletinService.generate_bulletin_from_image_pdf(bulletin)

        if not pdf_content:
            logger.error("Erreur generation PDF bulletin %s", bulletin_id)
            messages.error(request, "Impossible de generer le bulletin PDF.")
            return redirect('bulletins:detail', bulletin_id=bulletin_id)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = "apercu_bulletin_%s_%s_%s.pdf" % (
            bulletin.eleve.last_name, bulletin.periode, bulletin.annee_scolaire
        )
        response['Content-Disposition'] = 'inline; filename="%s"' % filename
        return response

    except Exception as e:
        logger.error("Erreur preview bulletin %s: %s", bulletin_id, e)
        messages.error(request, "Erreur lors de la generation du PDF.")
        return redirect('bulletins:detail', bulletin_id=bulletin_id)


# ---------------------------------------------------------------
# BULLETIN SCOLAIRE - Format officiel Benin (INTERRO + DEV 1/2/3)
# ---------------------------------------------------------------

def _build_bulletin_scolaire_context(bulletin):
    """
    Construit le contexte pour le template bulletin_scolaire.html
    a partir d'un objet Bulletin existant.
    """
    eleve = bulletin.eleve

    # Periode -> numero de trimestre
    periode_map = {'T1': 1, 'T2': 2, 'T3': 3, 'S1': 1, 'S2': 2, 'AN': 3}
    trimestre = periode_map.get(bulletin.periode, 1)

    # Annee scolaire : "2025-2026" -> debut=25, fin=26
    annee_parts = bulletin.annee_scolaire.replace(' ', '').split('-')
    debut = annee_parts[0][-2:] if len(annee_parts) > 0 else '25'
    fin   = annee_parts[1][-2:] if len(annee_parts) > 1 else '26'
    annee = {'debut': debut, 'fin': fin}

    # Lignes de matieres depuis BulletinLigne
    lignes = bulletin.lignes.all().order_by('matiere')
    matieres = []
    total_coef = 0
    total_moy_coef = 0

    for ligne in lignes:
        coef = float(ligne.coefficient or 1)
        note = float(ligne.note or 0)
        if ligne.note_moy_coeff is not None:
            moy_coef = float(ligne.note_moy_coeff)
        else:
            moy_coef = round(note * coef, 2)
        total_coef += coef
        total_moy_coef += moy_coef

        coef_display = int(coef) if coef == int(coef) else coef
        interro = float(ligne.controle) if ligne.controle is not None else ''
        dev1    = float(ligne.devoir)   if ligne.devoir   is not None else ''

        matieres.append({
            'nom': ligne.matiere,
            'coef': coef_display,
            'interro': interro,
            'dev1': dev1,
            'dev2': '',
            'dev3': '',
            'moyenne': note,
            'moy_coef': moy_coef,
            'rang': ligne.rang or '',
            'appreciation': ligne.appreciation or '',
        })

    if total_coef:
        moyenne_trimestre = round(total_moy_coef / total_coef, 2)
    else:
        moyenne_trimestre = 0

    total_coef_display = int(total_coef) if total_coef == int(total_coef) else total_coef

    # Resultats globaux
    rang_str = str(bulletin.rang)
    if bulletin.effectif_total:
        rang_str = "%s / %s" % (bulletin.rang, bulletin.effectif_total)
    resultats = {
        'moyenne':        str(bulletin.moyenne_generale).replace('.', ','),
        'rang':           rang_str,
        'plus_forte':     '',
        'plus_faible':    '',
        'moyenne_classe': '',
        'mention':        bulletin.decision_conseil or '',
    }

    # Avis du conseil
    avis = {
        'felicitations':   False,
        'tableau_honneur': False,
        'encouragement':   False,
        'avertissement':   False,
        'blame':           False,
    }
    obs = (bulletin.observation_conseil or '').lower()
    if 'felicitation' in obs:
        avis['felicitations'] = True
    if 'honneur' in obs:
        avis['tableau_honneur'] = True
    if 'encouragement' in obs:
        avis['encouragement'] = True
    if 'avertissement' in obs:
        avis['avertissement'] = True
    if 'blame' in obs:
        avis['blame'] = True

    # Decision
    decision_raw = (bulletin.decision_conseil or '').lower()
    if 'redouble' in decision_raw:
        decision = 'redouble'
    elif 'exclu' in decision_raw:
        decision = 'exclu'
    else:
        decision = 'passe'

    # Nom complet de l'eleve
    if hasattr(eleve, 'get_full_name') and callable(eleve.get_full_name):
        nom_prenoms = eleve.get_full_name()
    else:
        nom_prenoms = getattr(eleve, 'username', '')

    return {
        'logo_benin': '/static/images/armoiries_benin.png',
        'etablissement': {
            'bp':    '',
            'tel':   '',
            'ville': 'Cotonou',
        },
        'annee':     annee,
        'trimestre': trimestre,
        'eleve': {
            'nom_prenoms':    nom_prenoms,
            'date_naissance': getattr(eleve, 'date_naissance', '') or '',
            'lieu_naissance': getattr(eleve, 'lieu_naissance', '') or '',
            'sexe':           getattr(eleve, 'sexe', '') or '',
            'classe':         bulletin.classe,
            'effectif':       bulletin.effectif_total or '',
            'matricule':      getattr(eleve, 'matricule', '') or getattr(eleve, 'username', ''),
            'statut':         getattr(eleve, 'statut', '') or 'Nouveau',
        },
        'matieres': matieres,
        'totaux': {
            'coef':     total_coef_display,
            'moy_coef': round(total_moy_coef, 2),
        },
        'moyenne_trimestre': moyenne_trimestre,
        'resultats':         resultats,
        'avis':              avis,
        'decision':          decision,
        'fait_a':            'Cotonou',
        'fait_le':           '',
    }


@login_required
def bulletin_scolaire_html(request, bulletin_id):
    """
    Affiche le bulletin au format officiel beninois (HTML) dans le navigateur.
    URL : /bulletins/<uuid>/scolaire/
    """
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Acces non autorise.")
    context = _build_bulletin_scolaire_context(bulletin)
    return render(request, 'bulletins/bulletin.html', context)


@login_required
def bulletin_scolaire_pdf(request, bulletin_id):
    """
    Genere et telecharge le bulletin au format PDF officiel beninois.
    Utilise WeasyPrint si disponible, sinon xhtml2pdf.
    URL : /bulletins/<uuid>/scolaire/pdf/
    """
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Acces non autorise.")

    context = _build_bulletin_scolaire_context(bulletin)
    html_string = render_to_string(
        'bulletins/bulletin.html', context, request=request
    )
    eleve_nom = getattr(bulletin.eleve, 'last_name', 'eleve')
    filename = "bulletin_scolaire_%s_%s_%s.pdf" % (
        eleve_nom, bulletin.periode, bulletin.annee_scolaire
    )

    # Tentative WeasyPrint
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_bytes = WeasyHTML(
            string=html_string,
            base_url=request.build_absolute_uri('/')
        ).write_pdf()
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="%s"' % filename
        return response
    except ImportError:
        pass
    except Exception as e:
        logging.getLogger(__name__).warning("WeasyPrint erreur: %s, fallback xhtml2pdf", e)

    # Fallback xhtml2pdf
    try:
        from io import BytesIO
        from xhtml2pdf import pisa
        result = BytesIO()
        pisa_status = pisa.CreatePDF(html_string, dest=result, encoding='utf-8')
        if pisa_status.err:
            return HttpResponse("Erreur lors de la generation du PDF.", status=500)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="%s"' % filename
        return response
    except Exception as e:
        logging.getLogger(__name__).error("xhtml2pdf erreur: %s", e)
        return HttpResponse("Impossible de generer le PDF : %s" % e, status=500)


def verify_and_download(request, token):
    """
    Endpoint PUBLIC pour verification via QR code.
    Permet de telecharger le bulletin PDF en scannant le QR.
    Pas d'authentification requise - le token sert de cle de securite.
    """
    bulletin = get_object_or_404(Bulletin, verification_token=token)
    logger = logging.getLogger(__name__)

    need_regeneration = False

    if not bulletin.file_pdf:
        need_regeneration = True
    else:
        try:
            if not bulletin.file_pdf.storage.exists(bulletin.file_pdf.name):
                need_regeneration = True
                bulletin.file_pdf.delete(save=False)
        except Exception as e:
            logger.error("Erreur verification fichier QR %s: %s", token, e)
            need_regeneration = True
            bulletin.file_pdf.delete(save=False)

    if need_regeneration:
        try:
            BulletinService.generate_bulletin_from_image_pdf(bulletin)
            bulletin.refresh_from_db()
        except Exception as e:
            logger.error("Erreur generation PDF via QR %s: %s", token, e)
            return HttpResponse("Erreur lors de la generation du PDF.", status=500)

    if not bulletin.file_pdf:
        return HttpResponse("Bulletin PDF non disponible.", status=500)

    try:
        response = HttpResponse(bulletin.file_pdf.read(), content_type='application/pdf')
        filename = "bulletin_%s_%s_%s.pdf" % (
            bulletin.eleve.last_name, bulletin.periode, bulletin.annee_scolaire
        )
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response
    except Exception as e:
        logger.error("Erreur lecture fichier via QR %s: %s", token, e)
        return HttpResponse("Erreur lors du telechargement.", status=500)


# ---------------------------------------------------------------
# PAGE CRÉATION / ÉDITION — Bulletin Officiel
# ---------------------------------------------------------------

COMPORTEMENT_CRITERES = [
    {'key': 'comport_ponctualite', 'label': 'Ponctualité'},
    {'key': 'comport_travail',     'label': 'Travail'},
    {'key': 'comport_discipline',  'label': 'Discipline'},
    {'key': 'comport_assiduite',   'label': 'Assiduité'},
]

AVIS_OPTIONS = [
    {'key': 'avis_felicitations',   'label': 'Félicitations'},
    {'key': 'avis_tableau_honneur', 'label': 'Tableau d\'honneur'},
    {'key': 'avis_encouragement',   'label': 'Encouragement'},
    {'key': 'avis_avertissement',   'label': 'Avertissement de travail'},
    {'key': 'avis_blame',           'label': 'Blâme'},
]

DECISIONS = [
    {'val': 'passe',    'label': 'Passe',    'icon': 'fa-check-circle',   'color': 'green-400'},
    {'val': 'redouble', 'label': 'Redouble', 'icon': 'fa-rotate-left',    'color': 'orange-400'},
    {'val': 'exclu',    'label': 'Exclu',    'icon': 'fa-ban',            'color': 'red-400'},
]

MATIERES_DEFAUT = [
    'Français', 'Mathématiques', 'Anglais', 'Histoire-Géographie',
    'SVT', 'PCT', 'EPS', 'Langue Vivante 2',
]


def _parse_form_matieres(post, nb):
    matieres = []
    for i in range(nb):
        nom = post.get('mat_nom_%d' % i, '').strip()
        if not nom:
            continue
        def safe_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None
        coef   = safe_float(post.get('mat_coef_%d' % i))
        interro= safe_float(post.get('mat_interro_%d' % i))
        dev1   = safe_float(post.get('mat_dev1_%d' % i))
        dev2   = safe_float(post.get('mat_dev2_%d' % i))
        dev3   = safe_float(post.get('mat_dev3_%d' % i))
        moy    = safe_float(post.get('mat_moy_%d' % i))
        moy_cf = safe_float(post.get('mat_moy_coef_%d' % i))
        rang   = post.get('mat_rang_%d' % i, '')
        app    = post.get('mat_app_%d' % i, '')
        matieres.append({
            'nom': nom, 'coef': coef or 1,
            'interro': interro, 'dev1': dev1, 'dev2': dev2, 'dev3': dev3,
            'moyenne': moy, 'moy_coef': moy_cf,
            'rang': rang, 'appreciation': app,
        })
    return matieres


def _build_officiel_context_from_post(post):
    nb = int(post.get('nb_matieres', 0))
    matieres = _parse_form_matieres(post, nb)
    total_coef = sum(float(m['coef'] or 0) for m in matieres)
    total_moy_coef = sum(float(m['moy_coef'] or 0) for m in matieres if m['moy_coef'])
    moy_trim = round(total_moy_coef / total_coef, 2) if total_coef else 0

    trimestre = int(post.get('trimestre', 1))
    debut = str(post.get('annee_debut', '2025'))[-2:]
    fin   = str(post.get('annee_fin',   '2026'))[-2:]

    comportements = []
    for c in COMPORTEMENT_CRITERES:
        comportements.append({
            'label': c['label'],
            'valeur': post.get(c['key'], 'Moyen'),
        })

    avis = {
        'felicitations':   bool(post.get('avis_felicitations')),
        'tableau_honneur': bool(post.get('avis_tableau_honneur')),
        'encouragement':   bool(post.get('avis_encouragement')),
        'avertissement':   bool(post.get('avis_avertissement')),
        'blame':           bool(post.get('avis_blame')),
    }

    return {
        'logo_benin': '/static/images/armoiries_benin.png',
        'etablissement': {
            'nom':   post.get('etablissement_nom', 'Academie Numerique'),
            'bp':    post.get('etablissement_bp', ''),
            'tel':   post.get('etablissement_tel', ''),
            'ville': post.get('etablissement_ville', 'Cotonou'),
        },
        'annee':     {'debut': debut, 'fin': fin},
        'trimestre': trimestre,
        'eleve': {
            'nom_prenoms':    post.get('eleve_nom', ''),
            'date_naissance': post.get('eleve_dob', ''),
            'lieu_naissance': post.get('eleve_lieu', ''),
            'sexe':           post.get('eleve_sexe', 'M'),
            'classe':         post.get('eleve_classe', ''),
            'effectif':       post.get('eleve_effectif', ''),
            'matricule':      post.get('eleve_matricule', ''),
            'statut':         post.get('eleve_statut', 'Nouveau'),
        },
        'matieres': matieres,
        'matieres_defaut': MATIERES_DEFAUT,
        'totaux': {
            'coef':     int(total_coef) if total_coef == int(total_coef) else total_coef,
            'moy_coef': round(total_moy_coef, 2),
        },
        'moyenne_trimestre': moy_trim,
        'resultats': {
            'moyenne':        post.get('res_moyenne', ''),
            'rang':           post.get('res_rang', ''),
            'plus_forte':     post.get('res_plus_forte', ''),
            'plus_faible':    post.get('res_plus_faible', ''),
            'moyenne_classe': post.get('res_moy_classe', ''),
            'mention':        post.get('res_mention', ''),
        },
        'absences': {
            'justifiees':   post.get('abs_justifiees', '0'),
            'injustifiees': post.get('abs_injustifiees', '0'),
            'heures':       post.get('abs_heures', '0'),
            'retards':      post.get('abs_retards', '0'),
        },
        'comportements': comportements,
        'observation': post.get('observation', ''),
        'avis':        avis,
        'decision':    post.get('decision', 'passe'),
        'fait_a':      post.get('fait_a', 'Cotonou'),
        'fait_le':     post.get('fait_le', ''),
        'qr_code_url': '',
    }


def _form_context(form_data=None, bulletin=None):
    nb = len(form_data.get('matieres', [])) if form_data else 0
    return {
        'bulletin':             bulletin,
        'form_data':            form_data or {},
        'matieres_range':       list(range(nb)),
        'matieres_form':        form_data.get('matieres', []) if form_data else [],
        'comportement_criteres':COMPORTEMENT_CRITERES,
        'avis_options':         AVIS_OPTIONS,
        'decisions':            DECISIONS,
    }


@login_required
def bulletin_creer(request):
    """
    Page de creation d'un nouveau bulletin officiel.
    GET  -> affiche le formulaire vide
    POST -> sauvegarde et redirige vers l'apercu
    """
    from django.utils import timezone

    if request.method == 'POST':
        ctx = _build_officiel_context_from_post(request.POST)
        # Construire l'annee scolaire
        annee_scolaire = "%s-%s" % (
            request.POST.get('annee_debut', '2025'),
            request.POST.get('annee_fin',   '2026')
        )
        trimestre_map = {'1': 'T1', '2': 'T2', '3': 'T3'}
        periode = trimestre_map.get(request.POST.get('trimestre', '1'), 'T1')

        # Sauvegarder dans la base
        bulletin = Bulletin.objects.create(
            eleve=request.user,
            classe=request.POST.get('eleve_classe', ''),
            annee_scolaire=annee_scolaire,
            periode=periode,
            type_bulletin=Bulletin.TypeBulletin.ADMINISTRATIF,
            moyenne_generale=float(
                (request.POST.get('res_moyenne') or '0').replace(',', '.')
            ) if request.POST.get('res_moyenne') else 0,
            rang=int(request.POST.get('res_rang', '1').split('/')[0].strip() or 1),
            effectif_total=int(request.POST.get('eleve_effectif') or 0),
            decision_conseil=request.POST.get('res_mention', ''),
            absences=int(request.POST.get('abs_justifiees') or 0),
            heures_absences=int(request.POST.get('abs_heures') or 0),
            retards=int(request.POST.get('abs_retards') or 0),
            comportement_ponctualite=request.POST.get('comport_ponctualite', 'Moyen'),
            comportement_travail=request.POST.get('comport_travail', 'Moyen'),
            comportement_discipline=request.POST.get('comport_discipline', 'Moyen'),
            comportement_assiduite=request.POST.get('comport_assiduite', 'Moyen'),
            observation_conseil=request.POST.get('observation', ''),
        )

        # Sauvegarder les lignes de notes
        nb = int(request.POST.get('nb_matieres', 0))
        for mat in _parse_form_matieres(request.POST, nb):
            BulletinLigne.objects.create(
                bulletin=bulletin,
                matiere=mat['nom'],
                coefficient=mat['coef'],
                controle=mat['interro'],
                devoir=mat['dev1'],
                note=mat['moyenne'] or 0,
                note_moy_coeff=mat['moy_coef'],
                rang=int(mat['rang']) if str(mat['rang']).isdigit() else 0,
                appreciation=mat['appreciation'],
            )

        messages.success(request, "Bulletin cree avec succes !")
        return redirect('bulletins:scolaire_html', bulletin_id=bulletin.id)

    # GET - formulaire vide
    ctx = {
        'bulletin':              None,
        'form_data':             {},
        'matieres_range':        range(0),
        'matieres_form':         [],
        'comportement_criteres': COMPORTEMENT_CRITERES,
        'avis_options':          AVIS_OPTIONS,
        'decisions':             DECISIONS,
    }
    return render(request, 'bulletins/bulletin_creer_editer.html', ctx)


@login_required
def bulletin_editer(request, bulletin_id):
    """
    Page d'edition d'un bulletin existant.
    GET  -> pré-remplit le formulaire
    POST -> sauvegarde les modifications
    """
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if request.user.role not in ('admin', 'prof', 'cp') and bulletin.eleve != request.user:
        return HttpResponseForbidden("Acces non autorise.")

    if request.method == 'POST':
        trimestre_map = {'1': 'T1', '2': 'T2', '3': 'T3'}
        annee_scolaire = "%s-%s" % (
            request.POST.get('annee_debut', '2025'),
            request.POST.get('annee_fin',   '2026')
        )
        bulletin.classe         = request.POST.get('eleve_classe', bulletin.classe)
        bulletin.annee_scolaire = annee_scolaire
        bulletin.periode        = trimestre_map.get(request.POST.get('trimestre', '1'), 'T1')
        bulletin.effectif_total = int(request.POST.get('eleve_effectif') or bulletin.effectif_total)
        bulletin.moyenne_generale = float(
            (request.POST.get('res_moyenne') or str(bulletin.moyenne_generale)).replace(',', '.')
        )
        rang_raw = request.POST.get('res_rang', str(bulletin.rang)).split('/')[0].strip()
        bulletin.rang              = int(rang_raw) if rang_raw.isdigit() else bulletin.rang
        bulletin.decision_conseil  = request.POST.get('res_mention', bulletin.decision_conseil)
        bulletin.absences          = int(request.POST.get('abs_justifiees') or bulletin.absences)
        bulletin.heures_absences   = int(request.POST.get('abs_heures') or bulletin.heures_absences)
        bulletin.retards           = int(request.POST.get('abs_retards') or bulletin.retards)
        bulletin.comportement_ponctualite = request.POST.get('comport_ponctualite', bulletin.comportement_ponctualite)
        bulletin.comportement_travail     = request.POST.get('comport_travail',     bulletin.comportement_travail)
        bulletin.comportement_discipline  = request.POST.get('comport_discipline',  bulletin.comportement_discipline)
        bulletin.comportement_assiduite   = request.POST.get('comport_assiduite',   bulletin.comportement_assiduite)
        bulletin.observation_conseil      = request.POST.get('observation', bulletin.observation_conseil)
        bulletin.save()

        # Remplacer les lignes
        bulletin.lignes.all().delete()
        nb = int(request.POST.get('nb_matieres', 0))
        for mat in _parse_form_matieres(request.POST, nb):
            BulletinLigne.objects.create(
                bulletin=bulletin,
                matiere=mat['nom'],
                coefficient=mat['coef'],
                controle=mat['interro'],
                devoir=mat['dev1'],
                note=mat['moyenne'] or 0,
                note_moy_coeff=mat['moy_coef'],
                rang=int(mat['rang']) if str(mat['rang']).isdigit() else 0,
                appreciation=mat['appreciation'],
            )

        messages.success(request, "Bulletin mis a jour avec succes !")
        return redirect('bulletins:scolaire_html', bulletin_id=bulletin.id)

    # GET - pré-remplir le formulaire
    annee_parts = bulletin.annee_scolaire.replace(' ', '').split('-')
    trimestre_map_inv = {'T1': '1', 'T2': '2', 'T3': '3', 'S1': '1', 'S2': '2', 'AN': '3'}

    lignes = list(bulletin.lignes.all().order_by('matiere'))
    matieres_form = [{
        'nom':          l.matiere,
        'coef':         str(l.coefficient),
        'interro':      str(l.controle or ''),
        'dev1':         str(l.devoir or ''),
        'dev2':         '',
        'dev3':         '',
        'moyenne':      str(l.note or ''),
        'moy_coef':     str(l.note_moy_coeff or ''),
        'rang':         str(l.rang or ''),
        'appreciation': l.appreciation or '',
    } for l in lignes]

    rang_str = "%s / %s" % (bulletin.rang, bulletin.effectif_total) if bulletin.effectif_total else str(bulletin.rang)

    form_data = {
        'etablissement_nom':   'Academie Numerique',
        'etablissement_ville': 'Cotonou',
        'etablissement_bp':    '',
        'etablissement_tel':   '',
        'trimestre':           trimestre_map_inv.get(bulletin.periode, '1'),
        'annee_debut':         annee_parts[0] if len(annee_parts) > 0 else '2025',
        'annee_fin':           annee_parts[1] if len(annee_parts) > 1 else '2026',
        'eleve_nom':           bulletin.eleve.get_full_name() if hasattr(bulletin.eleve, 'get_full_name') else '',
        'eleve_dob':           str(getattr(bulletin.eleve, 'date_naissance', '') or ''),
        'eleve_lieu':          getattr(bulletin.eleve, 'lieu_naissance', '') or '',
        'eleve_sexe':          getattr(bulletin.eleve, 'sexe', 'M') or 'M',
        'eleve_classe':        bulletin.classe,
        'eleve_effectif':      str(bulletin.effectif_total or ''),
        'eleve_matricule':     getattr(bulletin.eleve, 'matricule', '') or '',
        'eleve_statut':        getattr(bulletin.eleve, 'statut', 'Nouveau') or 'Nouveau',
        'res_moyenne':         str(bulletin.moyenne_generale).replace('.', ','),
        'res_rang':            rang_str,
        'res_mention':         bulletin.decision_conseil or '',
        'abs_justifiees':      str(bulletin.absences or 0),
        'abs_heures':          str(bulletin.heures_absences or 0),
        'abs_retards':         str(bulletin.retards or 0),
        'abs_injustifiees':    '0',
        'comport_ponctualite': bulletin.comportement_ponctualite,
        'comport_travail':     bulletin.comportement_travail,
        'comport_discipline':  bulletin.comportement_discipline,
        'comport_assiduite':   bulletin.comportement_assiduite,
        'observation':         bulletin.observation_conseil or '',
        'decision':            'passe',
        'fait_a':              'Cotonou',
        'fait_le':             '',
        'matieres':            matieres_form,
    }

    ctx = {
        'bulletin':              bulletin,
        'form_data':             form_data,
        'matieres_range':        range(len(matieres_form)),
        'matieres_form':         matieres_form,
        'comportement_criteres': COMPORTEMENT_CRITERES,
        'avis_options':          AVIS_OPTIONS,
        'decisions':             DECISIONS,
    }
    return render(request, 'bulletins/bulletin_creer_editer.html', ctx)
