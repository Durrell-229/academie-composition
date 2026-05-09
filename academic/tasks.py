"""
Tâches Redis pour le module academic
Génération des bulletins, calcul des moyennes, notifications
"""

import logging
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files import File
from core.redis_tasks import redis_task
from .models import BulletinNotes, Note, Inscription, Evaluation

logger = logging.getLogger(__name__)


@redis_task("academic.generer_bulletin")
def generer_bulletin_pdf(bulletin_id):
    """
    Générer le PDF du bulletin scolaire en arrière-plan
    """
    try:
        from xhtml2pdf import pisa
        from django.shortcuts import get_object_or_404
        
        bulletin = get_object_or_404(BulletinNotes, id=bulletin_id)
        inscription = bulletin.inscription
        eleve = inscription.eleve
        classe = inscription.classe
        
        # Récupérer les notes
        notes = Note.objects.filter(inscription=inscription, periode=bulletin.periode)
        
        # Calculer les totaux
        total_coefficients = sum(n.coefficient for n in notes)
        total_points = sum(n.note * n.coefficient for n in notes)
        
        # Rendre le template
        html_content = render_to_string('bulletins/bulletin_benin_template.html', {
            'bulletin': bulletin,
            'eleve': eleve,
            'inscription': inscription,
            'classe': classe,
            'notes': notes,
            'total_coefficients': total_coefficients,
            'total_points': total_points,
            'etablissement': classe.etablissement,
        })
        
        # Générer PDF
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content.encode('utf-8'), dest=pdf_buffer)
        pdf_buffer.seek(0)
        
        # Sauvegarder
        filename = f"bulletin_{eleve.last_name}_{bulletin.periode}.pdf"
        bulletin.fichier_pdf.save(filename, File(pdf_buffer))
        bulletin.is_genere = True
        bulletin.save()
        
        logger.info(f"✅ Bulletin PDF généré: {filename}")
        
        # Notifier l'élève
        from notifications.utils import send_notification
        send_notification.delay(
            user_id=eleve.id,
            title="Bulletin disponible",
            message=f"Votre bulletin du {bulletin.get_periode_display()} est disponible"
        )
        
        return f"Bulletin généré: {filename}"
        
    except Exception as e:
        logger.error(f"❌ Erreur génération bulletin {bulletin_id}: {e}")
        raise


@redis_task("academic.calculer_moyennes_classe")
def calculer_moyennes_classe(classe_id, periode):
    """
    Calculer les moyennes de toute une classe
    """
    try:
        from django.shortcuts import get_object_or_404
        from schools.models import Classe
        
        classe = get_object_or_404(Classe, id=classe_id)
        inscriptions = Inscription.objects.filter(classe=classe, is_active=True)
        
        moyennes = []
        
        for inscription in inscriptions:
            notes = Note.objects.filter(inscription=inscription, periode=periode)
            
            if notes.exists():
                total_points = sum(n.note * n.coefficient for n in notes)
                total_coef = sum(n.coefficient for n in notes)
                moyenne = total_points / total_coef if total_coef > 0 else 0
                
                # Mettre à jour ou créer le bulletin
                bulletin, created = BulletinNotes.objects.update_or_create(
                    inscription=inscription,
                    periode=periode,
                    defaults={
                        'moyenne_generale': moyenne,
                        'nombre_matiere': notes.count(),
                    }
                )
                
                moyennes.append((inscription.eleve.id, moyenne))
        
        # Trier pour déterminer les rangs
        moyennes.sort(key=lambda x: x[1], reverse=True)
        
        for rang, (eleve_id, moyenne) in enumerate(moyennes, 1):
            BulletinNotes.objects.filter(
                inscription__eleve_id=eleve_id,
                periode=periode
            ).update(rang=rang, effectif_classe=len(moyennes))
        
        logger.info(f"✅ Moyennes calculées pour {len(moyennes)} élèves de {classe.nom}")
        return f"{len(moyennes)} bulletins mis à jour"
        
    except Exception as e:
        logger.error(f"❌ Erreur calcul moyennes classe {classe_id}: {e}")
        raise


@redis_task("academic.notifier_nouvelle_note")
def notifier_nouvelle_note(note_id):
    """
    Notifier l'élève et les parents d'une nouvelle note
    """
    try:
        from django.shortcuts import get_object_or_404
        from parents.models import NotificationParent
        
        note = get_object_or_404(Note, id=note_id)
        eleve = note.inscription.eleve
        matiere = note.matiere
        
        # Notification à l'élève
        from notifications.utils import send_notification
        send_notification.delay(
            user_id=eleve.id,
            title=f"Nouvelle note - {matiere.nom}",
            message=f"Vous avez obtenu {note.note}/20 en {matiere.nom}"
        )
        
        # Notifications aux parents
        parents = eleve.parents.all()
        for parent in parents:
            NotificationParent.objects.create(
                parent=parent,
                eleve=eleve,
                type_notification='note',
                titre=f"Nouvelle note - {eleve.get_full_name()}",
                contenu=f"{eleve.first_name} a obtenu {note.note}/20 en {matiere.nom}"
            )
            
            # Envoyer aussi notification push
            send_notification.delay(
                user_id=parent.user.id,
                title=f"Note de {eleve.first_name}",
                message=f"{note.note}/20 en {matiere.nom}"
            )
        
        logger.info(f"✅ Notifications envoyées pour note {note_id}")
        return f"Notifié: 1 élève, {parents.count()} parents"
        
    except Exception as e:
        logger.error(f"❌ Erreur notification note {note_id}: {e}")
        raise


@redis_task("academic.calculer_statistiques_trimestre")
def calculer_statistiques_trimestre(etablissement_id, periode):
    """
    Calculer les statistiques pédagogiques d'un trimestre
    """
    try:
        from django.shortcuts import get_object_or_404
        from schools.models import Etablissement
        
        etablissement = get_object_or_404(Etablissement, id=etablissement_id)
        
        # Récupérer tous les bulletins du trimestre
        bulletins = BulletinNotes.objects.filter(
            inscription__classe__etablissement=etablissement,
            periode=periode,
            is_genere=True
        )
        
        if not bulletins.exists():
            return "Aucun bulletin généré pour cette période"
        
        # Statistiques globales
        moyennes = [b.moyenne_generale for b in bulletins]
        moyenne_generale = sum(moyennes) / len(moyennes)
        taux_reussite = sum(1 for m in moyennes if m >= 10) / len(moyennes) * 100
        
        # Par classe
        classes_stats = {}
        for bulletin in bulletins:
            classe_nom = bulletin.inscription.classe.nom
            if classe_nom not in classes_stats:
                classes_stats[classe_nom] = []
            classes_stats[classe_nom].append(bulletin.moyenne_generale)
        
        # Sauvegarder les statistiques
        stats = {
            'periode': periode,
            'total_eleves': len(moyennes),
            'moyenne_generale': round(moyenne_generale, 2),
            'taux_reussite': round(taux_reussite, 2),
            'moyenne_plus_haute': max(moyennes),
            'moyenne_plus_basse': min(moyennes),
            'par_classe': {c: round(sum(m)/len(m), 2) for c, m in classes_stats.items()}
        }
        
        logger.info(f"✅ Statistiques {periode}: Moy={moyenne_generale:.2f}, Réussite={taux_reussite:.1f}%")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur statistiques trimestre: {e}")
        raise
