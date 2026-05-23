from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from exams.models import Exam
from notifications.models import Notification
from core.models import Organisation
from accounts.models import MembreOrganisation


def promo_video_view(request):
    """Page promotionnelle avec vidéos auto-play avant l'accès à l'application."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'promo.html', {'is_promo_page': True})


def home_view(request):
    return render(request, 'welcome.html', {'is_home': True})


@login_required
def organisation_create(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        code = request.POST.get('code', '').strip()
        pays = request.POST.get('pays', 'Bénin').strip()
        if nom and code:
            org = Organisation.objects.create(nom=nom, code=code, pays=pays)
            MembreOrganisation.objects.create(
                user=request.user,
                organisation=org,
                role='admin',
                est_principal=not MembreOrganisation.objects.filter(user=request.user, est_principal=True).exists(),
            )
            messages.success(request, f'Organisation « {org.nom} » créée avec succès.')
            return redirect('core:organisation_detail', pk=org.pk)
    return render(request, 'core/organisation_form.html', {})


@login_required
def organisation_detail(request, pk):
    org = get_object_or_404(Organisation, pk=pk)
    membres = MembreOrganisation.objects.filter(organisation=org).select_related('user')
    return render(request, 'core/organisation_detail.html', {'organisation': org, 'membres': membres})


@login_required
def organisation_membres(request, pk):
    org = get_object_or_404(Organisation, pk=pk)
    membres = MembreOrganisation.objects.filter(organisation=org).select_related('user')
    return render(request, 'core/organisation_membres.html', {'organisation': org, 'membres': membres})


@login_required
def admin_dashboard_view(request):
    if not request.user.is_superuser and request.user.role != 'admin':
        return redirect('home')

    pending_exams = Exam.objects.filter(approval_status='pending')
    notifications = Notification.objects.all()[:10]

    return render(request, 'admin/dashboard.html', {
        'pending_exams': pending_exams,
        'pending_count': pending_exams.count(),
        'notifications': notifications,
        'user': request.user,
    })
