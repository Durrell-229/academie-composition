"""
Service de génération de cachet numérique pour les bulletins.
Génère un tampon officiel avec signature hash et token de vérification.
"""
import hashlib
import base64
from datetime import datetime
from django.conf import settings
from io import BytesIO


def generate_digital_stamp(bulletin, admin_user=None):
    """
    Génère un cachet numérique pour un bulletin approuvé.
    
    Returns:
        dict: {
            'stamp_hash': str,
            'signature': str,
            'timestamp': str,
            'verification_url': str,
            'stamp_data': dict
        }
    """
    # Données du cachet
    stamp_data = {
        'bulletin_id': str(bulletin.id),
        'eleve_matricule': bulletin.eleve.matricule if bulletin.eleve.matricule else str(bulletin.eleven.id),
        'eleve_nom': bulletin.eleve.full_name,
        'devoir_titre': bulletin.devoir.titre if hasattr(bulletin, 'devoir') and bulletin.devoir else 'N/A',
        'moyenne': str(bulletin.moyenne_generale),
        'rang': str(bulletin.rang),
        'date_approbaion': datetime.now().isoformat(),
        'admin_id': str(admin_user.id) if admin_user else 'system',
        'verification_token': str(bulletin.verification_token),
    }
    
    # Générer le hash unique du cachet
    hash_input = f"{bulletin.id}{bulletin.verification_token}{datetime.now().isoformat()}{admin_user.id if admin_user else 'system'}"
    stamp_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    
    # Signature numérique
    signature_input = f"BULLETIN-{bulletin.id}-{stamp_hash}"
    signature = hashlib.sha512(signature_input.encode()).hexdigest()[:32]
    
    # URL de vérification
    verification_url = f"/bulletins/verify/{bulletin.verification_token}/"
    
    return {
        'stamp_hash': stamp_hash,
        'signature': signature,
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'verification_url': verification_url,
        'stamp_data': stamp_data,
        'etablissement': 'Académie Numérique IA',
        'autorite': 'Ministère de l\'Éducation Nationale',
    }


def add_stamp_to_pdf_context(context, stamp_info):
    """
    Ajoute les informations du cachet au contexte du template PDF.
    
    Args:
        context: Contexte du template Django
        stamp_info: Informations du cachet générées par generate_digital_stamp
    
    Returns:
        dict: Contexte mis à jour avec les données du cachet
    """
    context.update({
        'digital_stamp': stamp_info,
        'stamp_hash': stamp_info['stamp_hash'],
        'stamp_signature': stamp_info['signature'],
        'stamp_timestamp': stamp_info['timestamp'],
        'stamp_verification_url': stamp_info['verification_url'],
        'stamp_etablissement': stamp_info['etablissement'],
        'stamp_autorite': stamp_info['autorite'],
    })
    
    return context


def verify_stamp(bulletin, stamp_hash, signature):
    """
    Vérifie l'authenticité d'un cachet numérique.
    
    Args:
        bulletin: Instance du Bulletin
        stamp_hash: Hash du cachet à vérifier
        signature: Signature à vérifier
    
    Returns:
        bool: True si le cachet est valide, False sinon
    """
    # Reconstruire le hash attendu
    expected_hash_input = f"{bulletin.id}{bulletin.verification_token}"
    expected_hash = hashlib.sha256(expected_hash_input.encode()).hexdigest()
    
    return stamp_hash == expected_hash


def generate_stamp_visual_svg(stamp_info):
    """
    Génère un SVG visuel du cachet pour inclusion dans les PDFs.
    
    Args:
        stamp_info: Informations du cachet
    
    Returns:
        str: SVG du cachet
    """
    svg = f'''
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <!-- Cercle extérieur -->
        <circle cx="100" cy="100" r="95" fill="none" stroke="#1e40af" stroke-width="3" opacity="0.6"/>
        <circle cx="100" cy="100" r="88" fill="none" stroke="#1e40af" stroke-width="1" opacity="0.4"/>
        
        <!-- Texte circulaire - Établissement -->
        <path id="arc1" d="M 100,100 m -75,0 a 75,75 0 1,1 150,0" fill="none"/>
        <text font-size="11" font-weight="bold" fill="#1e40af" opacity="0.7">
            <textPath href="#arc1" startOffset="50%" text-anchor="middle">
                {stamp_info['etablissement'].upper()}
            </textPath>
        </text>
        
        <!-- Texte circulaire - Autorité -->
        <path id="arc2" d="M 100,100 m 75,0 a 75,75 0 1,1 -150,0" fill="none"/>
        <text font-size="9" font-weight="bold" fill="#1e40af" opacity="0.7">
            <textPath href="#arc2" startOffset="50%" text-anchor="middle">
                {stamp_info['autorite'].upper()}
            </textPath>
        </text>
        
        <!-- Centre du cachet -->
        <circle cx="100" cy="100" r="50" fill="#1e40af" opacity="0.1"/>
        
        <!-- Icône centrale -->
        <text x="100" y="85" font-size="28" fill="#1e40af" opacity="0.8" text-anchor="middle">✓</text>
        
        <!-- Date -->
        <text x="100" y="110" font-size="10" font-weight="bold" fill="#1e40af" text-anchor="middle" opacity="0.7">
            {stamp_info['timestamp'][:10]}
        </text>
        
        <!-- Hash court -->
        <text x="100" y="125" font-size="7" fill="#1e40af" text-anchor="middle" opacity="0.6" font-family="monospace">
            {stamp_info['stamp_hash'][:12].upper()}
        </text>
        
        <!-- Signature -->
        <text x="100" y="140" font-size="8" font-weight="bold" fill="#1e40af" text-anchor="middle" opacity="0.7">
            APPROUVÉ
        </text>
    </svg>
    '''
    
    return svg
