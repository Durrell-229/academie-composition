"""
Vues de gestion admin — alternatives au panneau Django admin.
Accessible depuis le dashboard admin uniquement (role='admin').
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from core.models import Matiere, Classe


def _admin_required(request):
    return request.user.is_authenticated and request.user.role == 'admin'


# ═══════════════════════════════════════════════════════════════
# HUB DE NAVIGATION
# ═══════════════════════════════════════════════════════════════

@login_required
def admin_hub(request):
    """Page centrale de navigation vers tous les outils admin."""
    if not _admin_required(request):
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard')

    from accounts.models import User
    from exams.models import Exam
    from notifications.models import GlobalAnnouncement

    try:
        from cours.models import Course
        cours_pending = Course.objects.filter(status='pending').count()
    except Exception:
        cours_pending = 0

    try:
        from payments.models import BourseScolaire
        bourses_pending = BourseScolaire.objects.filter(statut='en_attente').count()
    except Exception:
        bourses_pending = 0

    context = {
        'total_users':       User.objects.count(),
        'total_eleves':      User.objects.filter(role='eleve').count(),
        'total_profs':       User.objects.filter(role='professeur').count(),
        'exams_pending':     Exam.objects.filter(approval_status='pending').count(),
        'cours_pending':     cours_pending,
        'bourses_pending':   bourses_pending,
        'annonces_actives':  GlobalAnnouncement.objects.filter(est_actif=True).count(),
        'total_classes':     Classe.objects.filter(is_active=True).count(),
        'total_matieres':    Matiere.objects.filter(is_active=True).count(),
    }
    return render(request, 'accounts/admin_hub.html', context)


# ═══════════════════════════════════════════════════════════════
# CLASSES & MATIÈRES
# ═══════════════════════════════════════════════════════════════

@login_required
def admin_classes_matieres(request):
    """Gestion des classes et matières."""
    if not _admin_required(request):
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard')

    tab = request.GET.get('tab', 'classes')
    classes = Classe.objects.order_by('niveau', 'nom')
    matieres = Matiere.objects.order_by('nom')

    return render(request, 'accounts/admin_classes_matieres.html', {
        'tab': tab,
        'classes': classes,
        'matieres': matieres,
        'niveaux': ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Tle', 'CP1', 'CP2', 'CE1', 'CE2', 'CM1', 'CM2'],
    })


@login_required
@require_http_methods(["POST"])
def admin_classe_save(request, classe_id=None):
    if not _admin_required(request):
        return redirect('dashboard')
    nom = request.POST.get('nom', '').strip()
    niveau = request.POST.get('niveau', '').strip()
    section = request.POST.get('section', '').strip()
    annee = request.POST.get('annee_academique', '').strip()
    is_active = request.POST.get('is_active') == 'on'

    if not nom or not niveau:
        messages.error(request, "Nom et niveau sont obligatoires.")
        return redirect('/gestion/classes-matieres/?tab=classes')

    if classe_id:
        obj = get_object_or_404(Classe, id=classe_id)
        obj.nom = nom; obj.niveau = niveau; obj.section = section
        obj.annee_academique = annee; obj.is_active = is_active
        obj.save()
        messages.success(request, f"Classe « {nom} » mise à jour.")
    else:
        Classe.objects.create(nom=nom, niveau=niveau, section=section,
                              annee_academique=annee, is_active=is_active)
        messages.success(request, f"Classe « {nom} » créée.")
    return redirect('/gestion/classes-matieres/?tab=classes')


@login_required
@require_http_methods(["POST"])
def admin_classe_delete(request, classe_id):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(Classe, id=classe_id)
    nom = obj.nom
    obj.is_active = False
    obj.save(update_fields=['is_active'])
    messages.success(request, f"Classe « {nom} » désactivée.")
    return redirect('/gestion/classes-matieres/?tab=classes')


@login_required
@require_http_methods(["POST"])
def admin_matiere_save(request, matiere_id=None):
    if not _admin_required(request):
        return redirect('dashboard')
    nom = request.POST.get('nom', '').strip()
    code = request.POST.get('code', '').strip().upper()
    couleur = request.POST.get('couleur', '#3b82f6')
    icone = request.POST.get('icone', '📚')
    is_active = request.POST.get('is_active') == 'on'

    if not nom or not code:
        messages.error(request, "Nom et code sont obligatoires.")
        return redirect('/gestion/classes-matieres/?tab=matieres')

    if matiere_id:
        obj = get_object_or_404(Matiere, id=matiere_id)
        obj.nom = nom; obj.code = code; obj.couleur = couleur
        obj.icone = icone; obj.is_active = is_active
        obj.save()
        messages.success(request, f"Matière « {nom} » mise à jour.")
    else:
        if Matiere.objects.filter(code=code).exists():
            messages.error(request, f"Le code « {code} » est déjà utilisé.")
            return redirect('/gestion/classes-matieres/?tab=matieres')
        Matiere.objects.create(nom=nom, code=code, couleur=couleur, icone=icone, is_active=is_active)
        messages.success(request, f"Matière « {nom} » créée.")
    return redirect('/gestion/classes-matieres/?tab=matieres')


@login_required
@require_http_methods(["POST"])
def admin_matiere_delete(request, matiere_id):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(Matiere, id=matiere_id)
    nom = obj.nom
    obj.is_active = False
    obj.save(update_fields=['is_active'])
    messages.success(request, f"Matière « {nom} » désactivée.")
    return redirect('/gestion/classes-matieres/?tab=matieres')


# ═══════════════════════════════════════════════════════════════
# APPROBATIONS (examens + cours)
# ═══════════════════════════════════════════════════════════════

@login_required
def admin_approbations(request):
    if not _admin_required(request):
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard')

    from exams.models import Exam
    exams_pending = Exam.objects.filter(
        approval_status='pending'
    ).select_related('createur', 'matiere', 'classe').order_by('-created_at')

    exams_approved = Exam.objects.filter(
        approval_status='approved'
    ).select_related('createur', 'matiere', 'classe').order_by('-created_at')[:20]

    try:
        from cours.models import Course
        cours_pending = Course.objects.filter(
            status='pending'
        ).select_related('creator', 'matiere', 'classe').order_by('-created_at')
        cours_approved = Course.objects.filter(
            status='approved'
        ).select_related('creator', 'matiere', 'classe').order_by('-created_at')[:20]
    except Exception:
        cours_pending = []
        cours_approved = []

    return render(request, 'accounts/admin_approbations.html', {
        'exams_pending':   exams_pending,
        'exams_approved':  exams_approved,
        'cours_pending':   cours_pending,
        'cours_approved':  cours_approved,
        'tab': request.GET.get('tab', 'examens'),
    })


@login_required
@require_http_methods(["POST"])
def admin_approuver_exam(request, exam_id):
    if not _admin_required(request):
        return redirect('dashboard')
    from exams.models import Exam
    exam = get_object_or_404(Exam, id=exam_id)
    action = request.POST.get('action', 'approve')
    commentaire = request.POST.get('commentaire', '')
    if action == 'approve':
        exam.approval_status = 'approved'
        exam.statut = 'publie'
        exam.approved_by = request.user
        exam.save(update_fields=['approval_status', 'statut', 'approved_by'])
        messages.success(request, f"Épreuve « {exam.titre} » approuvée.")
        _notifier_createur(exam.createur, f"Votre épreuve « {exam.titre} » a été approuvée.", 'success')
    else:
        exam.approval_status = 'rejected'
        exam.save(update_fields=['approval_status'])
        messages.warning(request, f"Épreuve « {exam.titre} » rejetée.")
        _notifier_createur(exam.createur, f"Votre épreuve « {exam.titre} » a été rejetée. {commentaire}", 'warning')
    return redirect('/gestion/approbations/?tab=examens')


@login_required
@require_http_methods(["POST"])
def admin_approuver_cours(request, cours_id):
    if not _admin_required(request):
        return redirect('dashboard')
    try:
        from cours.models import Course
        cours = get_object_or_404(Course, id=cours_id)
        action = request.POST.get('action', 'approve')
        if action == 'approve':
            cours.status = 'approved'
            cours.is_published = True
            cours.approved_by = request.user
            cours.save(update_fields=['status', 'is_published', 'approved_by'])
            messages.success(request, f"Cours « {cours.title} » approuvé.")
        else:
            cours.status = 'rejected'
            cours.save(update_fields=['status'])
            messages.warning(request, f"Cours « {cours.title} » rejeté.")
    except Exception as e:
        messages.error(request, f"Erreur : {e}")
    return redirect('/gestion/approbations/?tab=cours')


# ═══════════════════════════════════════════════════════════════
# ANNONCES GLOBALES
# ═══════════════════════════════════════════════════════════════

@login_required
def admin_annonces(request):
    if not _admin_required(request):
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard')

    from notifications.models import GlobalAnnouncement
    annonces = GlobalAnnouncement.objects.order_by('-created_at')
    return render(request, 'accounts/admin_annonces.html', {
        'annonces': annonces,
        'types_alerte': [
            ('info', 'Information'),
            ('warning', 'Avertissement'),
            ('success', 'Succès'),
            ('danger', 'Urgent'),
        ],
    })


@login_required
@require_http_methods(["POST"])
def admin_annonce_save(request, annonce_id=None):
    if not _admin_required(request):
        return redirect('dashboard')
    from notifications.models import GlobalAnnouncement
    titre = request.POST.get('titre', '').strip()
    message = request.POST.get('message', '').strip()
    type_alerte = request.POST.get('type_alerte', 'info')
    est_actif = request.POST.get('est_actif') == 'on'
    date_expiration = request.POST.get('date_expiration') or None

    if not titre or not message:
        messages.error(request, "Titre et message sont obligatoires.")
        return redirect('/gestion/annonces/')

    if annonce_id:
        obj = get_object_or_404(GlobalAnnouncement, id=annonce_id)
        obj.titre = titre; obj.message = message
        obj.type_alerte = type_alerte; obj.est_actif = est_actif
        obj.date_expiration = date_expiration
        obj.save()
        messages.success(request, "Annonce mise à jour.")
    else:
        GlobalAnnouncement.objects.create(
            titre=titre, message=message, type_alerte=type_alerte,
            est_actif=est_actif, date_expiration=date_expiration
        )
        messages.success(request, "Annonce créée et publiée.")
    return redirect('/gestion/annonces/')


@login_required
@require_http_methods(["POST"])
def admin_annonce_delete(request, annonce_id):
    if not _admin_required(request):
        return redirect('dashboard')
    from notifications.models import GlobalAnnouncement
    obj = get_object_or_404(GlobalAnnouncement, id=annonce_id)
    obj.delete()
    messages.success(request, "Annonce supprimée.")
    return redirect('/gestion/annonces/')


@login_required
@require_http_methods(["POST"])
def admin_annonce_toggle(request, annonce_id):
    if not _admin_required(request):
        return redirect('dashboard')
    from notifications.models import GlobalAnnouncement
    obj = get_object_or_404(GlobalAnnouncement, id=annonce_id)
    obj.est_actif = not obj.est_actif
    obj.save(update_fields=['est_actif'])
    etat = "activée" if obj.est_actif else "désactivée"
    messages.success(request, f"Annonce {etat}.")
    return redirect('/gestion/annonces/')


# ═══════════════════════════════════════════════════════════════
# BOURSES SCOLAIRES
# ═══════════════════════════════════════════════════════════════

@login_required
def admin_bourses(request):
    if not _admin_required(request):
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard')

    try:
        from payments.models import BourseScolaire
        tab = request.GET.get('tab', 'en_attente')
        statut_filtre = request.GET.get('statut', 'en_attente')

        bourses_qs = BourseScolaire.objects.select_related('eleve').order_by('-date_demande')
        if statut_filtre and statut_filtre != 'tous':
            bourses_qs = bourses_qs.filter(statut=statut_filtre)

        stats = {
            'en_attente': BourseScolaire.objects.filter(statut='en_attente').count(),
            'approuvee':  BourseScolaire.objects.filter(statut='approuvee').count(),
            'refusee':    BourseScolaire.objects.filter(statut='refusee').count(),
        }
    except Exception:
        bourses_qs = []
        stats = {'en_attente': 0, 'approuvee': 0, 'refusee': 0}

    statuts_list = [
        ('en_attente', 'En attente', 'linear-gradient(135deg,#f97316,#ea580c)'),
        ('approuvee',  'Approuvées', 'linear-gradient(135deg,#059669,#047857)'),
        ('refusee',    'Refusées',   'linear-gradient(135deg,#dc2626,#b91c1c)'),
        ('tous',       'Toutes',     'linear-gradient(135deg,#475569,#334155)'),
    ]
    return render(request, 'accounts/admin_bourses.html', {
        'bourses': bourses_qs,
        'stats': stats,
        'statut_filtre': statut_filtre,
        'statuts_list': statuts_list,
    })


@login_required
@require_http_methods(["POST"])
def admin_bourse_decision(request, bourse_id):
    if not _admin_required(request):
        return redirect('dashboard')
    try:
        from payments.models import BourseScolaire
        bourse = get_object_or_404(BourseScolaire, id=bourse_id)
        action = request.POST.get('action', '')
        decision = request.POST.get('decision_comite', '')
        if action == 'approuver':
            bourse.statut = 'approuvee'
            bourse.decision_comite = decision
            bourse.date_decision = timezone.now().date()
            bourse.save(update_fields=['statut', 'decision_comite', 'date_decision'])
            messages.success(request, f"Bourse de {bourse.eleve.get_full_name()} approuvée.")
        elif action == 'refuser':
            bourse.statut = 'refusee'
            bourse.decision_comite = decision
            bourse.date_decision = timezone.now().date()
            bourse.save(update_fields=['statut', 'decision_comite', 'date_decision'])
            messages.warning(request, f"Bourse de {bourse.eleve.get_full_name()} refusée.")
    except Exception as e:
        messages.error(request, f"Erreur : {e}")
    return redirect('/gestion/bourses/')


# ═══════════════════════════════════════════════════════════════
# GESTION UTILISATEURS (toggle actif, changer rôle)
# ═══════════════════════════════════════════════════════════════

@login_required
@require_http_methods(["POST"])
def admin_user_toggle_active(request, user_id):
    """Active ou désactive un compte utilisateur."""
    if not _admin_required(request):
        return redirect('dashboard')
    from accounts.models import User
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect('/accounts/admin/users/')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    etat = "activé" if user.is_active else "désactivé"
    messages.success(request, f"Compte de {user.get_full_name()} {etat}.")
    return redirect(request.META.get('HTTP_REFERER', '/accounts/admin/users/'))


@login_required
@require_http_methods(["POST"])
def admin_user_change_role(request, user_id):
    """Change le rôle d'un utilisateur."""
    if not _admin_required(request):
        return redirect('dashboard')
    from accounts.models import User
    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role', '')
    valid_roles = [r[0] for r in User.Role.choices]
    if new_role not in valid_roles:
        messages.error(request, "Rôle invalide.")
        return redirect('/accounts/admin/users/')
    if user == request.user and new_role != 'admin':
        messages.error(request, "Vous ne pouvez pas changer votre propre rôle.")
        return redirect('/accounts/admin/users/')
    user.role = new_role
    user.save(update_fields=['role'])
    messages.success(request, f"Rôle de {user.get_full_name()} changé en « {new_role} ».")
    return redirect(request.META.get('HTTP_REFERER', '/accounts/admin/users/'))


# ═══════════════════════════════════════════════════════════════
# HELPER INTERNE
# ═══════════════════════════════════════════════════════════════

def _notifier_createur(user, message, type_notif='info'):
    try:
        from notifications.models import Notification
        Notification.objects.create(
            recipient=user,
            title="Décision sur votre contenu",
            message=message,
            type=type_notif,
        )
    except Exception:
        pass
