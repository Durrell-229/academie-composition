"""
Vues pour la gestion académique
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, Max, Min
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
    from schools.models import Etablissement, NiveauScolaire
    if request.method == 'POST':
        try:
            etablissement = get_object_or_404(Etablissement, id=request.POST['etablissement'])
            niveau_entree = get_object_or_404(NiveauScolaire, id=request.POST['niveau_entree'])
            niveau_sortie = get_object_or_404(NiveauScolaire, id=request.POST['niveau_sortie'])
            Promotion.objects.create(
                etablissement=etablissement,
                nom=request.POST['nom'],
                code=request.POST['code'],
                annee_entree=request.POST['annee_entree'],
                annee_sortie=request.POST['annee_sortie'],
                niveau_entree=niveau_entree,
                niveau_sortie=niveau_sortie,
                description=request.POST.get('description', ''),
            )
            messages.success(request, "La promotion a été créée avec succès.")
            return redirect('academic:promotion_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {e}")
    context = {
        'title': 'Créer une promotion',
        'etablissements': Etablissement.objects.filter(is_active=True),
        'niveaux': NiveauScolaire.objects.all(),
    }
    return render(request, 'academic/promotion_form.html', context)


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
    from schools.models import Classe as SchoolsClasse, AnneeScolaire
    if request.method == 'POST':
        try:
            from accounts.models import User as AuthUser
            eleve = get_object_or_404(AuthUser, id=request.POST['eleve'])
            classe = get_object_or_404(SchoolsClasse, id=request.POST['classe'])
            annee_scolaire = get_object_or_404(AnneeScolaire, id=request.POST['annee_scolaire'])
            promotion = None
            if request.POST.get('promotion'):
                promotion = Promotion.objects.filter(id=request.POST['promotion']).first()
            inscription = Inscription(
                eleve=eleve,
                classe=classe,
                annee_scolaire=annee_scolaire,
                promotion=promotion,
                statut=request.POST.get('statut', Inscription.StatutInscription.INSCRITE),
            )
            inscription.save()
            messages.success(request, "L'inscription a été créée avec succès.")
            return redirect('academic:inscription_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {e}")
    from schools.models import Classe as SchoolsClasse, AnneeScolaire
    from accounts.models import User as AuthUser
    context = {
        'title': 'Nouvelle inscription',
        'eleves': AuthUser.objects.filter(role='eleve').order_by('last_name'),
        'classes': SchoolsClasse.objects.filter(is_active=True),
        'annees': AnneeScolaire.objects.filter(est_active=True),
        'promotions': Promotion.objects.filter(is_active=True),
        'statuts': Inscription.StatutInscription.choices,
    }
    return render(request, 'academic/inscription_form.html', context)


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
        try:
            inscription.statut = request.POST.get('statut', inscription.statut)
            inscription.frais_inscription_payes = 'frais_inscription_payes' in request.POST
            inscription.frais_scolarite_payes = 'frais_scolarite_payes' in request.POST
            inscription.est_boursier = 'est_boursier' in request.POST
            inscription.dossier_complet = 'dossier_complet' in request.POST
            solde_du = request.POST.get('solde_du', '').strip()
            if solde_du:
                inscription.solde_du = solde_du
            inscription.type_bourse = request.POST.get('type_bourse', inscription.type_bourse)
            inscription.documents_manquants = request.POST.get('documents_manquants', inscription.documents_manquants)
            inscription.appreciation = request.POST.get('appreciation', inscription.appreciation)
            inscription.observations = request.POST.get('observations', inscription.observations)
            inscription.save()
            messages.success(request, "L'inscription a été mise à jour.")
            return redirect('academic:inscription_detail', inscription_id=inscription.id)
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour : {e}")

    from schools.models import AnneeScolaire
    context = {
        'title': "Modifier l'inscription",
        'inscription': inscription,
        'statuts': Inscription.StatutInscription.choices,
    }
    return render(request, 'academic/inscription_form.html', context)


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
    from schools.models import Classe as SchoolsClasse
    classe = get_object_or_404(SchoolsClasse, id=classe_id)
    if request.method == 'POST':
        try:
            from core.models import Matiere
            from accounts.models import User as AuthUser
            matiere = get_object_or_404(Matiere, id=request.POST['matiere'])
            professeur = None
            if request.POST.get('professeur'):
                professeur = AuthUser.objects.filter(id=request.POST['professeur'], role='professeur').first()
            MatiereClasse.objects.create(
                classe=classe,
                matiere=matiere,
                professeur=professeur,
                coefficient=request.POST.get('coefficient', 1.0),
                heures_semaine=request.POST.get('heures_semaine', 2),
            )
            messages.success(request, "La matière a été ajoutée à la classe.")
            return redirect('academic:matiere_classe_list', classe_id=classe.id)
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout : {e}")
    from core.models import Matiere
    from accounts.models import User as AuthUser
    context = {
        'title': 'Ajouter une matière',
        'classe': classe,
        'matieres': Matiere.objects.filter(is_active=True),
        'professeurs': AuthUser.objects.filter(role='professeur').order_by('last_name'),
    }
    return render(request, 'academic/matiere_classe_form.html', context)


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
    from schools.models import Classe as SchoolsClasse
    if request.method == 'POST':
        try:
            matiere_classe = get_object_or_404(MatiereClasse, id=request.POST['matiere_classe'])
            classe = get_object_or_404(SchoolsClasse, id=request.POST['classe'])
            Evaluation.objects.create(
                matiere_classe=matiere_classe,
                classe=classe,
                professeur=request.user,
                titre=request.POST['titre'],
                type_evaluation=request.POST['type_evaluation'],
                description=request.POST.get('description', ''),
                date_evaluation=request.POST['date_evaluation'],
                duree=request.POST.get('duree', 60),
                note_maximale=request.POST.get('note_maximale', 20),
                coefficient=request.POST.get('coefficient', 1.0),
            )
            messages.success(request, "L'évaluation a été créée.")
            return redirect('academic:evaluation_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {e}")
    context = {
        'title': 'Créer une évaluation',
        'matieres_classes': MatiereClasse.objects.filter(is_active=True).select_related('matiere', 'classe'),
        'types': Evaluation.TypeEvaluation.choices,
    }
    return render(request, 'academic/evaluation_form.html', context)


@login_required
def evaluation_detail(request, evaluation_id):
    """Détail d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    notes = evaluation.notes.select_related('eleve')
    
    # Statistiques
    if notes.exists():
        moyenne = notes.aggregate(Avg('note'))['note__avg']
        max_note = notes.aggregate(Max('note'))['note__max']
        min_note = notes.aggregate(Min('note'))['note__min']
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

    # Inscriptions actives de la classe pour cette évaluation
    inscriptions = Inscription.objects.filter(
        classe=evaluation.classe,
        annee_scolaire__est_active=True,
    ).select_related('eleve').order_by('eleve__last_name')

    if request.method == 'POST':
        saved = 0
        errors = []
        for inscription in inscriptions:
            eleve_id = str(inscription.eleve.id)
            raw_note = request.POST.get(f'note_{eleve_id}', '').strip()
            if raw_note == '':
                continue
            try:
                note_val = float(raw_note)
                est_absent = f'absent_{eleve_id}' in request.POST
                appreciation = request.POST.get(f'appreciation_{eleve_id}', '')
                Note.objects.update_or_create(
                    evaluation=evaluation,
                    eleve=inscription.eleve,
                    defaults={
                        'inscription': inscription,
                        'note': note_val,
                        'note_sur': evaluation.note_maximale,
                        'appreciation': appreciation,
                        'est_absent': est_absent,
                    }
                )
                saved += 1
            except (ValueError, Exception) as e:
                errors.append(f"{inscription.eleve.get_full_name()}: {e}")

        if errors:
            messages.warning(request, f"{saved} note(s) enregistrée(s). Erreurs : {'; '.join(errors)}")
        else:
            messages.success(request, f"{saved} note(s) enregistrée(s) avec succès.")
        return redirect('academic:evaluation_detail', evaluation_id=evaluation.id)

    existing_notes = {str(n.eleve_id): n for n in Note.objects.filter(evaluation=evaluation)}
    context = {
        'evaluation': evaluation,
        'inscriptions': inscriptions,
        'existing_notes': existing_notes,
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


def _appreciation_from_moyenne(moyenne):
    if moyenne >= 16:
        return "Excellent travail"
    if moyenne >= 14:
        return "Très bien"
    if moyenne >= 12:
        return "Bien"
    if moyenne >= 10:
        return "Assez bien"
    return "Des efforts sont nécessaires"


@login_required
def bulletin_generate(request):
    """Génération de bulletins pour une classe et une période"""
    from schools.models import Classe as SchoolsClasse, AnneeScolaire
    if request.method == 'POST':
        try:
            classe = get_object_or_404(SchoolsClasse, id=request.POST['classe'])
            annee_scolaire = get_object_or_404(AnneeScolaire, id=request.POST['annee_scolaire'])
            periode = request.POST['periode']
            type_bulletin = request.POST.get('type_bulletin', BulletinNotes.TypeBulletin.TRIMESTRIEL)

            inscriptions = list(
                Inscription.objects.filter(
                    classe=classe,
                    annee_scolaire=annee_scolaire,
                    statut=Inscription.StatutInscription.CONFIRMEE,
                ).select_related('eleve')
            )
            if not inscriptions:
                messages.warning(request, "Aucun élève confirmé trouvé pour cette classe.")
                return redirect('academic:bulletin_list')

            moyennes = []
            for inscription in inscriptions:
                notes_qs = Note.objects.filter(inscription=inscription, est_absent=False).select_related('evaluation')
                total_coef = sum(float(n.evaluation.coefficient) for n in notes_qs)
                total_pts = sum(float(n.note_sur_20) * float(n.evaluation.coefficient) for n in notes_qs)
                moyenne = round(total_pts / total_coef, 2) if total_coef > 0 else 0
                moyennes.append((inscription, moyenne))

            all_vals = [m for _, m in moyennes]
            moyenne_classe = round(sum(all_vals) / len(all_vals), 2)
            moyennes.sort(key=lambda x: x[1], reverse=True)

            created_count = 0
            for rang, (inscription, moyenne) in enumerate(moyennes, 1):
                _, created = BulletinNotes.objects.update_or_create(
                    inscription=inscription,
                    periode=periode,
                    annee_scolaire=annee_scolaire,
                    defaults={
                        'eleve': inscription.eleve,
                        'classe': classe,
                        'type_bulletin': type_bulletin,
                        'moyenne_generale': moyenne,
                        'moyenne_classe': moyenne_classe,
                        'rang': rang,
                        'effectif_classe': len(moyennes),
                        'appreciation_generale': _appreciation_from_moyenne(moyenne),
                        'signe_par': request.user,
                    }
                )
                if created:
                    created_count += 1

            messages.success(request, f"{created_count} bulletin(s) créé(s), {len(moyennes) - created_count} mis à jour.")
            return redirect('academic:bulletin_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération : {e}")

    context = {
        'title': 'Générer des bulletins',
        'classes': SchoolsClasse.objects.filter(is_active=True),
        'annees': AnneeScolaire.objects.filter(est_active=True),
        'types': BulletinNotes.TypeBulletin.choices,
    }
    return render(request, 'academic/bulletin_generate_form.html', context)


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
