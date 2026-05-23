#!/usr/bin/env python
"""
Script de configuration des plans d'abonnement de démo
À exécuter après les migrations
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from schools.models import Etablissement
from payments.models import (
    PlanAbonnementScolaire, ConfigurationFedaPay, PromotionAbonnement
)

def creer_plans_demo():
    """Créer les plans d'abonnement de démo"""
    
    print("🎓 Configuration des plans d'abonnement...")
    
    # Récupérer ou créer un établissement
    etablissement, created = Etablissement.objects.get_or_create(
        nom='Lycée Technique de Cotonou',
        defaults={
            'code': 'LTC-001',
            'adresse': 'Cotonou, Bénin',
            'telephone': '+229 21 00 00 00',
            'email': 'contact@ltc.bj',
            'is_actif': True,
        }
    )
    
    if created:
        print(f"✅ Établissement créé: {etablissement.nom}")
    else:
        print(f"ℹ️ Établissement existant: {etablissement.nom}")
    
    # Configuration FedaPay (Production avec la clé fournie)
    # Clé API publique : pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0
    config, created = ConfigurationFedaPay.objects.get_or_create(
        etablissement=etablissement,
        defaults={
            'environnement': 'production',  # Utilisation de la clé live fournie
            'cle_api_publique': 'pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0',  # Clé fournie par l'utilisateur
            'cle_api_secrete': '',  # À configurer manuellement pour sécurité
            'nom_marchand': 'Académie Numérique - LTC',
            'email_marchand': 'paiements@academie-ltc.bj',
            'webhook_secret': 'whsec_' + os.urandom(16).hex(),
            'is_actif': True,
        }
    )
    
    # Si la config existe déjà, mettre à jour avec la clé live
    if not created:
        config.cle_api_publique = 'pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0'
        config.environnement = 'production'
        config.save()
        print("ℹ️ Configuration FedaPay mise à jour avec la clé live")
    
    if created:
        print(f"✅ Configuration FedaPay créée (Sandbox)")
    else:
        print(f"ℹ️ Configuration FedaPay existante")
    
    # Plan Essentiel
    plan_essentiel, created = PlanAbonnementScolaire.objects.get_or_create(
        slug='essentiel',
        defaults={
            'etablissement': etablissement,
            'nom': 'Essentiel',
            'niveau': 'basique',
            'type_plan': 'mensuel',
            'prix_mensuel': 5000,
            'prix_annuel': 48000,
            'reduction_annuelle_pourcentage': 20,
            'description_courte': 'Parfait pour débuter votre apprentissage',
            'description_complete': 'Accès aux fonctionnalités essentielles pour démarrer votre parcours éducatif.',
            'features': [
                'Accès aux cours vidéos',
                '5 compositions par mois',
                'Certificats PDF',
                'Support par email',
            ],
            'limitations': [
                'Pas de correction IA avancée',
                'Pas de coaching personnalisé',
            ],
            'duree_jours': 30,
            'ordre_affichage': 1,
            'couleur': '#64748b',
            'icone': '📚',
            'is_actif': True,
            'visible_sur_site': True,
        }
    )
    print(f"{'✅ Créé' if created else 'ℹ️ Existe'}: Plan Essentiel (5,000 FCFA/mois)")
    
    # Plan Standard (Populaire)
    plan_standard, created = PlanAbonnementScolaire.objects.get_or_create(
        slug='standard',
        defaults={
            'etablissement': etablissement,
            'nom': 'Standard',
            'niveau': 'standard',
            'type_plan': 'mensuel',
            'prix_mensuel': 10000,
            'prix_annuel': 96000,
            'reduction_annuelle_pourcentage': 20,
            'description_courte': 'Le choix des élèves sérieux',
            'description_complete': 'Notre plan le plus populaire avec toutes les fonctionnalités essentielles plus la correction IA.',
            'features': [
                'Tout du plan Essentiel',
                'Compositions illimitées',
                'Correction IA avancée',
                'Rapports détaillés',
                'Support prioritaire',
            ],
            'duree_jours': 30,
            'ordre_affichage': 2,
            'couleur': '#3b82f6',
            'icone': '⭐',
            'is_populaire': True,
            'is_actif': True,
            'visible_sur_site': True,
        }
    )
    print(f"{'✅ Créé' if created else 'ℹ️ Existe'}: Plan Standard (10,000 FCFA/mois) - POPULAIRE")
    
    # Plan Premium
    plan_premium, created = PlanAbonnementScolaire.objects.get_or_create(
        slug='premium',
        defaults={
            'etablissement': etablissement,
            'nom': 'Premium',
            'niveau': 'premium',
            'type_plan': 'mensuel',
            'prix_mensuel': 15000,
            'prix_annuel': 144000,
            'reduction_annuelle_pourcentage': 20,
            'description_courte': 'Pour une excellence totale',
            'description_complete': 'Accès complet avec coaching personnalisé et certifications premium.',
            'features': [
                'Tout du plan Standard',
                'Coaching personnalisé (2h/mois)',
                'Accès prioritaire au support 24/7',
                'Certificats premium holographiques',
                'Préparation aux examens officiels',
                'Bibliothèque numérique illimitée',
            ],
            'duree_jours': 30,
            'ordre_affichage': 3,
            'couleur': '#8b5cf6',
            'icone': '🚀',
            'is_recommande': True,
            'is_actif': True,
            'visible_sur_site': True,
        }
    )
    print(f"{'✅ Créé' if created else 'ℹ️ Existe'}: Plan Premium (15,000 FCFA/mois)")
    
    # Plan Famille
    plan_famille, created = PlanAbonnementScolaire.objects.get_or_create(
        slug='famille',
        defaults={
            'etablissement': etablissement,
            'nom': 'Famille',
            'niveau': 'elite',
            'type_plan': 'mensuel',
            'prix_mensuel': 25000,
            'prix_annuel': 240000,
            'reduction_annuelle_pourcentage': 20,
            'description_courte': 'Jusqu\'à 4 membres de la famille',
            'description_complete': 'Idéal pour les familles avec plusieurs enfants. Économisez jusqu\'à 60% par rapport aux abonnements individuels.',
            'features': [
                '4 comptes élèves séparés',
                'Toutes les fonctionnalités Premium',
                'Dashboard parent avancé',
                'Rapports familiaux comparatifs',
                'Réductions sur certifications',
                'Support familial dédié',
            ],
            'duree_jours': 30,
            'ordre_affichage': 4,
            'couleur': '#10b981',
            'icone': '👨‍👩‍👧‍👦',
            'badge_special': 'Économisez 60%',
            'is_actif': True,
            'visible_sur_site': True,
        }
    )
    print(f"{'✅ Créé' if created else 'ℹ️ Existe'}: Plan Famille (25,000 FCFA/mois)")
    
    # Promotion de rentrée
    promo, created = PromotionAbonnement.objects.get_or_create(
        code_promo='RENTREE2024',
        defaults={
            'etablissement': etablissement,
            'nom': 'Offre de Rentrée 2024',
            'description': '1 mois gratuit sur votre premier abonnement',
            'type_reduction': 'pourcentage',
            'valeur_reduction': 50,  # 50% de réduction = 1 mois gratuit sur abonnement annuel
            'date_debut': timezone.now(),
            'date_fin': timezone.now() + timedelta(days=60),
            'nombre_utilisations_max': 100,
            'couleur_badge': '#ef4444',
            'is_actif': True,
        }
    )
    
    # Associer tous les plans à la promotion
    if created:
        promo.plans_applicables.add(plan_essentiel, plan_standard, plan_premium)
        print(f"✅ Promotion RENTREE2024 créée (50% de réduction)")
    else:
        print(f"ℹ️ Promotion RENTREE2024 existe déjà")
    
    print("\n" + "="*60)
    print("🎉 CONFIGURATION TERMINÉE")
    print("="*60)
    print(f"\n📊 Récapitulatif:")
    print(f"   • 4 plans d'abonnement créés")
    print(f"   • Configuration FedaPay (Sandbox)")
    print(f"   • 1 promotion active (RENTREE2024)")
    print(f"\n💰 Tarifs:")
    print(f"   • Essentiel: 5,000 FCFA/mois ou 48,000 FCFA/an")
    print(f"   • Standard: 10,000 FCFA/mois ou 96,000 FCFA/an ⭐ POPULAIRE")
    print(f"   • Premium: 15,000 FCFA/mois ou 144,000 FCFA/an")
    print(f"   • Famille: 25,000 FCFA/mois ou 240,000 FCFA/an")
    print(f"\n📝 Prochaines étapes:")
    print(f"   1. Remplacer les clés API FedaPay dans l'admin")
    print(f"   2. Télécharger les images publicitaires")
    print(f"   3. Tester le paiement avec les cartes de test FedaPay")
    print(f"   4. Configurer l'URL du webhook dans FedaPay Dashboard")
    print(f"\n🔗 URL Webhook à configurer:")
    print(f"   https://votre-domaine.com/payments/webhook/fedapay/")
    print("="*60)

if __name__ == '__main__':
    creer_plans_demo()
