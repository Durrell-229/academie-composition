"""
Vues pour les dashboards fonctionnels avec données réelles
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Max, Min
from django.utils import timezone
from datetime import timedelta
import logging

from accounts.models import User
from core.models import Matiere, Classe
from exams.models import Exam, ExamAssignment
from compositions.models import CompositionSession
from correction.models import CorrectionCopie
from bulletins.models import Bulletin
from notifications.models import Notification
from gamification.models import GlobalLeaderboard, Badge, UserBadge

logger = logging.getLogger(__name__)


@login_required
def dashboard_eleve(request):
    """Dashboard élève avec données réelles"""
    user = request.user
    
    if user.role != 'eleve':
        return redirect('dashboard_professeur' if user.role == 'professeur' else 'dashboard_admin')
    
    context = {
        'user': user,
    }
    
    try:
        # Statistiques examens
        context['examens_termines'] = CorrectionCopie.objects.filter(
            student=user,
            status='approved'
        ).count()
        
        context['examens_en_cours'] = CompositionSession.objects.filter(
            eleve=user,
            statut='en_cours'
        ).count()
        
        context['examens_a_venir'] = ExamAssignment.objects.filter(
            eleve=user,
            exam__date_debut__gt=timezone.now()
        ).count()
        
        # Moyenne générale
        moyenne = CorrectionCopie.objects.filter(
            student=user,
            status='approved'
        ).aggregate(avg=Avg('grade'))['avg']
        context['moyenne_generale'] = round(moyenne, 2) if moyenne else 0
        
        # Rang dans la classe
        if user.classe:
            notes_classe = CorrectionCopie.objects.filter(
                student__classe=user.classe,
                status='approved'
            ).values('student').annotate(avg=Avg('grade')).order_by('-avg')
            
            for i, note in enumerate(notes_classe, 1):
                if note['student'] == user.id:
                    context['rang_classe'] = i
                    context['total_eleves'] = len(notes_classe)
                    break
        else:
            context['rang_classe'] = None
            context['total_eleves'] = 0
        
        # Dernières corrections
        dernieres_corrections = CorrectionCopie.objects.filter(
            student=user
        ).order_by('-created_at')[:5]
        
        context['dernieres_corrections'] = dernieres_corrections
        
        # Prochains examens
        context['prochains_examens'] = ExamAssignment.objects.filter(
            eleve=user,
            exam__date_debut__gte=timezone.now()
        ).select_related('exam', 'exam__matiere').order_by('exam__date_debut')[:5]
        
        # Notifications non lues
        context['notifications_non_lues'] = Notification.objects.filter(
            recipient=user,
            read=False
        ).count()
        
        # XP et Badges (gamification)
        try:
            user_xp = GlobalLeaderboard.objects.filter(user=user).order_by('-updated_at').first()
            if user_xp:
                context['xp_total'] = user_xp.points_xp
                context['niveau'] = user_xp.niveau
                context['xp_pourcentage'] = min(100, int((user_xp.points_xp % 1000) / 10))
            else:
                context['xp_total'] = 0
                context['niveau'] = 1
                context['xp_pourcentage'] = 0
        except Exception:
            context['xp_total'] = 0
            context['niveau'] = 1
            context['xp_pourcentage'] = 0
        
        user_badges = UserBadge.objects.filter(user=user).select_related('badge')[:6]
        context['badges'] = [ub.badge for ub in user_badges]
        context['badges_count'] = UserBadge.objects.filter(user=user).count()
        
        # Graphique des notes par matière
        notes_par_matiere = CorrectionCopie.objects.filter(
            student=user,
            status='approved'
        ).values('exam__matiere__nom').annotate(
            moyenne=Avg('grade')
        ).order_by('exam__matiere__nom')
        
        context['notes_par_matiere'] = list(notes_par_matiere)
        context['chart_labels'] = [n['exam__matiere__nom'] for n in notes_par_matiere]
        context['chart_data'] = [float(n['moyenne']) for n in notes_par_matiere]
        
        # Évolution des notes sur 6 mois
        six_mois = timezone.now() - timedelta(days=180)
        evolution = CorrectionCopie.objects.filter(
            student=user,
            status='approved',
            created_at__gte=six_mois
        ).order_by('created_at')
        
        context['evolution_labels'] = [r.created_at.strftime('%b') for r in evolution]
        context['evolution_data'] = [float(r.grade) for r in evolution]
        
    except Exception as e:
        logger.error(f"Erreur dashboard élève: {e}")
        context['erreur'] = str(e)
    
    return render(request, 'dashboards/eleve.html', context)


@login_required
def dashboard_professeur(request):
    """Dashboard professeur avec données réelles"""
    user = request.user
    
    if user.role not in ['professeur', 'conseiller']:
        return redirect('dashboard_eleve' if user.role == 'eleve' else 'dashboard_admin')
    
    context = {'user': user}
    
    try:
        # Statistiques
        context['examens_crees'] = Exam.objects.filter(createur=user).count()
        context['examens_publies'] = Exam.objects.filter(
            createur=user,
            statut='publie'
        ).count()
        context['examens_en_cours'] = Exam.objects.filter(
            createur=user,
            statut='en_cours'
        ).count()
        
        # Copies à corriger
        context['copies_a_corriger'] = CompositionSession.objects.filter(
            exam__createur=user,
            statut='soumis'
        ).count()
        
        # Total élèves assignés
        context['total_eleves'] = ExamAssignment.objects.filter(
            exam__createur=user
        ).values('eleve').distinct().count()
        
        # Moyenne générale des copies corrigées
        moyenne = CorrectionCopie.objects.filter(
            exam__createur=user,
            status='approved'
        ).aggregate(avg=Avg('grade'))['avg']
        context['moyenne_classe'] = round(moyenne, 2) if moyenne else 0
        
        # Derniers examens créés
        context['derniers_examens'] = Exam.objects.filter(
            createur=user
        ).select_related('matiere', 'classe').order_by('-date_creation')[:5]
        
        # Copies récemment soumises
        context['copies_recentes'] = CompositionSession.objects.filter(
            exam__createur=user,
            statut='soumis'
        ).select_related('eleve', 'exam').order_by('-date_fin')[:10]
        
        # Statistiques par matière
        context['stats_par_matiere'] = Exam.objects.filter(
            createur=user
        ).values('matiere__nom').annotate(
            total=Count('id'),
            moyenne=Avg('correctioncopie__grade')
        ).order_by('-total')
        
        # Notifications
        context['notifications_non_lues'] = Notification.objects.filter(
            recipient=user,
            read=False
        ).count()
        
        # Alertes anti-triche
        context['alertes_anticheat'] = 0  # À implémenter avec le système anti-triche
        
        # Distribution des notes (pour graphique)
        notes = CorrectionCopie.objects.filter(
            exam__createur=user,
            status='approved'
        ).values_list('grade', flat=True)
        
        distribution = {'moins_5': 0, 'moins_10': 0, 'moins_15': 0, 'plus_15': 0}
        for note in notes:
            if note <= 5:
                distribution['moins_5'] += 1
            elif note <= 10:
                distribution['moins_10'] += 1
            elif note <= 15:
                distribution['moins_15'] += 1
            else:
                distribution['plus_15'] += 1
        
        context['distribution_notes'] = distribution
        
    except Exception as e:
        logger.error(f"Erreur dashboard professeur: {e}")
        context['erreur'] = str(e)
    
    return render(request, 'dashboards/professeur.html', context)


@login_required
def dashboard_admin(request):
    """Dashboard admin avec données réelles"""
    user = request.user
    
    if not user.is_staff and user.role != 'admin':
        return redirect('dashboard_eleve')
    
    context = {'user': user}
    
    try:
        # Statistiques globales
        context['total_eleves'] = User.objects.filter(role='eleve').count()
        context['total_professeurs'] = User.objects.filter(role='professeur').count()
        context['total_classes'] = Classe.objects.filter(is_active=True).count()
        context['total_matieres'] = Matiere.objects.filter(is_active=True).count()
        
        # Examens
        context['examens_total'] = Exam.objects.count()
        context['examens_en_cours'] = Exam.objects.filter(statut='en_cours').count()
        context['examens_termines'] = Exam.objects.filter(statut='termine').count()
        
        # Copies
        context['copies_total'] = CompositionSession.objects.count()
        context['copies_corrigees'] = CorrectionCopie.objects.filter(status='approved').count()
        context['copies_en_attente'] = CompositionSession.objects.filter(
            statut='soumis'
        ).count()
        
        # Moyenne globale
        moyenne = CorrectionCopie.objects.filter(status='approved').aggregate(avg=Avg('grade'))['avg']
        context['moyenne_globale'] = round(moyenne, 2) if moyenne else 0
        
        # Activité récente (7 jours)
        sept_jours = timezone.now() - timedelta(days=7)
        context['nouveaux_eleves'] = User.objects.filter(
            role='eleve',
            date_joined__gte=sept_jours
        ).count()
        context['nouveaux_examens'] = Exam.objects.filter(
            date_creation__gte=sept_jours
        ).count()
        context['copies_cette_semaine'] = CompositionSession.objects.filter(
            date_fin__gte=sept_jours
        ).count()
        
        # Top classes par moyenne
        context['top_classes'] = Classe.objects.filter(
            is_active=True
        ).annotate(
            moyenne=Avg('exam_assignments__exam__correctioncopie__grade')
        ).order_by('-moyenne')[:5]
        
        # Top matières
        context['top_matieres'] = Matiere.objects.filter(
            is_active=True
        ).annotate(
            total_examens=Count('exams')
        ).order_by('-total_examens')[:5]
        
        # Utilisateurs connectés récemment
        context['utilisateurs_recents'] = User.objects.filter(
            last_login__gte=sept_jours
        ).order_by('-last_login')[:10]
        
        # Graphique d'activité mensuelle
        mois = []
        examens_par_mois = []
        copies_par_mois = []
        
        for i in range(5, -1, -1):
            date = timezone.now() - timedelta(days=i*30)
            mois.append(date.strftime('%b'))
            
            debut_mois = date.replace(day=1)
            fin_mois = (debut_mois + timedelta(days=32)).replace(day=1)
            
            examens_par_mois.append(
                Exam.objects.filter(date_creation__gte=debut_mois, date_creation__lt=fin_mois).count()
            )
            copies_par_mois.append(
                CompositionSession.objects.filter(date_fin__gte=debut_mois, date_fin__lt=fin_mois).count()
            )
        
        context['mois_labels'] = mois
        context['examens_par_mois'] = examens_par_mois
        context['copies_par_mois'] = copies_par_mois
        
    except Exception as e:
        logger.error(f"Erreur dashboard admin: {e}")
        context['erreur'] = str(e)
    
    return render(request, 'dashboards/admin.html', context)


@login_required
def dashboard_redirect(request):
    """Redirection vers le bon dashboard selon le rôle"""
    user = request.user
    
    if user.role == 'eleve':
        return redirect('dashboard_eleve')
    elif user.role in ['professeur', 'conseiller']:
        return redirect('dashboard_professeur')
    else:
        return redirect('dashboard_admin')
