"""
Vues : espace paiement élève, paiement par tranches, dossier de candidature, admin config.
"""

import logging
from datetime import timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .models import (
    AbonnementEleve, PlanAbonnementScolaire,
    PlanEchelonnement, TranchePaiement,
    ConfigTarifCandidature, DocumentRequis,
    DossierCandidature, SoumissionDocument,
    PaiementAbonnement, ConfigurationFedaPay,
)
from .fedapay_service import FedaPayService
from .utils import paiements_actifs
from core.models import Organisation as Etablissement
from subscriptions.decorators import prof_required

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────

def _get_abonnement_actif(user):
    """Renvoie l'AbonnementEleve actif ou None."""
    return AbonnementEleve.objects.filter(
        eleve=user,
        statut=AbonnementEleve.StatutAbonnement.ACTIF,
        date_fin__gt=timezone.now(),
    ).select_related('plan', 'plan_echelonnement').first()


def _get_tarif(user, etablissement=None):
    """Retourne le ConfigTarifCandidature correspondant au type du candidat."""
    type_c = getattr(user, 'type_candidat', 'non_defini')
    qs = ConfigTarifCandidature.objects.filter(type_candidat=type_c, is_actif=True)
    if etablissement:
        tarif = qs.filter(etablissement=etablissement).first()
        if tarif:
            return tarif
    return qs.filter(etablissement__isnull=True).first()


def _paiements_actifs_pour_user(user):
    """Vérifie si les paiements sont activés pour l'établissement lié à l'utilisateur."""
    try:
        etablissement = getattr(user, 'etablissement', None)
        if etablissement:
            return paiements_actifs(etablissement)
    except Exception:
        pass
    # Vérifier s'il existe au moins un établissement avec FedaPay configuré et actif
    return ConfigurationFedaPay.objects.filter(is_actif=True).exists()


def _verifier_acces_service(user):
    """
    Renvoie un dict décrivant l'état d'accès de l'utilisateur.
    {
      'autorise': bool,
      'raison': str,
      'abonnement': AbonnementEleve | None,
      'tranche_due': TranchePaiement | None,
    }
    """
    role = getattr(user, 'role', '')
    if role in ('professeur', 'admin', 'superadmin', 'directeur', 'conseiller'):
        return {'autorise': True, 'raison': 'staff', 'abonnement': None, 'tranche_due': None}

    if not _paiements_actifs_pour_user(user):
        return {'autorise': True, 'raison': 'paiements_desactives', 'abonnement': None, 'tranche_due': None}

    abonnement = _get_abonnement_actif(user)
    if not abonnement:
        return {'autorise': False, 'raison': 'pas_abonnement', 'abonnement': None, 'tranche_due': None}

    # Vérifier le plan échelonné si applicable
    try:
        plan_ech = abonnement.plan_echelonnement
        prochaine = plan_ech.prochaine_tranche_impayee
        if prochaine and prochaine.est_en_retard:
            return {
                'autorise': False,
                'raison': 'tranche_en_retard',
                'abonnement': abonnement,
                'tranche_due': prochaine,
            }
    except PlanEchelonnement.DoesNotExist:
        pass

    return {'autorise': True, 'raison': 'abonnement_actif', 'abonnement': abonnement, 'tranche_due': None}


# ──────────────────────────────────────────────────────────────
#  VUE PRINCIPALE : ESPACE PAIEMENT ÉLÈVE
# ──────────────────────────────────────────────────────────────

@login_required
def espace_paiement(request):
    """Tableau de bord paiement de l'élève : statut, tranches, options."""
    user = request.user
    acces = _verifier_acces_service(user)
    abonnement = _get_abonnement_actif(user)

    # Historique de tous les abonnements
    historique_abonnements = AbonnementEleve.objects.filter(
        eleve=user
    ).select_related('plan').order_by('-date_souscription')[:10]

    # Plan échelonné actif
    plan_ech = None
    tranches = []
    if abonnement:
        try:
            plan_ech = abonnement.plan_echelonnement
            tranches = list(plan_ech.tranches.all())
        except PlanEchelonnement.DoesNotExist:
            pass

    # Tarifs disponibles pour ce type de candidat
    tarif = _get_tarif(user)
    plans_disponibles = PlanAbonnementScolaire.objects.filter(is_actif=True, visible_sur_site=True)

    # Type de candidat pour l'affichage
    type_label = {
        'academie': 'Candidat Académie Numérique',
        'libre': 'Candidat Libre',
    }.get(getattr(user, 'type_candidat', ''), 'Non défini')

    return render(request, 'payments/espace_paiement.html', {
        'acces': acces,
        'abonnement': abonnement,
        'plan_ech': plan_ech,
        'tranches': tranches,
        'historique_abonnements': historique_abonnements,
        'tarif': tarif,
        'plans_disponibles': plans_disponibles,
        'type_label': type_label,
    })


