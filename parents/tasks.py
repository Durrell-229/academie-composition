"""
Tâches Redis pour le module parents
Notifications, synchronisation des données
"""

import logging
from django.conf import settings
from core.redis_tasks import redis_task
from .models import Parent, NotificationParent, Enfant

logger = logging.getLogger(__name__)


@redis_task("parents.notifier_absence")
def notifier_absence_eleve(absence_id):
    """
    Notifier les parents d'une absence de leur enfant
    """
    try:
        from attendance.models import Absence
        from notifications.utils import send_notification
        from django.shortcuts import get_object_or_404
        
        absence = get_object_or_404(Absence, id=absence_id)
        eleve = absence.eleve
        
        # Récupérer les parents
        parents = Parent.objects.filter(
            enfants__eleve=eleve,
            enfants__is_principal=True,
            is_actif=True
        )
        
        for parent in parents:
            # Créer notification dans le système parents
            NotificationParent.objects.create(
                parent=parent,
                eleve=eleve,
                type_notification='absence',
                titre=f"Absence de {eleve.first_name}",
                contenu=f"{eleve.first_name} était absent le {absence.date_absence}. Cours: {absence.cours or 'Non spécifié'}."
            )
            
            # Envoyer notification push
            send_notification.delay(
                user_id=parent.user.id,
                title=f"⚠️ Absence de {eleve.first_name}",
                message=f"Absent le {absence.date_absence}"
            )
        
        logger.info(f"✅ Parents notifiés pour absence {absence_id}")
        return f"{parents.count()} parents notifiés"
        
    except Exception as e:
        logger.error(f"❌ Erreur notification absence {absence_id}: {e}")
        raise


@redis_task("parents.notifier_retard")
def notifier_retard_eleve(retard_id):
    """
    Notifier les parents d'un retard de leur enfant
    """
    try:
        from attendance.models import Retard
        from notifications.utils import send_notification
        from django.shortcuts import get_object_or_404
        
        retard = get_object_or_404(Retard, id=retard_id)
        eleve = retard.eleve
        
        parents = Parent.objects.filter(
            enfants__eleve=eleve,
            enfants__is_principal=True,
            is_actif=True
        )
        
        for parent in parents:
            NotificationParent.objects.create(
                parent=parent,
                eleve=eleve,
                type_notification='retard',
                titre=f"Retard de {eleve.first_name}",
                contenu=f"{eleve.first_name} est arrivé en retard le {retard.date_retard} ({retard.duree_minutes} minutes)."
            )
            
            send_notification.delay(
                user_id=parent.user.id,
                title=f"⏰ Retard de {eleve.first_name}",
                message=f"Retard de {retard.duree_minutes} minutes"
            )
        
        logger.info(f"✅ Parents notifiés pour retard {retard_id}")
        return f"{parents.count()} parents notifiés"
        
    except Exception as e:
        logger.error(f"❌ Erreur notification retard {retard_id}: {e}")
        raise


@redis_task("parents.notifier_bulletin")
def notifier_bulletin_disponible(bulletin_id):
    """
    Notifier les parents qu'un bulletin est disponible
    """
    try:
        from academic.models import BulletinNotes
        from notifications.utils import send_notification
        from django.shortcuts import get_object_or_404
        
        bulletin = get_object_or_404(BulletinNotes, id=bulletin_id)
        eleve = bulletin.inscription.eleve
        
        parents = Parent.objects.filter(enfants__eleve=eleve, is_actif=True)
        
        mention_text = bulletin.get_statut_display() if bulletin.moyenne_generale >= 10 else "À améliorer"
        
        for parent in parents:
            NotificationParent.objects.create(
                parent=parent,
                eleve=eleve,
                type_notification='bulletin',
                titre=f"Bulletin disponible - {eleve.first_name}",
                contenu=f"Le bulletin du {bulletin.get_periode_display()} est disponible. Moyenne: {bulletin.moyenne_generale}/20 - Mention: {mention_text}"
            )
            
            send_notification.delay(
                user_id=parent.user.id,
                title=f"📊 Bulletin de {eleve.first_name}",
                message=f"Moyenne: {bulletin.moyenne_generale}/20 - {mention_text}"
            )
        
        logger.info(f"✅ Parents notifiés pour bulletin {bulletin_id}")
        return f"{parents.count()} parents notifiés"
        
    except Exception as e:
        logger.error(f"❌ Erreur notification bulletin {bulletin_id}: {e}")
        raise


@redis_task("parents.notifier_paiement")
def notifier_paiement_requis(paiement_id):
    """
    Notifier les parents d'un paiement requis
    """
    try:
        from payments.models import Paiement
        from notifications.utils import send_notification
        from django.shortcuts import get_object_or_404
        
        paiement = get_object_or_404(Paiement, id=paiement_id)
        eleve = paiement.eleve
        
        parents = Parent.objects.filter(
            enfants__eleve=eleve,
            enfants__is_principal=True,
            is_actif=True
        )
        
        for parent in parents:
            NotificationParent.objects.create(
                parent=parent,
                eleve=eleve,
                type_notification='paiment',
                titre=f"Paiement requis - {paiement.frais.nom}",
                contenu=f"Un paiement de {paiement.montant_restant:,.0f} FCFA est requis pour {paiement.frais.nom} ({eleve.first_name})."
            )
            
            send_notification.delay(
                user_id=parent.user.id,
                title=f"💰 Paiement requis",
                message=f"{paiement.frais.nom}: {paiement.montant_restant:,.0f} FCFA"
            )
        
        logger.info(f"✅ Parents notifiés pour paiement {paiement_id}")
        return f"{parents.count()} parents notifiés"
        
    except Exception as e:
        logger.error(f"❌ Erreur notification paiement {paiement_id}: {e}")
        raise


@redis_task("parents.sync_donnees_parent")
def sync_donnees_parent(parent_id):
    """
    Synchroniser les données d'un parent avec les informations des enfants
    """
    try:
        from django.shortcuts import get_object_or_404
        
        parent = get_object_or_404(Parent, id=parent_id)
        enfants = Enfant.objects.filter(parent=parent)
        
        stats = {
            'enfants_count': enfants.count(),
            'absences_recentes': 0,
            'retards_recents': 0,
            'paiements_en_attente': 0,
            'bulletins_non_consultes': 0
        }
        
        for enfant in enfants:
            eleve = enfant.eleve
            
            # Compter les absences récentes (7 derniers jours)
            from attendance.models import Absence
            from datetime import datetime, timedelta
            
            date_limite = datetime.now() - timedelta(days=7)
            stats['absences_recentes'] += Absence.objects.filter(
                eleve=eleve,
                date_absence__gte=date_limite
            ).count()
            
            # Compter les paiements en attente
            from payments.models import Paiement
            stats['paiements_en_attente'] += Paiement.objects.filter(
                eleve=eleve,
                statut__in=['en_attente', 'partiel']
            ).count()
        
        logger.info(f"✅ Données parent {parent_id} synchronisées: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur sync données parent {parent_id}: {e}")
        raise
