#!/usr/bin/env python
"""
Script de configuration FedaPay en mode PRODUCTION
À exécuter après avoir reçu les clés API
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.utils import timezone
from schools.models import Etablissement
from payments.models import ConfigurationFedaPay

def configurer_fedapay_live():
    """Configurer FedaPay avec la clé API publique fournie"""
    
    print("="*70)
    print("🔐 CONFIGURATION FEDAPAY - MODE PRODUCTION")
    print("="*70)
    
    # Clé API publique (fournie par l'utilisateur)
    CLE_PUBLIQUE = 'pk_live_X_DmtE7HnbtVA7i1nmjgcXJ0'
    
    print(f"\n📋 Clé API Publique : {CLE_PUBLIQUE[:20]}...")
    print("⚠️  IMPORTANT : Cette clé est visible côté client (frontend)")
    
    # Demander la clé secrète (à ne jamais exposer)
    print("\n" + "="*70)
    print("🔑 CLÉ API SECRÈTE (SK)")
    print("="*70)
    print("⚠️  ATTENTION : La clé secrète doit rester CONFIDENTIELLE !")
    print("Elle ne doit JAMAIS être commitée dans Git ou exposée publiquement.")
    print("\nEntrez votre clé secrète FedaPay (sk_live_...):")
    print("(Appuyez sur Entrée pour sauter et configurer manuellement plus tard)")
    
    try:
        cle_secrete = input("\nClé secrète : ").strip()
    except KeyboardInterrupt:
        cle_secrete = ''
        print("\n\n❌ Configuration annulée.")
        return
    
    # Récupérer l'établissement
    etablissement = Etablissement.objects.filter(is_actif=True).first()
    
    if not etablissement:
        print("\n❌ Aucun établissement trouvé. Créez d'abord un établissement.")
        return
    
    print(f"\n🏫 Établissement : {etablissement.nom}")
    
    # Créer ou mettre à jour la configuration
    config, created = ConfigurationFedaPay.objects.update_or_create(
        etablissement=etablissement,
        defaults={
            'environnement': 'production',
            'cle_api_publique': CLE_PUBLIQUE,
            'cle_api_secrete': cle_secrete if cle_secrete else '',
            'nom_marchand': etablissement.nom,
            'email_marchand': etablissement.email or f'paiements@{etablissement.slug}.bj',
            'devise': 'XOF',
            'langue_par_defaut': 'fr',
            'is_actif': True,
        }
    )
    
    if created:
        print("\n✅ Configuration FedaPay PRODUCTION créée avec succès !")
    else:
        print("\n✅ Configuration FedaPay PRODUCTION mise à jour !")
    
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF")
    print("="*70)
    print(f"Environnement      : {config.get_environnement_display()}")
    print(f"Marchand           : {config.nom_marchand}")
    print(f"Email              : {config.email_marchand}")
    print(f"Devise             : {config.devise}")
    print(f"Statut             : {'✅ Actif' if config.is_actif else '❌ Inactif'}")
    print(f"Clé publique       : {config.cle_api_publique[:30]}...")
    print(f"Clé secrète        : {'✅ Configurée' if config.cle_api_secrete else '⚠️  Non configurée'}")
    
    print("\n" + "="*70)
    print("🚀 PROCHAINES ÉTAPES")
    print("="*70)
    print("1. ✅ Clé publique configurée")
    
    if not cle_secrete:
        print("2. ⚠️  Clé secrète : Ajoutez-la manuellement dans l'admin Django")
        print("   → /admin/payments/configurationfedapay/")
    else:
        print("2. ✅ Clé secrète configurée")
    
    print("\n3. 🌐 Configurer l'URL Webhook dans FedaPay Dashboard :")
    print(f"   → https://votre-domaine.com/payments/webhook/fedapay/")
    
    print("\n4. 🧪 Tester un paiement avec un petit montant (100 FCFA)")
    
    print("\n5. 📧 Vérifier que les emails de reçu fonctionnent")
    
    print("\n" + "="*70)
    print("⚠️  NOTES DE SÉCURITÉ IMPORTANTES")
    print("="*70)
    print("• La clé publique (pk_live_...) peut être visible côté client")
    print("• La clé secrète (sk_live_...) doit RESTER CONFIDENTIELLE")
    print("• Ne jamais committer la clé secrète dans Git")
    print("• Utiliser HTTPS obligatoirement en production")
    print("• Activer la vérification HMAC des webhooks")
    
    print("\n" + "="*70)
    print("📝 VARIABLES D'ENVIRONNEMENT (optionnel)")
    print("="*70)
    print("Pour plus de sécurité, vous pouvez utiliser des variables d'environnement :")
    print()
    print("# .env")
    print(f"FEDAPAY_PUBLIC_KEY={CLE_PUBLIQUE}")
    print("FEDAPAY_SECRET_KEY=sk_live_...")
    print()
    
    # Créer un fichier .env.example
    env_content = f"""# Configuration FedaPay - Production
FEDAPAY_PUBLIC_KEY={CLE_PUBLIQUE}
FEDAPAY_SECRET_KEY=sk_live_VOTRE_CLE_SECRETE_ICI
FEDAPAY_WEBHOOK_SECRET=whsec_{os.urandom(16).hex()}
SITE_URL=https://votre-domaine.com
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '.env.fedapay')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"💾 Fichier exemple créé : {env_path}")
    print("   Renommez-le en .env et remplissez les valeurs manquantes")
    
    print("\n✅ Configuration terminée !")
    print("="*70)

if __name__ == '__main__':
    configurer_fedapay_live()
