"""
Vues pour la gestion des emplois du temps
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta
from .models import EmploiDuTemps, CreneauHoraire, EvenementScolaire, DisponibiliteProfesseur, Salle


@login_required
def emploi_du_temps_list(request):
    """Liste de tous les emplois du temps"""
    query = request.GET.get('q', '')
    type_cible = request.GET.get('type', '')
    
    emplois = EmploiDuTemps.objects.filter(is_actif=True)
    
    if query:
        emplois = emplois.filter(
            Q(nom__icontains=query) |
            Q(classe__nom__icontains=query)
        )
    
    if type_cible:
        emplois = emplois.filter(type_cible=type_cible)
    
    context = {
        'emplois': emplois,
        'query': query,
    }
    return render(request, 'schedule/emploi_du_temps_list.html', context)


@login_required
def emploi_du_temps_create(request):
    """Création d'un nouvel emploi du temps"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "L'emploi du temps a été créé.")
        return redirect('schedule:emploi_du_temps_list')
    
    return render(request, 'schedule/emploi_du_temps_form.html', {'title': 'Créer un emploi du temps'})


@login_required
def emploi_du_temps_detail(request, emploi_id):
    """Détail d'un emploi du temps"""
    emploi = get_object_or_404(EmploiDuTemps, id=emploi_id)
    creneaux = emploi.creneaux.filter(is_actif=True).select_related('matiere', 'professeur', 'classe')
    
    # Organiser les créneaux par jour
    creneaux_par_jour = {}
    for jour in EmploiDuTemps.JourSemaine.choices:
        creneaux_par_jour[jour[0]] = creneaux.filter(jour=jour[0]).order_by('heure_debut')
    
    context = {
        'emploi': emploi,
        'creneaux': creneaux,
        'creneaux_par_jour': creneaux_par_jour,
    }
    return render(request, 'schedule/emploi_du_temps_detail.html', context)


@login_required
def emploi_du_temps_edit(request, emploi_id):
    """Modification d'un emploi du temps"""
    emploi = get_object_or_404(EmploiDuTemps, id=emploi_id)
    
    if request.method == 'POST':
        # Logique de modification
        messages.success(request, "L'emploi du temps a été mis à jour.")
        return redirect('schedule:emploi_du_temps_detail', emploi_id=emploi.id)
    
    return render(request, 'schedule/emploi_du_temps_form.html', {
        'title': 'Modifier l\'emploi du temps',
        'emploi': emploi
    })


@login_required
def creneau_list(request, emploi_id):
    """Liste des créneaux d'un emploi du temps"""
    emploi = get_object_or_404(EmploiDuTemps, id=emploi_id)
    creneaux = emploi.creneaux.filter(is_actif=True).select_related('matiere', 'professeur', 'classe')
    
    context = {
        'emploi': emploi,
        'creneaux': creneaux,
    }
    return render(request, 'schedule/creneau_list.html', context)


@login_required
def evenement_list(request):
    """Liste de tous les événements scolaires"""
    query = request.GET.get('q', '')
    type_evenement = request.GET.get('type', '')
    
    evenements = EvenementScolaire.objects.filter(is_annule=False)
    
    if query:
        evenements = evenements.filter(
            Q(titre__icontains=query) |
            Q(description__icontains=query)
        )
    
    if type_evenement:
        evenements = evenements.filter(type_evenement=type_evenement)
    
    context = {
        'evenements': evenements,
        'query': query,
    }
    return render(request, 'schedule/evenement_list.html', context)


@login_required
def evenement_create(request):
    """Création d'un nouvel événement"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "L'événement a été créé.")
        return redirect('schedule:evenement_list')
    
    return render(request, 'schedule/evenement_form.html', {'title': 'Créer un événement'})


@login_required
def evenement_detail(request, evenement_id):
    """Détail d'un événement"""
    evenement = get_object_or_404(EvenementScolaire, id=evenement_id)
    
    context = {
        'evenement': evenement,
    }
    return render(request, 'schedule/evenement_detail.html', context)


@login_required
def calendrier_view(request):
    """Vue du calendrier interactif"""
    # Récupérer les événements du mois en cours
    today = datetime.now()
    debut_mois = today.replace(day=1)
    fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    evenements = EvenementScolaire.objects.filter(
        date_debut__range=[debut_mois, fin_mois],
        is_annule=False
    ).select_related('etablissement')
    
    context = {
        'evenements': evenements,
        'today': today,
        'debut_mois': debut_mois,
        'fin_mois': fin_mois,
    }
    return render(request, 'schedule/calendrier.html', context)


@login_required
def salle_list(request):
    """Liste de toutes les salles"""
    query = request.GET.get('q', '')
    type_salle = request.GET.get('type', '')
    
    salles = Salle.objects.filter(is_disponible=True)
    
    if query:
        salles = salles.filter(
            Q(nom__icontains=query) |
            Q(code__icontains=query) |
            Q(batiment__icontains=query)
        )
    
    if type_salle:
        salles = salles.filter(type_salle=type_salle)
    
    context = {
        'salles': salles,
        'query': query,
    }
    return render(request, 'schedule/salle_list.html', context)


@login_required
def salle_create(request):
    """Création d'une nouvelle salle"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "La salle a été créée.")
        return redirect('schedule:salle_list')
    
    return render(request, 'schedule/salle_form.html', {'title': 'Créer une salle'})


@login_required
def disponibilite_list(request):
    """Liste des disponibilités professeurs"""
    query = request.GET.get('q', '')
    
    disponibilites = DisponibiliteProfesseur.objects.filter(is_actif=True).select_related('professeur')
    
    if query:
        disponibilites = disponibilites.filter(
            Q(professeur__last_name__icontains=query) |
            Q(professeur__first_name__icontains=query)
        )
    
    context = {
        'disponibilites': disponibilites,
        'query': query,
    }
    return render(request, 'schedule/disponibilite_list.html', context)