# ──────────────────────────────────────────────────────────────
#  SOUSCRIPTION AVEC ÉCHELONNEMENT
# ──────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def initier_souscription_echelonnee(request):
    """
    Crée un AbonnementEleve + PlanEchelonnement + TranchePaiement
    puis initie le paiement FedaPay de la première tranche.
    """
    plan_id = request.POST.get('plan_id')
    nombre_tranches = int(request.POST.get('nombre_tranches', 1))
    periode = request.POST.get('periode', 'mensuel')  # mensuel | trimestriel | annuel
    telephone = request.POST.get('telephone', '')

    plan = get_object_or_404(PlanAbonnementScolaire, id=plan_id, is_actif=True)
    etablissement = plan.etablissement

    # Déterminer le montant selon la période et le tarif du type de candidat
    tarif = _get_tarif(request.user, etablissement)
    if tarif and tarif.tarif_mensuel > 0:
        montants = {
            'mensuel': int(tarif.tarif_mensuel),
            'trimestriel': int(tarif.tarif_trimestriel) or int(tarif.tarif_mensuel * 3),
            'annuel': int(tarif.tarif_annuel) or int(tarif.tarif_mensuel * 12),
        }
        montant_total = montants.get(periode, int(tarif.tarif_mensuel))
    else:
        montant_total = int(plan.prix_mensuel)

    duree_jours = {'mensuel': 30, 'trimestriel': 90, 'annuel': 365}.get(periode, 30)

    config = getattr(etablissement, 'config_fedapay', None)
    if not config or not config.is_actif:
        messages.error(request, "Le système de paiement n'est pas configuré.")
        return redirect('payments:espace_paiement')

    nombre_tranches = min(max(nombre_tranches, 1), tarif.nombre_tranches_max if tarif else 3)
    montant_par_tranche = montant_total // nombre_tranches

    with transaction.atomic():
        abonnement = AbonnementEleve.objects.create(
            eleve=request.user,
            plan=plan,
            etablissement=etablissement,
            statut=AbonnementEleve.StatutAbonnement.EN_ATTENTE,
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(days=duree_jours),
        )

        plan_ech = PlanEchelonnement.objects.create(
            abonnement=abonnement,
            nombre_tranches=nombre_tranches,
            montant_total=montant_total,
            montant_par_tranche=montant_par_tranche,
        )

        today = date.today()
        for i in range(nombre_tranches):
            TranchePaiement.objects.create(
                plan=plan_ech,
                numero=i + 1,
                montant=montant_par_tranche,
                date_echeance=today + timedelta(days=30 * i),
            )

    # Payer la première tranche immédiatement
    premiere_tranche = plan_ech.tranches.first()
    return _initier_paiement_tranche(request, premiere_tranche, telephone)


def _initier_paiement_tranche(request, tranche, telephone=''):
    """Initie un paiement FedaPay pour une tranche spécifique."""
    abonnement = tranche.plan.abonnement
    etablissement = abonnement.etablissement
    fedapay = FedaPayService(etablissement)

    # Créer ou récupérer le customer FedaPay
    customer_id = abonnement.fedapay_customer_id
    if not customer_id:
        customer_id = fedapay.creer_customer(request.user)
        if customer_id:
            abonnement.fedapay_customer_id = customer_id
            abonnement.save(update_fields=['fedapay_customer_id'])

    # Créer le PaiementAbonnement lié à la tranche
    paiement = PaiementAbonnement.objects.create(
        abonnement=abonnement,
        eleve=request.user,
        montant=int(tranche.montant),
        montant_total=int(tranche.montant),
        mode_paiement=PaiementAbonnement.ModePaiement.MOBILE_MONEY,
        statut=PaiementAbonnement.StatutPaiement.EN_ATTENTE,
        telephone_paiement=telephone,
        reference_transaction=f"TRANCHE-{tranche.id.hex[:8]}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
    )

    callback_url = f"{settings.SITE_URL}/payments/paiement/succes/?tranche_id={tranche.id}"
    result = fedapay.creer_transaction(paiement, customer_id, callback_url)

    if not result or not result.get('payment_url'):
        paiement.statut = PaiementAbonnement.StatutPaiement.ECHEC
        paiement.derniere_erreur = 'Impossible d\'obtenir l\'URL FedaPay'
        paiement.save(update_fields=['statut', 'derniere_erreur'])
        messages.error(request, "Impossible d'initier le paiement. Réessayez.")
        return redirect('payments:espace_paiement')

    # Sauvegarder le lien FedaPay sur la tranche
    tranche.fedapay_transaction_id = result['transaction_id']
    tranche.fedapay_url_paiement = result['payment_url']
    tranche.statut = TranchePaiement.Statut.EN_COURS
    tranche.save(update_fields=['fedapay_transaction_id', 'fedapay_url_paiement', 'statut'])

    paiement.statut = PaiementAbonnement.StatutPaiement.EN_COURS
    paiement.save(update_fields=['statut'])

    return redirect(result['payment_url'])


