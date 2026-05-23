#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def fix_duplicate_matieres():
    """Corriger les matières en double et finaliser la configuration béninoise"""
    print("🔧 CORRECTION MATIÈRES EN DOUBLE + FINALISATION BÉNIN")
    print("=" * 60)
    
    try:
        from core.models import Matiere
        from django.db import transaction
        
        # 1. Nettoyer les matières en double
        print("🧹 Nettoyage des matières en double...")
        
        # Liste des matières potentiellement en double
        matiere_names = [
            "Français", "Mathématiques", "Histoire-Géographie", "Anglais", 
            "Physique-Chimie", "Sciences de la Vie et de la Terre"
        ]
        
        for matiere_name in matiere_names:
            matieres = Matiere.objects.filter(nom=matiere_name)
            if matieres.count() > 1:
                print(f"📋 {matieres.count()} copies trouvées pour: {matiere_name}")
                # Garder la première, supprimer les autres
                first = matieres.first()
                others = matieres.exclude(id=first.id)
                for other in others:
                    print(f"   ❌ Suppression: {other.code}")
                    other.delete()
                print(f"   ✅ Conservé: {first.code}")
        
        # 2. Ajouter les matières manquantes avec codes uniques
        print("\n➕ Ajout des matières manquantes...")
        
        benin_matieres = [
            {"nom": "Sciences de la Vie et de la Terre", "code": "SVT", "coefficient": 2, "description": "Biologie"},
            {"nom": "Instruction Civique et Morale", "code": "ICM", "coefficient": 1, "description": "Éducation civique"},
            {"nom": "Sciences Physiques", "code": "SP", "coefficient": 5, "description": "Physique-Chimie approfondie"},
            {"nom": "Sciences Naturelles", "code": "SN", "coefficient": 5, "description": "Biologie approfondie"},
            {"nom": "Philosophie", "code": "PHILO", "coefficient": 4, "description": "Philosophie"},
            {"nom": "Littérature", "code": "LITT", "coefficient": 3, "description": "Littérature française"},
            {"nom": "Latin", "code": "LAT", "coefficient": 2, "description": "Langue latine"},
            {"nom": "Économie", "code": "ECO", "coefficient": 4, "description": "Sciences économiques"},
            {"nom": "Droit", "code": "DROIT", "coefficient": 3, "description": "Droit constitutionnel"},
            {"nom": "Comptabilité", "code": "COMPTA", "coefficient": 3, "description": "Comptabilité générale"},
            {"nom": "Arts Plastiques", "code": "ART", "coefficient": 1, "description": "Éducation artistique"},
            {"nom": "Éducation Musicale", "code": "MUSIQUE", "coefficient": 1, "description": "Éducation musicale"},
            {"nom": "Éducation Physique et Sportive", "code": "EPS", "coefficient": 1, "description": "Sports"},
            {"nom": "Technologie", "code": "TECH", "coefficient": 1, "description": "Technologie"},
            {"nom": "Informatique", "code": "INFO", "coefficient": 1, "description": "Bureautique et programmation"},
        ]
        
        with transaction.atomic():
            for matiere_data in benin_matieres:
                try:
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
                except Exception as e:
                    print(f"⚠️ Erreur avec {matiere_data['nom']}: {e}")
        
        # 3. Finaliser la configuration des examens nationaux
        print("\n🎓 Finalisation des examens nationaux...")
        
        from exams.models import ExamenNational, ExamenNationalMatiere
        from core.models import Classe
        from accounts.models import User
        from datetime import date, timedelta
        
        # Récupérer l'admin
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            admin_user = User.objects.create_user(
                email='admin@benin.edu',
                password='admin2026',
                first_name='Administrateur',
                last_name='Système',
                role='admin'
            )
        
        # Configurations des examens
        examens_config = [
            {
                "nom": "BEPC - Brevet d'Études du Premier Cycle",
                "type_examen": "bepc",
                "classe": "3ème",
                "matieres": ["Français", "Mathématiques", "Histoire-Géographie", "Anglais", "Physique-Chimie", "Sciences de la Vie et de la Terre", "Instruction Civique et Morale"],
                "coefficients": {"Français": 3, "Mathématiques": 3, "Histoire-Géographie": 2, "Anglais": 2, "Physique-Chimie": 2, "Sciences de la Vie et de la Terre": 2, "Instruction Civique et Morale": 1}
            },
            {
                "nom": "BACCALAURÉAT Série C",
                "type_examen": "bac_c",
                "classe": "Terminale C",
                "matieres": ["Français", "Philosophie", "Anglais", "Mathématiques", "Sciences Physiques", "Sciences Naturelles"],
                "coefficients": {"Français": 3, "Philosophie": 3, "Anglais": 2, "Mathématiques": 5, "Sciences Physiques": 5, "Sciences Naturelles": 5}
            }
        ]
        
        with transaction.atomic():
            for examen_data in examens_config:
                # Créer l'examen
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
                    
                    # Associer la classe
                    classe = Classe.objects.get(nom=examen_data["classe"])
                    examen.classes.add(classe)
                    
                    # Associer les matières et créer les épreuves
                    for matiere_nom in examen_data["matieres"]:
                        try:
                            matiere = Matiere.objects.get(nom=matiere_nom)
                            examen.matieres.add(matiere)
                            
                            ExamenNationalMatiere.objects.get_or_create(
                                examen=examen,
                                matiere=matiere,
                                defaults={
                                    "statut": "valide"
                                }
                            )
                        except Matiere.DoesNotExist:
                            print(f"⚠️ Matière non trouvée: {matiere_nom}")
                else:
                    print(f"📋 Examen existant: {examen.nom}")
        
        # 4. Créer un bulletin type béninois
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
                    "matieres": True,
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
        
        from core.models import Parametre
        param, created = Parametre.objects.get_or_create(
            cle="bulletin_benin_config",
            defaults={"valeur": str(bulletin_config)}
        )
        
        if created:
            print("✅ Configuration bulletin béninois créée")
        else:
            print("📋 Configuration bulletin existante")
        
        # 5. Sauvegarder les coefficients
        print("\n⚙️ Sauvegarde des coefficients béninois...")
        
        coefficients_map = {m["nom"]: m["coefficient"] for m in benin_matieres}
        
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
        
        print("\n🎉 SYSTÈME ÉDUCATIF BÉNINOIS FINALISÉ!")
        print("\n📊 RÉCAPITULATIF:")
        
        classe_count = Classe.objects.count()
        matiere_count = Matiere.objects.count()
        examen_count = ExamenNational.objects.count()
        
        print(f"✅ {classe_count} classes configurées")
        print(f"✅ {matiere_count} matières configurées")
        print(f"✅ {examen_count} examens nationaux configurés")
        print(f"✅ Bulletins adaptés au format béninois")
        print(f"✅ Coefficients béninois appliqués")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_duplicate_matieres()
    if success:
        print("\n🇧🇯 Le système est maintenant 100% adapté au contexte éducatif béninois!")
        print("📚 Vous pouvez créer des examens et devoirs selon les standards béninois")
        print("🎓 Les examens nationaux (BEPC, BACC) sont configurés")
        print("📄 Les bulletins suivent le format officiel béninois")
    else:
        print("\n❌ Échec de la finalisation")
