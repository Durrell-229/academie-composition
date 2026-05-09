"""
Vues pour la gestion multi-établissements
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .models import Etablissement, Campus, NiveauScolaire, Classe, AnneeScolaire, ConfigurationEtablissement
from .forms import EtablissementForm, CampusForm, ClasseForm, ConfigurationEtablissementForm


@login_required
def etablissement_list(request):
    """Liste de tous les établissements"""
    query = request.GET.get('q', '')
    etablissements = Etablissement.objects.filter(is_active=True)
    
    if query:
        etablissements = etablissements.filter(
            Q(nom__icontains=query) |
            Q(code__icontains=query) |
            Q(ville__icontains=query)
        )
    
    # Statistiques
    stats = {
        'total': etablissements.count(),
        'primaire': etablissements.filter(type_etablissement='primaire').count(),
        'college': etablissements.filter(type_etablissement='college').count(),
        'lycee': etablissements.filter(type_etablissement='lycee').count(),
        'universite': etablissements.filter(type_etablissement='universite').count(),
    }
    
    context = {
        'etablissements': etablissements,
        'stats': stats,
        'query': query,
    }
    return render(request, 'schools/etablissement_list.html', context)


@login_required
def etablissement_create(request):
    """Création d'un nouvel établissement"""
    if request.method == 'POST':
        form = EtablissementForm(request.POST, request.FILES)
        if form.is_valid():
            etablissement = form.save(commit=False)
            etablissement.save()
            
            # Créer la configuration par défaut
            ConfigurationEtablissement.objects.create(etablissement=etablissement)
            
            messages.success(request, f"L'établissement {etablissement.nom} a été créé avec succès.")
            return redirect('schools:etablissement_detail', etablissement_id=etablissement.id)
    else:
        form = EtablissementForm()
    
    return render(request, 'schools/etablissement_form.html', {'form': form, 'title': 'Créer un établissement'})


@login_required
def etablissement_detail(request, etablissement_id):
    """Détail d'un établissement"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    campus_list = etablissement.campus.filter(is_active=True)
    classes_list = etablissement.classes.filter(is_active=True)
    niveaux_list = etablissement.niveaux.filter(is_active=True)
    
    # Statistiques
    stats = {
        'nombre_campus': campus_list.count(),
        'nombre_classes': classes_list.count(),
        'nombre_niveaux': niveaux_list.count(),
        'total_eleves': etablissement.nombre_eleves,
        'total_professeurs': etablissement.nombre_professeurs,
        'taux_occupation': etablissement.taux_occupation,
    }
    
    context = {
        'etablissement': etablissement,
        'campus_list': campus_list,
        'classes_list': classes_list,
        'niveaux_list': niveaux_list,
        'stats': stats,
    }
    return render(request, 'schools/etablissement_detail.html', context)


@login_required
def etablissement_update(request, etablissement_id):
    """Modification d'un établissement"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    
    if request.method == 'POST':
        form = EtablissementForm(request.POST, request.FILES, instance=etablissement)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'établissement {etablissement.nom} a été mis à jour.")
            return redirect('schools:etablissement_detail', etablissement_id=etablissement.id)
    else:
        form = EtablissementForm(instance=etablissement)
    
    return render(request, 'schools/etablissement_form.html', {
        'form': form,
        'title': f'Modifier {etablissement.nom}',
        'etablissement': etablissement
    })


@login_required
def etablissement_delete(request, etablissement_id):
    """Suppression d'un établissement"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    
    if request.method == 'POST':
        etablissement.is_active = False
        etablissement.save()
        messages.success(request, f"L'établissement {etablissement.nom} a été désactivé.")
        return redirect('schools:etablissement_list')
    
    return render(request, 'schools/etablissement_confirm_delete.html', {'etablissement': etablissement})


@login_required
def campus_list(request, etablissement_id):
    """Liste des campus d'un établissement"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    campus_list = etablissement.campus.filter(is_active=True)
    
    context = {
        'etablissement': etablissement,
        'campus_list': campus_list,
    }
    return render(request, 'schools/campus_list.html', context)


@login_required
def campus_create(request, etablissement_id):
    """Création d'un nouveau campus"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    
    if request.method == 'POST':
        form = CampusForm(request.POST)
        if form.is_valid():
            campus = form.save(commit=False)
            campus.etablissement = etablissement
            campus.save()
            messages.success(request, f"Le campus {campus.nom} a été créé.")
            return redirect('schools:campus_list', etablissement_id=etablissement.id)
    else:
        form = CampusForm()
    
    return render(request, 'schools/campus_form.html', {
        'form': form,
        'title': 'Créer un campus',
        'etablissement': etablissement
    })


@login_required
def campus_detail(request, etablissement_id, campus_id):
    """Détail d'un campus"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    campus = get_object_or_404(Campus, id=campus_id, etablissement=etablissement)
    classes_list = campus.classes.filter(is_active=True)
    
    context = {
        'etablissement': etablissement,
        'campus': campus,
        'classes_list': classes_list,
    }
    return render(request, 'schools/campus_detail.html', context)


@login_required
def classe_list(request, etablissement_id):
    """Liste des classes d'un établissement"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    classes_list = etablissement.classes.filter(is_active=True).select_related('niveau', 'professeur_principal')
    
    # Filtrage par niveau
    niveau_id = request.GET.get('niveau')
    if niveau_id:
        classes_list = classes_list.filter(niveau_id=niveau_id)
    
    context = {
        'etablissement': etablissement,
        'classes_list': classes_list,
        'niveaux': etablissement.niveaux.filter(is_active=True),
    }
    return render(request, 'schools/classe_list.html', context)


@login_required
def classe_create(request, etablissement_id):
    """Création d'une nouvelle classe"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    
    if request.method == 'POST':
        form = ClasseForm(request.POST, etablissement=etablissement)
        if form.is_valid():
            classe = form.save()
            messages.success(request, f"La classe {classe.nom} a été créée.")
            return redirect('schools:classe_list', etablissement_id=etablissement.id)
    else:
        form = ClasseForm(etablissement=etablissement)
    
    return render(request, 'schools/classe_form.html', {
        'form': form,
        'title': 'Créer une classe',
        'etablissement': etablissement
    })


@login_required
def classe_detail(request, etablissement_id, classe_id):
    """Détail d'une classe"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    classe = get_object_or_404(Classe, id=classe_id, etablissement=etablissement)
    
    # Élèves de la classe
    from accounts.models import User
    eleves = User.objects.filter(classe=classe.nom, role='eleve')
    
    context = {
        'etablissement': etablissement,
        'classe': classe,
        'eleves': eleves,
    }
    return render(request, 'schools/classe_detail.html', context)


@login_required
def configuration_edit(request, etablissement_id):
    """Modification de la configuration d'un établissement"""
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    configuration, created = ConfigurationEtablissement.objects.get_or_create(etablissement=etablissement)
    
    if request.method == 'POST':
        form = ConfigurationEtablissementForm(request.POST, instance=configuration)
        if form.is_valid():
            form.save()
            messages.success(request, "La configuration a été mise à jour.")
            return redirect('schools:etablissement_detail', etablissement_id=etablissement.id)
    else:
        form = ConfigurationEtablissementForm(instance=configuration)
    
    return render(request, 'schools/configuration_form.html', {
        'form': form,
        'title': f'Configuration - {etablissement.nom}',
        'etablissement': etablissement
    })