@login_required
def payer_tranche(request, tranche_id):
    """Payer une tranche spécifique (depuis l'espace paiement)."""
    tranche = get_object_or_404(
        TranchePaiement,
        id=tranche_id,
        plan__abonnement__eleve=request.user,
        statut__in=[TranchePaiement.Statut.EN_ATTENTE, TranchePaiement.Statut.EN_RETARD],
    )
    telephone = request.GET.get('tel', '')
    return _initier_paiement_tranche(request, tranche, telephone)


@login_required
def verifier_paiement_tranche(request, tranche_id):
    """Vérification AJAX du statut d'une tranche après retour FedaPay."""
    tranche = get_object_or_404(
        TranchePaiement,
        id=tranche_id,
        plan__abonnement__eleve=request.user,
    )
    abonnement = tranche.plan.abonnement

    if tranche.fedapay_transaction_id:
        fedapay = FedaPayService(abonnement.etablissement)
        status = fedapay.verifier_transaction(tranche.fedapay_transaction_id)
        if status and status.get('status') == 'approved':
            with transaction.atomic():
                tranche.statut = TranchePaiement.Statut.PAYE
                tranche.date_paiement = timezone.now()
                tranche.save(update_fields=['statut', 'date_paiement'])

                # Activer l'abonnement à la première tranche payée
                if tranche.numero == 1:
                    abonnement.statut = AbonnementEleve.StatutAbonnement.ACTIF
                    abonnement.dernier_paiement = timezone.now()
                    abonnement.montant_paye_total += tranche.montant
                    abonnement.nombre_paiements += 1
                    abonnement.save(update_fields=['statut', 'dernier_paiement', 'montant_paye_total', 'nombre_paiements'])

                # Vérifier si toutes les tranches sont payées
                plan_ech = tranche.plan
                if plan_ech.tranches.filter(statut=TranchePaiement.Statut.PAYE).count() == plan_ech.nombre_tranches:
                    plan_ech.statut = PlanEchelonnement.Statut.SOLDE
                    plan_ech.save(update_fields=['statut'])

            return JsonResponse({'status': 'approved', 'redirect': '/payments/paiement/succes/'})

    return JsonResponse({'status': tranche.statut})


# ──────────────────────────────────────────────────────────────
#  DOSSIER DE CANDIDATURE
# ──────────────────────────────────────────────────────────────

@login_required
def mon_dossier(request):
    """Page principale du dossier de candidature de l'élève."""
    user = request.user
    type_c = getattr(user, 'type_candidat', 'non_defini')

    # Récupérer ou créer le dossier
    dossier, _ = DossierCandidature.objects.get_or_create(eleve=user)

    # Documents requis pour ce type de candidat
    from django.db.models import Q
    documents_requis = DocumentRequis.objects.filter(
        is_actif=True
    ).filter(
        Q(type_candidat='tous') | Q(type_candidat=type_c)
    ).order_by('ordre')

    # Soumissions existantes
    soumissions_par_doc = {
        str(s.document_requis_id): s
        for s in dossier.soumissions.select_related('document_requis').all()
    }

    docs_avec_statut = []
    for doc in documents_requis:
        soumission = soumissions_par_doc.get(str(doc.id))
        docs_avec_statut.append({
            'doc': doc,
            'soumission': soumission,
            'statut': soumission.statut if soumission else 'non_soumis',
        })

    nb_obligatoires = documents_requis.filter(est_obligatoire=True).count()
    nb_soumis_valides = sum(
        1 for d in docs_avec_statut
        if d['doc'].est_obligatoire and d['statut'] in ('en_attente', 'valide')
    )

    return render(request, 'payments/mon_dossier.html', {
        'dossier': dossier,
        'docs_avec_statut': docs_avec_statut,
        'nb_obligatoires': nb_obligatoires,
        'nb_soumis_valides': nb_soumis_valides,
        'progression': int(nb_soumis_valides / nb_obligatoires * 100) if nb_obligatoires else 100,
        'type_label': {
            'academie': 'Académie Numérique',
            'libre': 'Candidat Libre',
        }.get(type_c, 'Non défini'),
    })


