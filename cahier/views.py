"""
Vues pour le cahier de texte
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SeanceCours, Devoir, Lecon, RenduDevoir, Progression


@login_required
def seance_list(request):
    """Liste de toutes les seances de cours"""
    query = request.GET.get('q', '')
    classe_id = request.GET.get('classe')
    
    seances = SeanceCours.objects.select_related('classe', 'matiere', 'professeur')
    
    if query:
        seances = seances.filter(titre__icontains=query)
    
    if classe_id:
        seances = seances.filter(classe_id=classe_id)
    
    context = {
        'seances': seances,
        'query': query,
    }
    return render(request, 'cahier/seance_list.html', context)


@login_required
def seance_create(request):
    """Creation d'une nouvelle seance"""
    if request.method == 'POST':
        messages.success(request, "La seance a ete cree.")
        return redirect('cahier:seance_list')
    
    return render(request, 'cahier/seance_form.html', {'title': 'Creer une seance'})


@login_required
def seance_detail(request, seance_id):
    """Detail d'une seance"""
    seance = get_object_or_404(SeanceCours, id=seance_id)
    
    context = {
        'seance': seance,
    }
    return render(request, 'cahier/seance_detail.html', context)


@login_required
def devoir_list(request):
    """Liste de tous les devoirs"""
    query = request.GET.get('q', '')
    type_devoir = request.GET.get('type')
    
    devoirs = Devoir.objects.select_related('classe', 'matiere', 'professeur')
    
    if query:
        devoirs = devoirs.filter(titre__icontains=query)
    
    if type_devoir:
        devoirs = devoirs.filter(type_devoir=type_devoir)
    
    context = {
        'devoirs': devoirs,
        'query': query,
    }
    return render(request, 'cahier/devoir_list.html', context)


@login_required
def devoir_create(request):
    """Creation d'un nouveau devoir"""
    if request.method == 'POST':
        messages.success(request, "Le devoir a ete cree.")
        return redirect('cahier:devoir_list')
    
    return render(request, 'cahier/devoir_form.html', {'title': 'Creer un devoir'})


@login_required
def devoir_detail(request, devoir_id):
    """Detail d'un devoir"""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    rendus = RenduDevoir.objects.filter(devoir=devoir).select_related('eleve')
    
    context = {
        'devoir': devoir,
        'rendus': rendus,
    }
    return render(request, 'cahier/devoir_detail.html', context)


@login_required
def rendu_list(request, devoir_id):
    """Liste des rendus d'un devoir"""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    rendus = RenduDevoir.objects.filter(devoir=devoir).select_related('eleve')
    
    context = {
        'devoir': devoir,
        'rendus': rendus,
    }
    return render(request, 'cahier/rendu_list.html', context)


@login_required
def lecon_list(request):
    """Liste de toutes les lecons"""
    query = request.GET.get('q', '')
    matiere_id = request.GET.get('matiere')
    
    lecons = Lecon.objects.select_related('classe', 'matiere')
    
    if query:
        lecons = lecons.filter(titre__icontains=query)
    
    if matiere_id:
        lecons = lecons.filter(matiere_id=matiere_id)
    
    context = {
        'lecons': lecons,
        'query': query,
    }
    return render(request, 'cahier/lecon_list.html', context)


@login_required
def lecon_create(request):
    """Creation d'une nouvelle lecon"""
    if request.method == 'POST':
        messages.success(request, "La lecon a ete cree.")
        return redirect('cahier:lecon_list')
    
    return render(request, 'cahier/lecon_form.html', {'title': 'Creer une lecon'})


@login_required
def lecon_detail(request, lecon_id):
    """Detail d'une lecon"""
    lecon = get_object_or_404(Lecon, id=lecon_id)
    
    context = {
        'lecon': lecon,
    }
    return render(request, 'cahier/lecon_detail.html', context)


@login_required
def progression_list(request):
    """Liste de toutes les progressions"""
    progressions = Progression.objects.select_related('classe', 'matiere')
    
    context = {
        'progressions': progressions,
    }
    return render(request, 'cahier/progression_list.html', context)


@login_required
def progression_detail(request, progression_id):
    """Detail d'une progression"""
    progression = get_object_or_404(Progression, id=progression_id)
    
    context = {
        'progression': progression,
    }
    return render(request, 'cahier/progression_detail.html', context)
