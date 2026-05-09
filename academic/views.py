"""
Vues pour la gestion académique
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from .models import Promotion, Inscription, MatiereClasse, Evaluation, Note, BulletinNotes, Discipline


@login_required
def promotion_list(request):
    """Liste de toutes les promotions"""
    query = request.GET.get('q', '')
    promotions = Promotion.objects.filter(is_active=True)
    
    if query:
        promotions = promotions.filter(
            Q(nom__icontains=query) |
            Q(code__icontains=query)
        )
    
    context = {
        'promotions': promotions,
        'query': query,
    }
    return render(request, 'academic/promotion_list.html', context)


@login_required
def promotion_create(request):
    """Création d'une nouvelle promotion"""
    if request.method == 'POST':
        # Logique de création de promotion
        messages.success(request, "La promotion a été créée avec succès.")
        return redirect('academic:promotion_list')
    
    return render(request, 'academic/promotion_form.html', {'title': 'Créer une promotion'})


@login_required
def promotion_detail(request, promotion_id):
    """Détail d'une promotion"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    inscriptions = promotion.inscriptions.select_related('eleve', 'classe')
    
    context = {
        'promotion': promotion,
        'inscriptions': inscriptions,
    }
    return render(request, 'academic/promotion_detail.html', context)


@login_required
def inscription_list(request):
    """Liste de toutes les inscriptions"""
    query = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    
    inscriptions = Inscription.objects.select_related('eleve', 'classe', 'annee_scolaire')
    
    if query:
        inscriptions = inscriptions.filter(
            Q(eleve__last_name__icontains=query) |
            Q(eleve__first_name__icontains=query) |
            Q(numero_inscription__icontains=query)
        )
    
    if statut:
        inscriptions = inscriptions.filter(statut=statut)
    
    context = {
        'inscriptions': inscriptions,
        'query': query,
        'statut': statut,
    }
    return render(request, 'academic/inscription_list.html', context)


@login_required
def inscription_create(request):
    """Création d'une nouvelle inscription"""
    if request.method == 'POST':
        # Logique de création d'inscription
        messages.success(request, "L'inscription a été créée avec succès.")
        return redirect('academic:inscription_list')
    
    return render(request, 'academic/inscription_form.html', {'title': 'Nouvelle inscription'})


@login_required
def inscription_detail(request, inscription_id):
    """Détail d'une inscription"""
    inscription = get_object_or_404(Inscription, id=inscription_id)
    notes = inscription.notes.select_related('evaluation')
    bulletins = inscription.bulletins.all()
    
    context = {
        'inscription': inscription,
        'notes': notes,
        'bulletins': bulletins,
    }
    return render(request, 'academic/inscription_detail.html', context)


@login_required
def inscription_update(request, inscription_id):
    """Modification d'une inscription"""
    inscription = get_object_or_404(Inscription, id=inscription_id)
    
    if request.method == 'POST':
        # Logique de modification
        messages.success(request, "L'inscription a été mise à jour.")
        return redirect('academic:inscription_detail', inscription_id=inscription.id)
    
    return render(request, 'academic/inscription_form.html', {
        'title': 'Modifier l\'inscription',
        'inscription': inscription
    })


@login_required
def matiere_classe_list(request, classe_id):
    """Liste des matières d'une classe"""
    from schools.models import Classe
    classe = get_object_or_404(Classe, id=classe_id)
    matieres = classe.matieres.filter(is_active=True).select_related('matiere', 'professeur')
    
    context = {
        'classe': classe,
        'matieres': matieres,
    }
    return render(request, 'academic/matiere_classe_list.html', context)


@login_required
def matiere_classe_create(request, classe_id):
    """Ajout d'une matière à une classe"""
    from schools.models import Classe
    classe = get_object_or_404(Classe, id=classe_id)
    
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "La matière a été ajoutée à la classe.")
        return redirect('academic:matiere_classe_list', classe_id=classe.id)
    
    return render(request, 'academic/matiere_classe_form.html', {
        'title': 'Ajouter une matière',
        'classe': classe
    })


