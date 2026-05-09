"""
Tâches Redis pour le module analytics
Génération de rapports, calcul des KPI
"""

import logging
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files import File
from core.redis_tasks import redis_task
from .models import RapportStatistique, IndicateurPerformance

logger = logging.getLogger(__name__)


@redis_task("analytics.generer_rapport_statistique")
def generer_rapport_statistique(rapport_id):
    """
    Générer un rapport statistique complet en arrière-plan
    """
    try:
        from xhtml2pdf import pisa
        from django.shortcuts import get_object_or_404
        
        rapport = get_object_or_404(RapportStatistique, id=rapport_id)
        etablissement = rapport.etablissement
        
        # Collecter les données selon le type de rapport
        donnees = collecter_donnees_rapport(rapport)
        
        # Mettre à jour le rapport
        rapport.donnees = donnees
        rapport.save()
        
        # Générer PDF si nécessaire
        html_content = render_to_string(f'analytics/rapport_{rapport.type_rapport}.html', {
            'rapport': rapport,
            'etablissement': etablissement,
            'donnees': donnees,
        })
        
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content.encode('utf-8'), dest=pdf_buffer)
        pdf_buffer.seek(0)
        
        filename = f"rapport_{rapport.type_rapport}_{rapport.periode_fin}.pdf"
        rapport.fichier_rapport.save(filename, File(pdf_buffer))
        
        # Notifier le générateur
        from notifications.utils import send_notification
        send_notification.delay(
            user_id=rapport.genere_par.id,
            title="Rapport généré",
            message=f"Votre rapport {rapport.get_type_rapport_display()} est prêt"
        )
        
        logger.info(f"✅ Rapport statistique généré: {filename}")
        return f"Rapport généré: {filename}"
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport {rapport_id}: {e}")
        raise


def collecter_donnees_rapport(rapport):
    """
    Collecter les données selon le type de rapport
    """
    from academic.models import Note, BulletinNotes
    from attendance.models import Presence
    from payments.models import Paiement
    
    donnees = {}
    
    if rapport.type_rapport == RapportStatistique.TypeRapport.PERFORMANCE_ELEVES:
        # Performance des élèves
        bulletins = BulletinNotes.objects.filter(
            inscription__classe__etablissement=rapport.etablissement,
            date_generation__range=[rapport.periode_debut, rapport.periode_fin]
        )
        
        donnees['total_eleves'] = bulletins.count()
        donnees['moyenne_generale'] = sum(b.moyenne_generale for b in bulletins) / bulletins.count() if bulletins else 0
        donnees['taux_reussite'] = sum(1 for b in bulletins if b.moyenne_generale >= 10) / bulletins.count() * 100 if bulletins else 0
        
    elif rapport.type_rapport == RapportStatistique.TypeRapport.ASSIDUITE:
        # Assiduité
        presences = Presence.objects.filter(
            eleve__etablissement=rapport.etablissement,
            date__range=[rapport.periode_debut, rapport.periode_fin]
        )
        
        total = presences.count()
        presents = presences.filter(est_present=True).count()
        
        donnees['total_seances'] = total
        donnees['taux_presence'] = presents / total * 100 if total > 0 else 0
        donnees['taux_absence'] = (total - presents) / total * 100 if total > 0 else 0
        
    elif rapport.type_rapport == RapportStatistique.TypeRapport.FINANCIER:
        # Financier
        paiements = Paiement.objects.filter(
            frais__etablissement=rapport.etablissement,
            date_paiement__range=[rapport.periode_debut, rapport.periode_fin]
        )
        
        donnees['total_encaisse'] = sum(p.montant_paye for p in paiements)
        donnees['nombre_paiements'] = paiements.count()
        donnees['moyenne_paiement'] = donnees['total_encaisse'] / paiements.count() if paiements else 0
    
    return donnees


@redis_task("analytics.calculer_kpi")
def calculer_kpi(etablissement_id, type_indicateur, periode):
    """
    Calculer un indicateur de performance clé
    """
    try:
        from django.shortcuts import get_object_or_404
        from schools.models import Etablissement
        
        etablissement = get_object_or_404(Etablissement, id=etablissement_id)
        
        # Calculer selon le type
        valeur = 0
        if type_indicateur == IndicateurPerformance.TypeIndicateur.TAUX_REUSSITE:
            from academic.models import BulletinNotes
            bulletins = BulletinNotes.objects.filter(
                inscription__classe__etablissement=etablissement,
                periode=periode
            )
            if bulletins:
                reussites = sum(1 for b in bulletins if b.moyenne_generale >= 10)
                valeur = reussites / bulletins.count() * 100
                
        elif type_indicateur == IndicateurPerformance.TypeIndicateur.TAUX_PRESENCE:
            from attendance.models import Presence
            from django.db.models import Count
            
            presences = Presence.objects.filter(
                eleve__etablissement=etablissement,
                date__month=int(periode.split('-')[2])
            ).aggregate(
                total=Count('id'),
                presents=Count('id', filter={'est_present': True})
            )
            if presences['total']:
                valeur = presences['presents'] / presences['total'] * 100
        
        # Sauvegarder l'indicateur
        IndicateurPerformance.objects.update_or_create(
            etablissement=etablissement,
            type_indicateur=type_indicateur,
            periode=periode,
            defaults={'valeur_actuelle': valeur}
        )
        
        logger.info(f"✅ KPI calculé: {type_indicateur} = {valeur:.2f}")
        return f"{type_indicateur}: {valeur:.2f}"
        
    except Exception as e:
        logger.error(f"❌ Erreur calcul KPI: {e}")
        raise


@redis_task("analytics.generer_tableau_bord")
def generer_tableau_bord(utilisateur_id, periode):
    """
    Générer un tableau de bord personnalisé
    """
    try:
        from accounts.models import User
        from django.shortcuts import get_object_or_404
        
        utilisateur = get_object_or_404(User, id=utilisateur_id)
        
        # Collecter les widgets selon le rôle
        widgets = []
        
        if utilisateur.role == 'admin':
            widgets = [
                {'type': 'statistiques_globales', 'position': 1},
                {'type': 'revenus', 'position': 2},
                {'type': 'taux_reussite', 'position': 3},
                {'type': 'absences', 'position': 4},
            ]
        elif utilisateur.role == 'professeur':
            widgets = [
                {'type': 'mes_classes', 'position': 1},
                {'type': 'notes_a_saisir', 'position': 2},
                {'type': 'cahier_texte', 'position': 3},
            ]
        elif utilisateur.role == 'eleve':
            widgets = [
                {'type': 'mes_notes', 'position': 1},
                {'type': 'emploi_temps', 'position': 2},
                {'type': 'prochains_examens', 'position': 3},
            ]
        
        from .models import TableauBord
        TableauBord.objects.update_or_create(
            utilisateur=utilisateur,
            defaults={'configuration': {'widgets': widgets, 'periode': periode}}
        )
        
        logger.info(f"✅ Tableau de bord généré pour {utilisateur.username}")
        return f"Tableau de bord: {len(widgets)} widgets"
        
    except Exception as e:
        logger.error(f"❌ Erreur génération tableau de bord: {e}")
        raise
