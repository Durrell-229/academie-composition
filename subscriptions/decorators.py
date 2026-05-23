from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from functools import wraps


def subscription_required(level='PRO'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Mode gratuit : si l'établissement n'a pas configuré FedaPay → accès libre
            try:
                from payments.utils import paiements_actifs
                etablissement = getattr(request.user, 'etablissement', None)
                if etablissement and not paiements_actifs(etablissement):
                    return view_func(request, *args, **kwargs)
            except Exception:
                pass

            # Vérifier si l'utilisateur a un abonnement actif du niveau requis
            sub = getattr(request.user, 'subscription', None)

            if not sub or sub.is_expired or (sub.plan.level == 'FREE' and level != 'FREE'):
                messages.warning(request, f"Cette fonctionnalité nécessite un abonnement {level}. Veuillez mettre à jour votre plan.")
                return redirect('payments:abonnements')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def qcm_pro_required(view_func):
    """
    Vérifie que l'élève a un abonnement actif (AbonnementEleve) avant d'accéder aux QCM.
    Redirige vers la page des abonnements si non abonné.
    Les profs et admins passent sans vérification.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        role = getattr(request.user, 'role', '')
        if role in ('professeur', 'admin', 'superadmin', 'directeur'):
            return view_func(request, *args, **kwargs)

        # Mode gratuit : paiements non configurés → accès libre
        try:
            from payments.utils import paiements_actifs
            etablissement = getattr(request.user, 'etablissement', None)
            if etablissement and not paiements_actifs(etablissement):
                return view_func(request, *args, **kwargs)
        except Exception:
            pass

        # Vérifier AbonnementEleve (modèle principal d'abonnement scolaire)
        try:
            from payments.models import AbonnementEleve
            abonnement = AbonnementEleve.objects.filter(
                eleve=request.user,
                statut=AbonnementEleve.StatutAbonnement.ACTIF,
                date_fin__gt=timezone.now(),
            ).exists()
            if abonnement:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass

        # Aucun abonnement actif → paywall
        return redirect('qcm_paywall')

    return _wrapped_view


def prof_required(view_func):
    """Réserve la vue aux professeurs, directeurs et admins."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = getattr(request.user, 'role', '')
        if role not in ('professeur', 'admin', 'superadmin', 'directeur'):
            messages.error(request, "Accès réservé aux professeurs.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