@login_required
def evaluation_list(request):
    """Liste de toutes les évaluations"""
    evaluations = Evaluation.objects.select_related('classe', 'professeur', 'matiere_classe__matiere')
    
    # Filtres
    classe_id = request.GET.get('classe')
    type_eval = request.GET.get('type')
    
    if classe_id:
        evaluations = evaluations.filter(classe_id=classe_id)
    if type_eval:
        evaluations = evaluations.filter(type_evaluation=type_eval)
    
    context = {
        'evaluations': evaluations,
    }
    return render(request, 'academic/evaluation_list.html', context)


@login_required
def evaluation_create(request):
    """Création d'une nouvelle évaluation"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "L'évaluation a été créée.")
        return redirect('academic:evaluation_list')
    
    return render(request, 'academic/evaluation_form.html', {'title': 'Créer une évaluation'})


@login_required
def evaluation_detail(request, evaluation_id):
    """Détail d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    notes = evaluation.notes.select_related('eleve')
    
    # Statistiques
    if notes.exists():
        moyenne = notes.aggregate(Avg('note'))['note__avg']
        max_note = notes.aggregate(models.Max('note'))['note__max']
        min_note = notes.aggregate(models.Min('note'))['note__min']
    else:
        moyenne = max_note = min_note = None
    
    context = {
        'evaluation': evaluation,
        'notes': notes,
        'moyenne': moyenne,
        'max_note': max_note,
        'min_note': min_note,
    }
    return render(request, 'academic/evaluation_detail.html', context)


@login_required
def evaluation_notes(request, evaluation_id):
    """Gestion des notes d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    
    if request.method == 'POST':
        # Logique de saisie des notes
        messages.success(request, "Les notes ont été enregistrées.")
        return redirect('academic:evaluation_detail', evaluation_id=evaluation.id)
    
    context = {
        'evaluation': evaluation,
    }
    return render(request, 'academic/evaluation_notes_form.html', context)


@login_required
def bulletin_list(request):
    """Liste de tous les bulletins"""
    bulletins = BulletinNotes.objects.select_related('eleve', 'classe', 'annee_scolaire')
    
    # Filtres
    periode = request.GET.get('periode')
    eleve_id = request.GET.get('eleve')
    
    if periode:
        bulletins = bulletins.filter(periode__icontains=periode)
    if eleve_id:
        bulletins = bulletins.filter(eleve_id=eleve_id)
    
    context = {
        'bulletins': bulletins,
    }
    return render(request, 'academic/bulletin_list.html', context)


@login_required
def bulletin_detail(request, bulletin_id):
    """Détail d'un bulletin"""
    bulletin = get_object_or_404(BulletinNotes, id=bulletin_id)
    inscription = bulletin.inscription
    
    context = {
        'bulletin': bulletin,
        'inscription': inscription,
    }
    return render(request, 'academic/bulletin_detail.html', context)


@login_required
def bulletin_generate(request):
    """Génération de bulletins"""
    if request.method == 'POST':
        # Logique de génération
        messages.success(request, "Les bulletins ont été générés.")
        return redirect('academic:bulletin_list')
    
    return render(request, 'academic/bulletin_generate_form.html', {'title': 'Générer des bulletins'})


@login_required
def discipline_list(request):
    """Liste de tous les incidents disciplinaires"""
    disciplines = Discipline.objects.select_related('eleve', 'classe')
    
    # Filtres
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    type_sanction = request.GET.get('type')
    
    if date_debut:
        disciplines = disciplines.filter(date_incident__gte=date_debut)
    if date_fin:
        disciplines = disciplines.filter(date_incident__lte=date_fin)
    if type_sanction:
        disciplines = disciplines.filter(type_sanction=type_sanction)
    
    context = {
        'disciplines': disciplines,
    }
    return render(request, 'academic/discipline_list.html', context)


@login_required
def discipline_create(request):
    """Création d'un incident disciplinaire"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "L'incident disciplinaire a été enregistré.")
        return redirect('academic:discipline_list')
    
    return render(request, 'academic/discipline_form.html', {'title': 'Enregistrer un incident'})