@login_required
@require_http_methods(["POST"])
def soumettre_document(request, document_id):
    """Soumettre (uploader) un document dans le dossier de candidature."""
    doc_requis = get_object_or_404(DocumentRequis, id=document_id, is_actif=True)
    fichier = request.FILES.get('fichier')

    if not fichier:
        messages.error(request, "Veuillez sélectionner un fichier.")
        return redirect('payments:mon_dossier')

    # Vérifier la taille
    max_octets = doc_requis.taille_max_mo * 1024 * 1024
    if fichier.size > max_octets:
        messages.error(request, f"Fichier trop volumineux (max {doc_requis.taille_max_mo} Mo).")
        return redirect('payments:mon_dossier')

    dossier, _ = DossierCandidature.objects.get_or_create(eleve=request.user)

    # Créer ou remplacer la soumission
    soumission, created = SoumissionDocument.objects.update_or_create(
        dossier=dossier,
        document_requis=doc_requis,
        defaults={
            'fichier': fichier,
            'nom_fichier_original': fichier.name,
            'statut': SoumissionDocument.Statut.EN_ATTENTE,
            'commentaire_admin': '',
        },
    )

    # Mettre à jour le statut du dossier
    dossier.statut = DossierCandidature.Statut.SOUMIS if dossier.est_complet else DossierCandidature.Statut.INCOMPLET
    dossier.date_soumission = timezone.now() if dossier.statut == DossierCandidature.Statut.SOUMIS else dossier.date_soumission
    dossier.save(update_fields=['statut', 'date_soumission'])

    # Notifier les admins par email
    _notifier_admin_document(request, soumission, created)

    messages.success(request, f"Document « {doc_requis.nom} » soumis avec succès.")
    return redirect('payments:mon_dossier')


def _notifier_admin_document(request, soumission, is_new):
    """Envoie un email aux admins quand un document est soumis."""
    try:
        from accounts.models import User
        admins = User.objects.filter(role='admin', is_active=True).values_list('email', flat=True)
        admin_emails = list(admins)
        if not admin_emails:
            admin_emails = [settings.DEFAULT_FROM_EMAIL]

        sujet = f"[Dossier] {'Nouveau' if is_new else 'Mise à jour'} document — {soumission.dossier.eleve.get_full_name()}"
        corps = render_to_string('payments/email_document_soumis.html', {
            'soumission': soumission,
            'eleve': soumission.dossier.eleve,
            'doc': soumission.document_requis,
            'dossier_url': f"{settings.SITE_URL}/payments/admin/dossiers/{soumission.dossier.id}/",
            'site_url': settings.SITE_URL,
        })

        email = EmailMessage(
            subject=sujet,
            body=corps,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
        )
        email.content_subtype = 'html'
        # Joindre le document
        soumission.fichier.open('rb')
        email.attach(soumission.nom_fichier_original or 'document', soumission.fichier.read())
        soumission.fichier.close()
        email.send(fail_silently=True)
    except Exception as e:
        logger.error(f"Erreur envoi email document candidature: {e}")


# ──────────────────────────────────────────────────────────────
#  ADMIN : CONFIGURATION DES TARIFS
# ──────────────────────────────────────────────────────────────

