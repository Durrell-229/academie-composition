from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import json

# Importer tous les modèles nécessaires
from core.models import Matiere, Classe
from accounts.models import User
from notifications.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Synchroniser TOUTES les données de local vers production'

    def handle(self, *args, **options):
        self.stdout.write('🚀 DÉBUT SYNCHRONISATION COMPLÈTE...')
        
        with transaction.atomic():
            # 1. CRÉATION UTILISATEURS
            self.stdout.write('\n👥 1/8 - CRÉATION DES UTILISATEURS...')
            self.create_users()
            
            # 2. CRÉATION MATIÈRES
            self.stdout.write('\n📚 2/8 - CRÉATION DES MATIÈRES...')
            self.create_matieres()
            
            # 3. CRÉATION ÉTABLISSEMENTS
            self.stdout.write('\n🏫 3/8 - CRÉATION DES ÉTABLISSEMENTS...')
            self.create_etablissements()
            
            # 4. CRÉATION NIVEAUX
            self.stdout.write('\n📊 4/8 - CRÉATION DES NIVEAUX SCOLAIRES...')
            self.create_niveaux()
            
            # 5. CRÉATION ANNÉES SCOLAIRES
            self.stdout.write('\n📅 5/8 - CRÉATION DES ANNÉES SCOLAIRES...')
            self.create_annees()
            
            # 6. CRÉATION CLASSES
            self.stdout.write('\n🏫 6/8 - CRÉATION DES CLASSES...')
            self.create_classes()
            
            # 7. CRÉATION PROMOTIONS
            self.stdout.write('\n🎓 7/8 - CRÉATION DES PROMOTIONS...')
            self.create_promotions()
            
            # 8. CRÉATION INSCRIPTIONS
            self.stdout.write('\n✍️ 8/8 - CRÉATION DES INSCRIPTIONS...')
            self.create_inscriptions()
            
            # 9. ASSOCIATION MATIÈRES-CLASSES
            self.stdout.write('\n🔗 9/8 - ASSOCIATION MATIÈRES-CLASSES...')
            self.create_matieres_classes()
            
            # 10. CRÉATION ÉPREUVES
            self.stdout.write('\n📝 10/8 - CRÉATION DES ÉPREUVES...')
            self.create_epreuves()
            
            # 11. CRÉATION QCM
            self.stdout.write('\n✅ 11/8 - CRÉATION DES QCM...')
            self.create_qcm()
            
            # 12. CRÉATION NOTIFICATIONS
            self.stdout.write('\n🔔 12/8 - CRÉATION DES NOTIFICATIONS...')
            self.create_notifications()
        
        self.stdout.write('\n✅ SYNCHRONISATION TERMINÉE AVEC SUCCÈS!')
        self.stdout.write('🎉 Toutes les données ont été recréées dans la base de production!')

    def create_users(self):
        """Créer les utilisateurs de base"""
        users_data = [
            {
                'email': 'admin@academie-numerique.fr',
                'first_name': 'Admin',
                'last_name': 'Système',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'password': 'admin2025'
            },
            {
                'email': 'prof.maths@academie-numerique.fr',
                'first_name': 'Jean',
                'last_name': 'Dupont',
                'role': 'professeur',
                'password': 'prof2026'
            },
            {
                'email': 'eleve.test@academie-numerique.fr',
                'first_name': 'Marie',
                'last_name': 'Martin',
                'role': 'eleve',
                'password': 'eleve2026'
            }
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'  ✅ Utilisateur créé: {user.get_full_name()}')

    def create_matieres(self):
        """Créer toutes les matières"""
        matieres_data = [
            ('MATHS', 'Mathématiques', '#6366F1', 'fa-calculator', 'Enseignement des mathématiques'),
            ('PC', 'Physique-Chimie', '#F59E0B', 'fa-flask', 'Enseignement de physique-chimie'),
            ('SVT', 'Sciences de la Vie et de la Terre', '#10B981', 'fa-leaf', 'Enseignement des SVT'),
            ('FRANCAIS', 'Français', '#3B82F6', 'fa-book', 'Enseignement du français'),
            ('ANGLAIS', 'Anglais', '#06B6D4', 'fa-language', 'Enseignement de l\'anglais'),
            ('HIST_GEO', 'Histoire et Géographie', '#8B5CF6', 'fa-globe', 'Enseignement d\'histoire-géo'),
            ('PHILO', 'Philosophie', '#EC4899', 'fa-brain', 'Enseignement de la philosophie'),
            ('ESPAGNOL', 'Espagnol', '#F59E0B', 'fa-comments', 'Enseignement de l\'espagnol'),
            ('ALLEMAND', 'Allemand', '#6B7280', 'fa-comments', 'Enseignement de l\'allemand'),
            ('TIC', 'Technologie de l\'Information et de la Communication', '#6366F1', 'fa-laptop', 'Enseignement des TIC'),
            ('EPS', 'Éducation Physique et Sportive', '#10B981', 'fa-running', 'Enseignement de l\'EPS'),
            ('MUSIQUE', 'Musique', '#F59E0B', 'fa-music', 'Enseignement de la musique'),
            ('ARTS', 'Arts Plastiques', '#3B82F6', 'fa-palette', 'Enseignement des arts'),
            ('ECO', 'Économie', '#8B5CF6', 'fa-chart-line', 'Enseignement de l\'économie'),
        ]
        
        for code, nom, couleur, icone, description in matieres_data:
            matiere, created = Matiere.objects.get_or_create(
                code=code,
                defaults={
                    'nom': nom,
                    'couleur': couleur,
                    'icone': icone,
                    'niveaux': ['primaire', 'secondaire', 'universitaire'],
                    'description': description
                }
            )
            if created:
                self.stdout.write(f'  ✅ Matière créée: {nom}')

    def create_etablissements(self):
        """Créer les établissements"""
        etablissements_data = [
            {
                'code': 'ETAB001',
                'nom': 'Lycée Numérique Académie',
                'type': 'public',
                'adresse': '123 Avenue de l\'Éducation',
                'ville': 'Paris',
                'pays': 'France',
                'telephone': '+33123456789',
                'email': 'contact@lycee-numerique.fr',
                'site_web': 'https://academie-composition.onrender.com'
            },
            {
                'code': 'ETAB002',
                'nom': 'École Primaire Numérique',
                'type': 'public',
                'adresse': '45 Rue des Écoles',
                'ville': 'Lyon',
                'pays': 'France',
                'telephone': '+33456789012',
                'email': 'contact@ecole-primaire.fr',
                'site_web': 'https://ecole-primaire.academie.fr'
            }
        ]
        
        for etab_data in etablissements_data:
            etablissement, created = Etablissement.objects.get_or_create(
                code=etab_data['code'],
                defaults=etab_data
            )
            if created:
                self.stdout.write(f'  ✅ Établissement créé: {etablissement.nom}')

    def create_niveaux(self):
        """Créer les niveaux scolaires"""
        niveaux_data = [
            ('PRIMAIRE', 'Primaire'),
            ('SECONDAIRE', 'Secondaire'),
            ('UNIVERSITAIRE', 'Universitaire'),
            ('PROFESSIONNEL', 'Formation Professionnelle'),
        ]
        
        for code, nom in niveaux_data:
            niveau, created = NiveauScolaire.objects.get_or_create(
                code=code,
                defaults={'nom': nom}
            )
            if created:
                self.stdout.write(f'  ✅ Niveau créé: {nom}')

    def create_annees(self):
        """Créer les années scolaires"""
        annees_data = [
            ('2024-2025', '2024-2025'),
            ('2025-2026', '2025-2026'),
            ('2026-2027', '2026-2027'),
        ]
        
        for code, nom in annees_data:
            annee, created = AnneeScolaire.objects.get_or_create(
                code=code,
                defaults={'nom': nom}
            )
            if created:
                self.stdout.write(f'  ✅ Année créée: {nom}')

    def create_classes(self):
        """Créer les classes"""
        classes_data = [
            ('6E', 'SECONDAIRE', '6ème', '2024-2025'),
            ('5E', 'SECONDAIRE', '5ème', '2024-2025'),
            ('4E', 'SECONDAIRE', '4ème', '2024-2025'),
            ('3E', 'SECONDAIRE', '3ème', '2024-2025'),
            ('2NDE_A', 'SECONDAIRE', '2nde A', '2024-2025'),
            ('2NDE_C', 'SECONDAIRE', '2nde C', '2024-2025'),
            ('1ERE_S', 'SECONDAIRE', '1ère S', '2024-2025'),
            ('1ERE_ES', 'SECONDAIRE', '1ère ES', '2024-2025'),
            ('TLE_S', 'SECONDAIRE', 'Terminale S', '2024-2025'),
            ('TLE_ES', 'SECONDAIRE', 'Terminale ES', '2024-2025'),
            ('L1', 'UNIVERSITAIRE', 'Licence 1', '2024-2025'),
            ('L2', 'UNIVERSITAIRE', 'Licence 2', '2024-2025'),
            ('L3', 'UNIVERSITAIRE', 'Licence 3', '2024-2025'),
        ]
        
        for code, niveau, nom, annee in classes_data:
            classe, created = Classe.objects.get_or_create(
                code=code,
                defaults={
                    'nom': nom,
                    'niveau': niveau,
                    'annee_academique': annee,
                }
            )
            if created:
                self.stdout.write(f'  ✅ Classe créée: {nom}')

    def create_promotions(self):
        """Créer les promotions"""
        etablissement = Etablissement.objects.first()
        if not etablissement:
            etablissement = Etablissement.objects.create(
                code='ETAB001',
                nom='Établissement par défaut'
            )
        
        promotions_data = [
            ('PROMO2024', 'Promotion 2024-2028', '2024', '2028'),
            ('PROMO2025', 'Promotion 2025-2029', '2025', '2029'),
        ]
        
        for code, nom, annee_entree, annee_sortie in promotions_data:
            promo, created = Promotion.objects.get_or_create(
                code=code,
                defaults={
                    'etablissement': etablissement,
                    'nom': nom,
                    'annee_entree': annee_entree,
                    'annee_sortie': annee_sortie,
                    'nombre_eleves': 30,
                    'nombre_diplomes': 25,
                }
            )
            if created:
                self.stdout.write(f'  ✅ Promotion créée: {nom}')

    def create_inscriptions(self):
        """Créer les inscriptions"""
        promotion = Promotion.objects.first()
        classes = Classe.objects.all()[:5]  # 5 premières classes
        eleve = User.objects.filter(role='eleve').first()
        
        if not eleve:
            return
            
        for i, classe in enumerate(classes):
            inscription, created = Inscription.objects.get_or_create(
                eleve=eleve,
                classe=classe,
                defaults={
                    'promotion': promotion,
                    'date_inscription': '2024-09-01',
                    'statut': 'inscrite',
                    'moyenne_generale': 12.5 + i,
                }
            )
            if created:
                self.stdout.write(f'  ✅ Inscription créée: {eleve.get_full_name()} - {classe.nom}')

    def create_matieres_classes(self):
        """Associer les matières aux classes"""
        classes = Classe.objects.all()
        matieres = Matiere.objects.all()
        
        for classe in classes:
            for matiere in matieres[:6]:  # 6 premières matières
                matiere_classe, created = MatiereClasse.objects.get_or_create(
                    classe=classe,
                    matiere=matiere,
                    defaults={
                        'coefficient': 1.0,
                        'heures_semaine': 2,
                        'pourcentage_programme': 50,
                    }
                )
                if created:
                    self.stdout.write(f'  ✅ {matiere.nom} associée à {classe.nom}')

    def create_epreuves(self):
        """Créer des épreuves d'exemple"""
        professeur = User.objects.filter(role='professeur').first()
        if not professeur:
            return
            
        epreuves_data = [
            {
                'titre': 'Évaluation Mathématiques - Trigonométrie',
                'description': 'Évaluation sur les fonctions trigonométriques et leurs applications',
                'duree': 120,
                'type_epreuve': 'examen',
                'statut': 'brouillon',
            },
            {
                'titre': 'Composition Française - Analyse de texte',
                'description': 'Analyse de texte et rédaction argumentée',
                'duree': 180,
                'type_epreuve': 'composition',
                'statut': 'publie',
            },
            {
                'titre': 'QCM Sciences Physiques',
                'description': 'Questionnaire à choix multiples sur les sciences physiques',
                'duree': 60,
                'type_epreuve': 'qcm',
                'statut': 'publie',
            }
        ]
        
        for epreuve_data in epreuves_data:
            epreuve, created = Epreuve.objects.get_or_create(
                titre=epreuve_data['titre'],
                createur=professeur,
                defaults=epreuve_data
            )
            if created:
                self.stdout.write(f'  ✅ Épreuve créée: {epreuve.titre}')

    def create_qcm(self):
        """Créer des QCM d'exemple"""
        professeur = User.objects.filter(role='professeur').first()
        if not professeur:
            return
            
        qcm_data = [
            {
                'titre': 'QCM Mathématiques - Algèbre',
                'description': 'Test sur les équations algébriques',
                'nombre_questions': 10,
                'duree': 30,
                'points_par_question': 1,
            },
            {
                'titre': 'QCM Histoire - Révolution Française',
                'description': 'Test sur la période révolutionnaire',
                'nombre_questions': 15,
                'duree': 45,
                'points_par_question': 1,
            }
        ]
        
        for qcm_info in qcm_data:
            qcm, created = QCM.objects.get_or_create(
                titre=qcm_info['titre'],
                createur=professeur,
                defaults=qcm_info
            )
            if created:
                self.stdout.write(f'  ✅ QCM créé: {qcm.titre}')

    def create_notifications(self):
        """Créer des notifications d'exemple"""
        users = User.objects.all()
        
        notifications_data = [
            {
                'title': '🎉 Bienvenue sur l\'Académie Numérique',
                'message': 'Votre compte a été créé avec succès. Découvrez toutes nos fonctionnalités.',
                'type': 'INFO',
            },
            {
                'title': '📚 Nouvelle épreuve disponible',
                'message': 'Une nouvelle épreuve de mathématiques a été publiée.',
                'type': 'INFO',
            },
            {
                'title': '🔔 Rappel de devoir',
                'message': 'N\'oubliez pas de soumettre votre composition avant demain.',
                'type': 'WARNING',
            }
        ]
        
        for user in users:
            for notif_data in notifications_data:
                notification, created = Notification.objects.get_or_create(
                    recipient=user,
                    title=notif_data['title'],
                    defaults={
                        'message': notif_data['message'],
                        'type': notif_data['type'],
                    }
                )
                if created:
                    self.stdout.write(f'  ✅ Notification créée pour {user.get_full_name()}: {notif_data["title"]}')
