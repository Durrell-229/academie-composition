"""
Signaux Django pour les mises à jour temps réel des dashboards
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .services import realtime_service
from correction.models import CorrectionCopie
from compositions.models import CompositionSession
from exams.models import Exam
from gamification.models import GlobalLeaderboard, UserBadge
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CorrectionCopie)
def correction_completed_signal(sender, instance, created, **kwargs):
    """Déclencher une notification quand une correction est complétée"""
    if instance.status == 'approved' and not created:
        try:
            correction_data = {
                'id': instance.id,
                'student_id': instance.student.id,
                'professor_id': instance.exam.createur.id if instance.exam.createur else None,
                'grade': instance.grade,
                'exam_title': instance.exam.titre,
                'matiere': instance.exam.matiere.nom if instance.exam.matiere else 'N/A',
                'created_at': instance.created_at.isoformat(),
                'stats': {
                    'total_corrections': CorrectionCopie.objects.filter(status='approved').count(),
                    'avg_grade': CorrectionCopie.objects.filter(status='approved').aggregate(
                        avg=models.Avg('grade')
                    )['avg__grade'] or 0
                }
            }
            
            realtime_service.send_correction_completed(correction_data)
            logger.info(f"Signal correction complétée envoyée pour {instance.id}")
            
        except Exception as e:
            logger.error(f"Erreur signal correction: {e}")

@receiver(post_save, sender=CompositionSession)
def composition_session_signal(sender, instance, created, **kwargs):
    """Déclencher une notification quand une session de composition change"""
    try:
        # Notifier le début d'une composition
        if instance.statut == 'en_cours':
            session_data = {
                'id': instance.id,
                'exam_id': instance.exam.id,
                'student_id': instance.eleve.id,
                'exam_title': instance.exam.titre,
                'status': instance.statut,
                'started_at': instance.started_at.isoformat() if instance.started_at else None
            }
            
            realtime_service.send_dashboard_update(
                instance.eleve.id,
                'composition_started',
                session_data
            )
        
        # Notifier la soumission d'une composition
        elif instance.statut == 'soumis':
            session_data = {
                'id': instance.id,
                'exam_id': instance.exam.id,
                'student_id': instance.eleve.id,
                'exam_title': instance.exam.titre,
                'status': instance.statut,
                'submitted_at': instance.submitted_at.isoformat() if instance.submitted_at else None
            }
            
            # Notifier le professeur
            if instance.exam.createur:
                realtime_service.send_dashboard_update(
                    instance.exam.createur.id,
                    'composition_submitted',
                    session_data
                )
            
            # Mettre à jour les stats
            stats_data = {
                'pending_corrections': CompositionSession.objects.filter(
                    statut='soumis'
                ).count(),
                'total_compositions': CompositionSession.objects.count()
            }
            
            realtime_service.send_role_update('professeur', 'stats_updated', stats_data)
            
    except Exception as e:
        logger.error(f"Erreur signal composition session: {e}")

@receiver(post_save, sender=Exam)
def exam_status_signal(sender, instance, **kwargs):
    """Déclencher une notification quand le statut d'un examen change"""
    try:
        exam_data = {
            'id': instance.id,
            'title': instance.titre,
            'matiere': instance.matiere.nom if instance.matiere else 'N/A',
            'status': instance.statut,
            'date_debut': instance.date_debut.isoformat() if instance.date_debut else None,
            'date_fin': instance.date_fin.isoformat() if instance.date_fin else None,
            'createur_id': instance.createur.id if instance.createur else None
        }
        
        realtime_service.send_exam_status_change(exam_data)
        logger.info(f"Signal statut examen envoyé pour {instance.id}")
        
    except Exception as e:
        logger.error(f"Erreur signal examen: {e}")

@receiver(post_save, sender=GlobalLeaderboard)
def xp_updated_signal(sender, instance, created, **kwargs):
    """Déclencher une notification quand l'XP est mis à jour"""
    try:
        # Vérifier si c'est une mise à jour significative
        if not created:
            xp_data = {
                'user_id': instance.user.id,
                'total_xp': instance.points_xp,
                'level': instance.level,
                'rank': instance.rank,
                'updated_at': instance.updated_at.isoformat(),
                'level_up': False  # À implémenter selon la logique de niveau
            }
            
            realtime_service.send_xp_updated(instance.user.id, xp_data)
            logger.info(f"Signal XP mis à jour envoyé pour utilisateur {instance.user.id}")
            
    except Exception as e:
        logger.error(f"Erreur signal XP: {e}")

@receiver(post_save, sender=UserBadge)
def badge_earned_signal(sender, instance, created, **kwargs):
    """Déclencher une notification quand un badge est obtenu"""
    if created:
        try:
            badge_data = {
                'user_id': instance.user.id,
                'badge_id': instance.badge.id,
                'badge_name': instance.badge.name,
                'badge_description': instance.badge.description,
                'badge_icon': instance.badge.icon or '🏆',
                'earned_at': instance.earned_at.isoformat() if instance.earned_at else None
            }
            
            realtime_service.send_badge_earned(instance.user.id, badge_data)
            logger.info(f"Signal badge obtenu envoyé pour utilisateur {instance.user.id}")
            
        except Exception as e:
            logger.error(f"Erreur signal badge: {e}")

@receiver(post_save, sender=User)
def user_activity_signal(sender, instance, created, **kwargs):
    """Déclencher une notification pour l'activité utilisateur"""
    if not created:
        try:
            # Envoyer le statut de connexion (si implémenté)
            user_data = {
                'user_id': instance.id,
                'username': instance.username,
                'full_name': instance.get_full_name(),
                'role': instance.role,
                'is_active': instance.is_active,
                'last_login': instance.last_login.isoformat() if instance.last_login else None
            }
            
            realtime_service.send_user_online_status(user_data)
            
        except Exception as e:
            logger.error(f"Erreur signal activité utilisateur: {e}")

# Import des modèles nécessaires
from django.db import models