@login_required
@prof_required
def admin_config_tarifs(request):
    """Admin : configurer les tarifs par type de candidat."""
    etablissements = Etablissement.objects.all()
    tarifs = ConfigTarifCandidature.objects.select_related('etablissement').all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            tarif_id = request.POST.get('tarif_id')
            type_candidat = request.POST.get('type_candidat')
            etab_id = request.POST.get('etablissement_id') or None
            etablissement = Etablissement.objects.filter(id=etab_id).first() if etab_id else None

            data = {
                'tarif_mensuel': int(request.POST.get('tarif_mensuel', 0) or 0),
                'tarif_trimestriel': int(request.POST.get('tarif_trimestriel', 0) or 0),
                'tarif_annuel': int(request.POST.get('tarif_annuel', 0) or 0),
                'tarif_correction_unitaire': int(request.POST.get('tarif_correction_unitaire', 0) or 0),
                'tarif_qcm_unitaire': int(request.POST.get('tarif_qcm_unitaire', 0) or 0),
                'paiement_echelonne_autorise': request.POST.get('paiement_echelonne') == 'on',
                'nombre_tranches_max': int(request.POST.get('nombre_tranches_max', 3) or 3),
                'is_actif': True,
            }

            if tarif_id:
                ConfigTarifCandidature.objects.filter(id=tarif_id).update(**data)
                messages.success(request, "Tarif mis à jour.")
            else:
                ConfigTarifCandidature.objects.update_or_create(
                    etablissement=etablissement,
                    type_candidat=type_candidat,
                    defaults=data,
                )
                messages.success(request, "Tarif créé.")

        elif action == 'delete':
            tarif_id = request.POST.get('tarif_id')
            ConfigTarifCandidature.objects.filter(id=tarif_id).delete()
            messages.success(request, "Tarif supprimé.")

        return redirect('payments:admin_config_tarifs')

    return render(request, 'payments/admin_tarifs.html', {
        'tarifs': tarifs,
        'etablissements': etablissements,
        'types_candidat': ConfigTarifCandidature.TypeCandidat.choices,
    })


# ──────────────────────────────────────────────────────────────
#  ADMIN : GESTION DES DOCUMENTS REQUIS
# ──────────────────────────────────────────────────────────────

