#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def setup_benin_education_system():
    """Configurer le système éducatif béninois complet"""
    print("🇧🇯 CONFIGURATION SYSTÈME ÉDUCATIF BÉNINOIS")
    print("=" * 60)
    
    try:
        from core.models import Matiere, Classe
        from accounts.models import User
        from django.db import transaction
        
        # 1. Configurer les classes et niveaux du système béninois
        print("📚 Configuration des classes et niveaux...")
        
        benin_classes = [
            # PRIMAIRE
            {"nom": "CP", "niveau": "Primaire"},
            {"nom": "CE1", "niveau": "Primaire"},
            {"nom": "CE2", "niveau": "Primaire"},
            {"nom": "CM1", "niveau": "Primaire"},
            {"nom": "CM2", "niveau": "Primaire"},
            
            # COLLÈGE (CYCLE D'ORIENTATION)
            {"nom": "6ème", "niveau": "Secondaire"},
            {"nom": "5ème", "niveau": "Secondaire"},
            {"nom": "4ème", "niveau": "Secondaire"},
            {"nom": "3ème", "niveau": "Secondaire"},
            
            # LYCÉE (CYCLE TERMINAL)
            {"nom": "2nde A", "niveau": "Secondaire"},
            {"nom": "2nde C", "niveau": "Secondaire"},
            {"nom": "2nde D", "niveau": "Secondaire"},
            {"nom": "1ère A1", "niveau": "Secondaire"},
            {"nom": "1ère A2", "niveau": "Secondaire"},
            {"nom": "1ère B", "niveau": "Secondaire"},
            {"nom": "1ère C", "niveau": "Secondaire"},
            {"nom": "1ère D", "niveau": "Secondaire"},
            {"nom": "Terminale A1", "niveau": "Secondaire"},
            {"nom": "Terminale A2", "niveau": "Secondaire"},
            {"nom": "Terminale B", "niveau": "Secondaire"},
            {"nom": "Terminale C", "niveau": "Secondaire"},
            {"nom": "Terminale D", "niveau": "Secondaire"},
            {"nom": "Terminale E", "niveau": "Secondaire"},
            {"nom": "Terminale G1", "niveau": "Secondaire"},
            {"nom": "Terminale G2", "niveau": "Secondaire"},
            {"nom": "Terminale G3", "niveau": "Secondaire"},
        ]
        
        with transaction.atomic():
            for classe_data in benin_classes:
                classe, created = Classe.objects.get_or_create(
                    nom=classe_data["nom"],
                    defaults={
                        "niveau": classe_data["niveau"],
                        "annee_academique": "2025-2026",
                        "is_active": True
                    }
                )
                if created:
                    print(f"✅ Classe créée: {classe.nom}")
                else:
                    print(f"📋 Classe existante: {classe.nom}")
        
        # 2. Configurer les matières avec coefficients béninois
        print("\n📖 Configuration des matières et coefficients...")
        
        benin_matieres = [
            # MATIÈRES COMMUNES
            {"nom": "Français", "code": "FR", "coefficient": 3, "description": "Langue française"},
            {"nom": "Mathématiques", "code": "MATH", "coefficient": 3, "description": "Mathématiques"},
            {"nom": "Histoire-Géographie", "code": "HG", "coefficient": 2, "description": "Histoire et Géographie"},
            {"nom": "Instruction Civique et Morale", "code": "ICM", "coefficient": 1, "description": "Éducation civique"},
            {"nom": "Anglais", "code": "ANG", "coefficient": 2, "description": "Langue anglaise"},
            {"nom": "Physique-Chimie", "code": "PC", "coefficient": 2, "description": "Physique et Chimie"},
            {"nom": "Sciences de la Vie et de la Terre", "code": "SVT", "coefficient": 2, "description": "Biologie"},
            
            # MATIÈRES SCIENTIFIQUES (Séries C, D, E)
            {"nom": "Sciences Physiques", "code": "SP", "coefficient": 5, "description": "Physique-Chimie approfondie"},
            {"nom": "Sciences Naturelles", "code": "SN", "coefficient": 5, "description": "Biologie approfondie"},
            
            # MATIÈRES LITTÉRAIRES (Séries A1, A2)
            {"nom": "Philosophie", "code": "PHILO", "coefficient": 4, "description": "Philosophie"},
            {"nom": "Littérature", "code": "LITT", "coefficient": 3, "description": "Littérature française"},
            {"nom": "Latin", "code": "LAT", "coefficient": 2, "description": "Langue latine"},
            
            # MATIÈRES ÉCONOMIQUES (Séries G1, G2, G3)
            {"nom": "Économie", "code": "ECO", "coefficient": 4, "description": "Sciences économiques"},
            {"nom": "Droit", "code": "DROIT", "coefficient": 3, "description": "Droit constitutionnel"},
            {"nom": "Comptabilité", "code": "COMPTA", "coefficient": 3, "description": "Comptabilité générale"},
            
            # AUTRES MATIÈRES
            {"nom": "Arts Plastiques", "code": "ART", "coefficient": 1, "description": "Éducation artistique"},
            {"nom": "Éducation Musicale", "code": "MUSIQUE", "coefficient": 1, "description": "Éducation musicale"},
            {"nom": "Éducation Physique et Sportive", "code": "EPS", "coefficient": 1, "description": "Sports"},
            {"nom": "Technologie", "code": "TECH", "coefficient": 1, "description": "Technologie"},
            {"nom": "Informatique", "code": "INFO", "coefficient": 1, "description": "Bureautique et programmation"},
        ]
        
        with transaction.atomic():
            for matiere_data in benin_matieres:
                matiere, created = Matiere.objects.get_or_create(
                    nom=matiere_data["nom"],
                    defaults={
                        "code": matiere_data["code"],
                        "description": matiere_data["description"],
                        "is_active": True
                    }
                )
                if created:
                    print(f"✅ Matière créée: {matiere.nom} (Coef: {matiere_data['coefficient']})")
                else:
                    print(f"📋 Matière existante: {matiere.nom}")
        
        # 3. Configurer les examens nationaux béninois
        print("\n🎓 Configuration des examens nationaux...")
        
        from exams.models import ExamenNational, ExamenNationalMatiere
        
        examens_nationaux = [
            {
                "nom": "CEP - Certificat d'Études Primaires",
                "type_examen": "cep",
                "classes": ["CM2"],
                "matieres": ["Français", "Mathématiques", "Histoire-Géographie", "Instruction Civique et Morale", "Sciences"],
                "coefficients": {"Français": 3, "Mathématiques": 3, "Histoire-Géographie": 2, "Instruction Civique et Morale": 1, "Sciences": 1}
            },
            {
                "nom": "BEPC - Brevet d'Études du Premier Cycle",
                "type_examen": "bepc",
                "classes": ["3ème"],
                "matieres": ["Français", "Mathématiques", "Histoire-Géographie", "Anglais", "Physique-Chimie", "SVT", "Instruction Civique et Morale"],
                "coefficients": {"Français": 3, "Mathématiques": 3, "Histoire-Géographie": 2, "Anglais": 2, "Physique-Chimie": 2, "SVT": 2, "Instruction Civique et Morale": 1}
            },
            {
                "nom": "BACCALAURÉAT Série A1",
                "type_examen": "bac_a1",
                "classes": ["Terminale A1"],
                "matieres": ["Français", "Philosophie", "Histoire-Géographie", "Anglais", "Mathématiques", "Littérature", "Latin"],
                "coefficients": {"Français": 4, "Philosophie": 5, "Histoire-Géographie": 3, "Anglais": 2, "Mathématiques": 2, "Littérature": 3, "Latin": 2}
            },
            {
                "nom": "BACCALAURÉAT Série A2",
                "type_examen": "bac_a2",
                "classes": ["Terminale A2"],
                "matieres": ["Français", "Philosophie", "Histoire-Géographie", "Anglais", "Mathématiques", "Littérature"],
                "coefficients": {"Français": 4, "Philosophie": 5, "Histoire-Géographie": 3, "Anglais": 2, "Mathématiques": 2, "Littérature": 3}
            },
            {
                "nom": "BACCALAURÉAT Série B",
                "type_examen": "bac_b",
                "classes": ["Terminale B"],
                "matieres": ["Français", "Philosophie", "Histoire-Géographie", "Anglais", "Mathématiques", "Économie"],
                "coefficients": {"Français": 4, "Philosophie": 4, "Histoire-Géographie": 3, "Anglais": 2, "Mathématiques": 3, "Économie": 4}
            },
            {
                "nom": "BACCALAURÉAT Série C",
                "type_examen": "bac_c",
                "classes": ["Terminale C"],
                "matieres": ["Français", "Philosophie", "Anglais", "Mathématiques", "Sciences Physiques", "Sciences Naturelles"],
                "coefficients": {"Français": 3, "Philosophie": 3, "Anglais": 2, "Mathématiques": 5, "Sciences Physiques": 5, "Sciences Naturelles": 5}
            },
            {
                "nom": "BACCALAURÉAT Série D",
                "type_examen": "bac_d",
                "classes": ["Terminale D"],
                "matieres": ["Français", "Philosophie", "Anglais", "Mathématiques", "Sciences Physiques", "Sciences Naturelles"],
                "coefficients": {"Français": 3, "Philosophie": 3, "Anglais": 2, "Mathématiques": 4, "Sciences Physiques": 4, "Sciences Naturelles": 4}
            },
            {
                "nom": "BACCALAURÉAT Série E",
                "type_examen": "bac_e",
                "classes": ["Terminale E"],
                "matieres": ["Français", "Philosophie", "Anglais", "Mathématiques", "Technologie", "Physique-Chimie"],
                "coefficients": {"Français": 3, "Philosophie": 3, "Anglais": 2, "Mathématiques": 4, "Technologie": 4, "Physique-Chimie": 4}
            },
            {
                "nom": "BACCALAURÉAT Série G1",
                "type_examen": "bac_g1",
                "classes": ["Terminale G1"],
                "matieres": ["Français", "Philosophie", "Anglais", "Mathématiques", "Économie", "Droit"],
                "coefficients": {"Français": 3, "Philosophie": 3, "Anglais": 2, "Mathématiques": 3, "Économie": 5, "Droit": 3}
            },
            {
                "nom": "BACCALAURÉAT Série G2",
                "type_examen": "bac_g2",
                "classes": ["Terminale G2"],
                "matieres": ["Français", "Philosophie", "Anglais", "Mathématiques", "Économie", "Comptabilité"],
                "coefficients": {"Français": 3, "Philosophie": 3, "Anglais": 2, "Mathématiques": 3, "Économie": 4, "Comptabilité": 4}
            },
            {
                "nom": "BACCALAURÉAT Série G3",
                "type_examen": "bac_g3",
                "classes": ["Terminale G3"],
                "matieres": ["Français", "Philosophie", "Anglais", "Mathématiques", "Économie", "Comptabilité", "Droit"],
                "coefficients": {"Français": 3, "Philosophie": 3, "Anglais": 2, "Mathématiques": 3, "Économie": 3, "Comptabilité": 3, "Droit": 3}
            },
        ]
        
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            admin_user = User.objects.create_user(
                email='admin@benin.edu',
                password='admin2026',
                first_name='Administrateur',
                last_name='Système',
                role='admin'
            )
        
        from datetime import date, timedelta
        
        with transaction.atomic():
            for examen_data in examens_nationaux:
                # Créer l'examen national
                examen, created = ExamenNational.objects.get_or_create(
                    nom=examen_data["nom"],
                    type_examen=examen_data["type_examen"],
                    defaults={
                        "annee_scolaire": "2025-2026",
                        "date_debut": date.today() + timedelta(days=30),
                        "date_fin": date.today() + timedelta(days=35),
                        "createur": admin_user,
                        "statut": "programme_publie",
                        "coefficients_par_matiere": examen_data["coefficients"]
                    }
                )
                
                if created:
                    print(f"✅ Examen créé: {examen.nom}")
                    
                    # Associer les classes
                    for classe_nom in examen_data["classes"]:
                        classe = Classe.objects.get(nom=classe_nom)
                        examen.classes.add(classe)
                    
                    # Associer les matières
                    for matiere_nom in examen_data["matieres"]:
                        matiere = Matiere.objects.get(nom=matiere_nom)
                        examen.matieres.add(matiere)
                        
                        # Créer les épreuves par matière
                        ExamenNationalMatiere.objects.get_or_create(
                            examen=examen,
                            matiere=matiere,
                            defaults={
                                "coefficient": examen_data["coefficients"].get(matiere_nom, 1),
                                "statut": "valide"
                            }
                        )
                else:
                    print(f"📋 Examen existant: {examen.nom}")
        
        # 5. Sauvegarder les coefficients béninois dans les paramètres
        print("\n⚙️ Sauvegarde des coefficients béninois...")
        
        # Mettre à jour les coefficients par défaut dans les matières
        coefficients_map = {m["nom"]: m["coefficient"] for m in benin_matieres}
        
        from core.models import Parametre
        param, created = Parametre.objects.get_or_create(
            cle="coefficients_benin",
            defaults={"valeur": str(coefficients_map)}
        )
        
        if created:
            print("✅ Coefficients béninois sauvegardés")
        else:
            param.valeur = str(coefficients_map)
            param.save()
            print("✅ Coefficients béninois mis à jour")
        
        # 5. Créer un bulletin type béninois
        print("\n📄 Configuration du bulletin type béninois...")
        
        bulletin_config = {
            "entete": {
                "republique": "RÉPUBLIQUE DU BÉNIN",
                "ministere": "MINISTÈRE DES ENSEIGNEMENTS SECONDAIRE ET SUPÉRIEUR",
                "type": "BULLETIN TRIMESTRIEL",
                "annee": "2025-2026"
            },
            "sections": [
                {
                    "titre": "INFORMATIONS ÉLÈVE",
                    "champs": ["Nom", "Prénoms", "Date de naissance", "Lieu de naissance", "Sexe", "Classe", "Matricule"]
                },
                {
                    "titre": "ÉVALUATION DES COMPÉTENCES",
                    "matieres": True,  # Utiliser les matières configurées
                    "colonnes": ["Matière", "Coefficient", "Note trimestre", "Moyenne annuelle", "Appréciation"]
                },
                {
                    "titre": "COMPORTEMENT ET DISCIPLINE",
                    "items": ["Assiduité", "Ponctualité", "Conduite", "Respect des règles", "Participation"]
                },
                {
                    "titre": "MOYENNES ET DÉCISIONS",
                    "calculs": ["Moyenne générale", "Moyenne de classe", "Rang", "Décision du conseil de classe"]
                },
                {
                    "titre": "OBSERVATIONS ET SIGNATURES",
                    "champs": ["Observations du professeur principal", "Observations des parents", "Signature du professeur principal", "Signature du parent/tuteur"]
                }
            ]
        }
        
        # Sauvegarder la configuration
        from core.models import Parametre
        param, created = Parametre.objects.get_or_create(
            cle="bulletin_benin_config",
            defaults={"valeur": str(bulletin_config)}
        )
        
        if created:
            print("✅ Configuration bulletin béninois créée")
        else:
            print("📋 Configuration bulletin existante")
        
        print("\n🎉 SYSTÈME ÉDUCATIF BÉNINOIS CONFIGURÉ!")
        print("\n📊 RÉCAPITULATIF:")
        print(f"✅ {len(benin_classes)} classes configurées")
        print(f"✅ {len(benin_matieres)} matières configurées")
        print(f"✅ {len(examens_nationaux)} examens nationaux configurés")
        print(f"✅ Bulletins adaptés au format béninois")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_benin_education_system()
    if success:
        print("\n🇧🇯 Le système est maintenant adapté au contexte éducatif béninois!")
        print("📚 Vous pouvez créer des examens et devoirs selon les standards béninois")
    else:
        print("\n❌ Échec de la configuration")
