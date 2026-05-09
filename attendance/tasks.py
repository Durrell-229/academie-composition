"""
Tâches Redis pour le module attendance
Rapports de présence, notifications
"""

import logging
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files import File
from core.redis_tasks import redis_task
from .models import Presence, Absence, Retard, RapportPresence

logger = logging.getLogger(__name__)


@redis_task("attendance.generer_rapport_mensuel")
def generer_rapport_mensuel(classe_id, mois, annee):
    """
    Générer le rapport de présence mensuel pour une classe
    """
    try:
        from xhtml2pdf import pisa
        from django.shortcuts import get_object_or_404
        from schools.models import Classe
        from academic.models import Inscription
        
        classe = get_object_or_404(Classe, id=classe_id)
        inscriptions = Inscription.objects.filter(classe=classe, is_active=True)
        
        stats_eleves = []
        
        for inscription in inscriptions:
            eleve = inscription.eleve
            
            # Statistiques du mois
            presences = Presence.objects.filter(
                eleve=eleve,
                classe=classe,
                date__month=mois,
                date__year=annee
            )
            
            absences = Absence.objects.filter(
                eleve=eleve,
                date_absence__month=mois,
                date_absence__year=annee
            )
            
            retards = Retard.objects.filter(
                eleve=eleve,
                date_retard__month=mois,
                date_retard__year=annee
            )
            
            stats_eleves.append({
                'eleve': eleve,
                'presences': presences.filter(est_present=True).count(),
                'absences': absences.count(),
                'absences_justifiees': absences.filter(justifiee=True).count(),
                'retards': retards.count(),
                'minutes_retard': sum(r.duree_minutes for r in retards)
            })
        
        # Générer PDF
        html_content = render_to_string('attendance/rapport_mensuel.html', {
            'classe': classe,
            'mois': mois,
            'annee': annee,
            'stats': stats_eleves,
        })
        
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content.encode('utf-8'), dest=pdf_buffer)
        pdf_buffer.seek(0)
        
        # Sauvegarder le rapport
        rapport = RapportPresence.objects.create(
            classe=classe,
            mois=mois,
            annee=annee,
            type_rapport='mensuel',
            nombre_eleves=len(stats_eleves),
            total_absences=sum(s['absences'] for s in stats_eleves),
            total_retards=sum(s['retards'] for s in stats_eleves)
        )
        
        filename = f"rapport_presence_{classe.nom}_{mois}_{annee}.pdf"
        rapport.fichier_rapport.save(filename, File(pdf_buffer))
        
        logger.info(f"✅ Rapport présence généré: {filename}")
        return f"Rapport généré: {filename}"
        
    except Exception as e:
        logger.error(f"❌ Erreur rapport présence: {e}")
        raise


@redis_task("attendance.notifier_absences_cumulees")
def notifier_absences_cumulees(eleve_id):
    """
    Notifier si un élève a trop d'absences
    """
    try:
        from accounts.models import User
        from django.shortcuts import get_object_or_404
        from datetime import datetime, timedelta
        
        eleve = get_object_or_404(User, id=eleve_id)
        
        # Compter les absences des 30 derniers jours
        date_limite = datetime.now() - timedelta(days=30)
        
        absences_count = Absence.objects.filter(
            eleve=eleve,
            date_absence__gte=date_limite
        ).count()
        
        # Si plus de 5 absences en un mois, alerter
        if absences_count >= 5:
            from parents.tasks import notifier_absence_eleve
            from notifications.utils import send_notification
            
            # Notifier le professeur principal
            if hasattr(eleve, 'classe_actuelle') and eleve.classe_actuelle.professeur_principal:
                send_notification.delay(
                    user_id=eleve.classe_actuelle.professeur_principal.id,
                    title=f"⚠️ Alert absences - {eleve.get_full_name()}",
                    message=f"{eleve.first_name} a {absences_count} absences ce mois"
                )
            
            # Notifier les parents
            for parent in eleve.parents.filter(is_principal=True):
                send_notification.delay(
                    user_id=parent.user.id,
                    title=f"⚠️ Alert absences - {eleve.first_name}",
                    message=f"Votre enfant a {absences_count} absences ce mois"
                )
            
            logger.info(f"✅ Alert absences envoyée pour {eleve.get_full_name()}: {absences_count} absences")
            return f"Alert envoyée: {absences_count} absences"
        
        return f"Pas d'alert: {absences_count} absences"
        
    except Exception as e:
        logger.error(f"❌ Erreur notification absences: {e}")
        raise


@redis_task("attendance.calculer_statistiques_assiduite")
def calculer_statistiques_assiduite(classe_id, date_debut, date_fin):
    """
    Calculer les statistiques d'assiduité pour une période
    """
    try:
        from schools.models import Classe
        from academic.models import Inscription
        from django.shortcuts import get_object_or_404
        
        classe = get_object_or_404(Classe, id=classe_id)
        inscriptions = Inscription.objects.filter(classe=classe, is_active=True)
        
        stats = {
            'total_eleves': inscriptions.count(),
            'taux_presence_moyen': 0,
            'eleves_sous_seuil': [],  # Moins de 80% de présence
        }
        
        presences_totales = []
        
        for inscription in inscriptions:
            presences = Presence.objects.filter(
                eleve=inscription.eleve,
                classe=classe,
                date__range=[date_debut, date_fin]
            )
            
            total = presences.count()
            presents = presences.filter(est_present=True).count()
            
            if total > 0:
                taux = presents / total * 100
                presences_totales.append(taux)
                
                if taux < 80:
                    stats['eleves_sous_seuil'].append({
                        'eleve': inscription.eleve.get_full_name(),
                        'taux_presence': taux
                    })
        
        if presences_totales:
            stats['taux_presence_moyen'] = sum(presences_totales) / len(presences_totales)
        
        logger.info(f"✅ Stats assiduité: {stats['taux_presence_moyen']:.1f}% moyenne, {len(stats['eleves_sous_seuil'])} élèves sous seuil")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur stats assiduité: {e}")
        raise
