"""
Vues pour la gestion des présences
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import Presence, Retard, Absence, RapportPresence


@login_required
def presence_list(request):
    """Liste de toutes les présences"""
    query = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    presences = Presence.objects.select_related('eleve', 'classe')
    
    if query:
        presences = presences.filter(
            Q(eleve__last_name__icontains=query) |
            Q(eleve__first_name__icontains=query)
        )
    
    if statut:
        presences = presences.filter(statut=statut)
    
    if date_debut:
        presences = presences.filter(date__gte=date_debut)
    if date_fin:
        presences = presences.filter(date__lte=date_fin)
    
    context = {
        'presences': presences,
        'query': query,
    }
    return render(request, 'attendance/presence_list.html', context)


@login_required
def presence_create(request):
    """Création d'une nouvelle présence"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "La présence a été enregistrée.")
        return redirect('attendance:presence_list')
    
    return render(request, 'attendance/presence_form.html', {'title': 'Enregistrer une présence'})


@login_required
def presence_detail(request, presence_id):
    """Détail d'une présence"""
    presence = get_object_or_404(Presence, id=presence_id)
    
    context = {
        'presence': presence,
    }
    return render(request, 'attendance/presence_detail.html', context)


@login_required
def absence_list(request):
    """Liste de toutes les absences"""
    query = request.GET.get('q', '')
    type_absence = request.GET.get('type', '')
    statut = request.GET.get('statut', '')
    
    absences = Absence.objects.select_related('eleve', 'classe')
    
    if query:
        absences = absences.filter(
            Q(eleve__last_name__icontains=query) |
            Q(eleve__first_name__icontains=query) |
            Q(motif__icontains=query)
        )
    
    if type_absence:
        absences = absences.filter(type_absence=type_absence)
    
    if statut:
        absences = absences.filter(statut=statut)
    
    context = {
        'absences': absences,
        'query': query,
    }
    return render(request, 'attendance/absence_list.html', context)


@login_required
def absence_create(request):
    """Création d'une nouvelle absence"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "L'absence a été enregistrée.")
        return redirect('attendance:absence_list')
    
    return render(request, 'attendance/absence_form.html', {'title': 'Enregistrer une absence'})


@login_required
def absence_detail(request, absence_id):
    """Détail d'une absence"""
    absence = get_object_or_404(Absence, id=absence_id)
    
    context = {
        'absence': absence,
    }
    return render(request, 'attendance/absence_detail.html', context)


@login_required
def retard_list(request):
    """Liste de tous les retards"""
    query = request.GET.get('q', '')
    
    retards = Retard.objects.select_related('eleve', 'classe')
    
    if query:
        retards = retards.filter(
            Q(eleve__last_name__icontains=query) |
            Q(eleve__first_name__icontains=query)
        )
    
    context = {
        'retards': retards,
        'query': query,
    }
    return render(request, 'attendance/retard_list.html', context)


@login_required
def retard_create(request):
    """Création d'un nouveau retard"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "Le retard a été enregistré.")
        return redirect('attendance:retard_list')
    
    return render(request, 'attendance/retard_form.html', {'title': 'Enregistrer un retard'})


@login_required
def rapport_list(request):
    """Liste de tous les rapports de présence"""
    rapports = RapportPresence.objects.select_related('eleve', 'classe')
    
    context = {
        'rapports': rapports,
    }
    return render(request, 'attendance/rapport_list.html', context)


@login_required
def rapport_generate(request):
    """Génération de rapports de présence"""
    if request.method == 'POST':
        # Logique de génération
        messages.success(request, "Les rapports ont été générés.")
        return redirect('attendance:rapport_list')
    
    return render(request, 'attendance/rapport_generate_form.html', {'title': 'Générer des rapports'})


@login_required
def calendrier_presence(request):
    """Vue du calendrier de présence"""
    today = datetime.now()
    debut_mois = today.replace(day=1)
    fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    presences = Presence.objects.filter(
        date__range=[debut_mois, fin_mois]
    ).select_related('eleve', 'classe')
    
    context = {
        'presences': presences,
        'today': today,
        'debut_mois': debut_mois,
        'fin_mois': fin_mois,
    }
    return render(request, 'attendance/calendrier.html', context)