@login_required
@prof_required
def admin_documents_requis(request):
    """Admin : définir les documents requis pour les candidats."""
    etablissements = Etablissement.objects.all()
    documents = DocumentRequis.objects.select_related('etablissement').order_by('ordre', 'nom')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            doc_id = request.POST.get('doc_id')
            etab_id = request.POST.get('etablissement_id') or None
            etablissement = Etablissement.objects.filter(id=etab_id).first() if etab_id else None

            data = {
                'nom': request.POST.get('nom', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'type_candidat': request.POST.get('type_candidat', 'tous'),
                'est_obligatoire': request.POST.get('est_obligatoire') == 'on',
                'formats_acceptes': request.POST.get('formats_acceptes', 'PDF, JPG, PNG'),
                'taille_max_mo': int(request.POST.get('taille_max_mo', 5) or 5),
                'ordre': int(request.POST.get('ordre', 1) or 1),
                'is_actif': True,
                'etablissement': etablissement,
            }

            if doc_id:
                DocumentRequis.objects.filter(id=doc_id).update(**{k: v for k, v in data.items() if k != 'etablissement'})
                if 'etablissement' in data:
                    DocumentRequis.objects.filter(id=doc_id).update(etablissement=data['etablissement'])
                messages.success(request, "Document mis à jour.")
            else:
                DocumentRequis.objects.create(**data)
                messages.success(request, "Document créé.")

        elif action == 'delete':
            doc_id = request.POST.get('doc_id')
            DocumentRequis.objects.filter(id=doc_id).delete()
            messages.success(request, "Document supprimé.")

        elif action == 'toggle':
            doc_id = request.POST.get('doc_id')
            doc = get_object_or_404(DocumentRequis, id=doc_id)
            doc.is_actif = not doc.is_actif
            doc.save(update_fields=['is_actif'])

        return redirect('payments:admin_documents_requis')

    return render(request, 'payments/admin_documents_requis.html', {
        'documents': documents,
        'etablissements': etablissements,
        'types_candidat': DocumentRequis.TypeCandidat.choices,
    })


# ──────────────────────────────────────────────────────────────
#  ADMIN : DOSSIERS DE CANDIDATURE
# ──────────────────────────────────────────────────────────────

@login_required
@prof_required
def admin_dossiers_candidature(request):
    """Admin : liste et gestion des dossiers de candidature."""
    statut_filtre = request.GET.get('statut', '')
    type_filtre = request.GET.get('type', '')

    dossiers = DossierCandidature.objects.select_related(
        'eleve', 'valide_par'
    ).prefetch_related('soumissions__document_requis').order_by('-date_modification')

    if statut_filtre:
        dossiers = dossiers.filter(statut=statut_filtre)
    if type_filtre:
        dossiers = dossiers.filter(eleve__type_candidat=type_filtre)

    stats = {
        'total': DossierCandidature.objects.count(),
        'incomplets': DossierCandidature.objects.filter(statut='incomplet').count(),
        'soumis': DossierCandidature.objects.filter(statut='soumis').count(),
        'valides': DossierCandidature.objects.filter(statut='valide').count(),
        'rejetes': DossierCandidature.objects.filter(statut='rejete').count(),
    }

    return render(request, 'payments/admin_dossiers.html', {
        'dossiers': dossiers,
        'stats': stats,
        'statuts': DossierCandidature.Statut.choices,
        'statut_filtre': statut_filtre,
        'type_filtre': type_filtre,
    })


@login_required
@prof_required
def admin_detail_dossier(request, dossier_id):
    """Admin : détail d'un dossier de candidature et validation des documents."""
    dossier = get_object_or_404(DossierCandidature, id=dossier_id)
    soumissions = dossier.soumissions.select_related('document_requis').all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'valider_doc':
            soumission_id = request.POST.get('soumission_id')
            soumission = get_object_or_404(SoumissionDocument, id=soumission_id, dossier=dossier)
            soumission.statut = SoumissionDocument.Statut.VALIDE
            soumission.valide_par = request.user
            soumission.date_validation = timezone.now()
            soumission.commentaire_admin = request.POST.get('commentaire', '')
            soumission.save()
            messages.success(request, f"Document « {soumission.document_requis.nom} » validé.")

        elif action == 'rejeter_doc':
            soumission_id = request.POST.get('soumission_id')
            soumission = get_object_or_404(SoumissionDocument, id=soumission_id, dossier=dossier)
            soumission.statut = SoumissionDocument.Statut.REJETE
            soumission.valide_par = request.user
            soumission.date_validation = timezone.now()
            soumission.commentaire_admin = request.POST.get('commentaire', '')
            soumission.save()
            # Notifier l'élève du rejet
            _notifier_eleve_document(dossier.eleve, soumission)
            messages.warning(request, f"Document « {soumission.document_requis.nom} » rejeté.")

        elif action == 'valider_dossier':
            dossier.statut = DossierCandidature.Statut.VALIDE
            dossier.valide_par = request.user
            dossier.date_validation = timezone.now()
            dossier.commentaire_admin = request.POST.get('commentaire', '')
            dossier.save()
            _notifier_eleve_dossier(dossier, valide=True)
            messages.success(request, "Dossier validé. L'élève a été notifié.")

        elif action == 'rejeter_dossier':
            dossier.statut = DossierCandidature.Statut.REJETE
            dossier.commentaire_admin = request.POST.get('commentaire', '')
            dossier.save()
            _notifier_eleve_dossier(dossier, valide=False)
            messages.warning(request, "Dossier rejeté. L'élève a été notifié.")

        return redirect('payments:admin_detail_dossier', dossier_id=dossier_id)

    return render(request, 'payments/admin_detail_dossier.html', {
        'dossier': dossier,
        'soumissions': soumissions,
        'statuts_doc': SoumissionDocument.Statut.choices,
    })


def _notifier_eleve_document(eleve, soumission):
    try:
        statut_label = 'validé' if soumission.statut == 'valide' else 'rejeté'
        sujet = f"[Dossier] Votre document « {soumission.document_requis.nom} » a été {statut_label}"
        corps = (
            f"Bonjour {eleve.get_full_name()},\n\n"
            f"Votre document « {soumission.document_requis.nom} » a été {statut_label}.\n"
        )
        if soumission.commentaire_admin:
            corps += f"\nCommentaire : {soumission.commentaire_admin}\n"
        corps += f"\nConnectez-vous pour voir l'état de votre dossier : {settings.SITE_URL}/payments/mon-dossier/\n"
        from django.core.mail import send_mail
        send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL, [eleve.email], fail_silently=True)
    except Exception as e:
        logger.error(f"Erreur notification élève document: {e}")


def _notifier_eleve_dossier(dossier, valide):
    try:
        eleve = dossier.eleve
        statut_label = 'validé' if valide else 'rejeté'
        sujet = f"[Dossier de candidature] Votre dossier a été {statut_label}"
        corps = (
            f"Bonjour {eleve.get_full_name()},\n\n"
            f"Votre dossier de candidature a été {statut_label}.\n"
        )
        if dossier.commentaire_admin:
            corps += f"\nCommentaire de l'administration : {dossier.commentaire_admin}\n"
        corps += f"\nConnectez-vous : {settings.SITE_URL}/payments/mon-dossier/\n"
        from django.core.mail import send_mail
        send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL, [eleve.email], fail_silently=True)
    except Exception as e:
        logger.error(f"Erreur notification élève dossier: {e}")
