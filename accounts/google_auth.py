"""
Google OAuth 2.0 authentication flow.
Handles redirect to Google consent, token exchange, user info fetch, and login.
"""
import secrets
import logging
import urllib.parse
import urllib.request
import json
import os

from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings

from accounts.models import User

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

# OAuth scopes
SCOPES = 'openid email profile'


def google_login_redirect(request):
    """Redirect user to Google OAuth consent screen."""
    # Check credentials are configured
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '')

    if not client_id:
        from django.contrib import messages
        messages.error(request, "Google OAuth non configuré. Contactez l'administrateur.")
        return redirect('login')

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state

    # Where to redirect after successful login
    request.session['google_oauth_next'] = request.GET.get('next', '/accueil/')

    # Build authorization URL
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': SCOPES,
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account',
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


def google_callback(request):
    """Handle Google OAuth callback — exchange code for tokens, fetch user, login."""
    # Verify state (CSRF protection)
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')

    if error:
        messages.error(request, f"Erreur Google: {request.GET.get('error_description', error)}")
        return redirect('login')

    if not code or not state:
        messages.error(request, "Réponse Google invalide.")
        return redirect('login')

    stored_state = request.session.get('google_oauth_state')
    if not stored_state or state != stored_state:
        messages.error(request, "Erreur de sécurité. Réessayez.")
        return redirect('login')

    # Clean up session
    request.session.pop('google_oauth_state', None)
    next_url = request.session.pop('google_oauth_next', '/accueil/')

    # Exchange authorization code for access token
    token_data = urllib.parse.urlencode({
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }).encode('utf-8')

    try:
        req = urllib.request.Request(GOOGLE_TOKEN_URL, data=token_data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_resp = json.loads(resp.read().decode('utf-8'))

        if 'error' in token_resp:
            logger.error(f"Google token error: {token_resp['error']}")
            messages.error(request, "Erreur lors de l'authentification Google.")
            return redirect('login')

        access_token = token_resp.get('access_token')

        # Fetch user info from Google
        userinfo_req = urllib.request.Request(GOOGLE_USERINFO_URL)
        userinfo_req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(userinfo_req, timeout=15) as resp:
            userinfo = json.loads(resp.read().decode('utf-8'))

    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        messages.error(request, "Impossible de se connecter avec Google. Réessayez.")
        return redirect('login')

    # Extract user info
    email = userinfo.get('email', '')
    first_name = userinfo.get('given_name', '')
    last_name = userinfo.get('family_name', '')
    picture = userinfo.get('picture', '')
    email_verified = userinfo.get('verified_email', False)

    if not email or not email_verified:
        messages.error(request, "Email Google non vérifié. Utilisez un autre compte.")
        return redirect('login')

    # Find or create user
    user = User.objects.filter(email=email).first()
    is_new_user = user is None
    if is_new_user:
        # Create new user — will need role assignment
        user = User.objects.create(
            email=email,
            first_name=first_name or email.split('@')[0],
            last_name=last_name or '',
            role=User.Role.ELEVE,  # temporary default
            is_verified=True,
        )

        # Download and set profile picture from Google
        if picture:
            try:
                _set_user_avatar_from_url(user, picture)
            except Exception as e:
                logger.warning(f"Could not set Google avatar for {email}: {e}")

        # Redirect to role choice page for first-time users
        request.session['oauth_user_id'] = str(user.id)
        messages.info(request, "Bienvenue ! Choisissez votre rôle pour continuer.")
        from django.shortcuts import redirect as dj_redirect
        return dj_redirect('oauth_choose_role')
    else:
        # Existing user — update name/avatar if empty
        if not user.first_name and first_name:
            user.first_name = first_name
        if not user.last_name and last_name:
            user.last_name = last_name
        user.is_verified = True
        user.save()

        # Update avatar from Google if currently empty
        if picture and not user.avatar:
            try:
                _set_user_avatar_from_url(user, picture)
            except Exception:
                pass

        # Log the user in
        login(request, user)
        messages.success(request, f"Connecté en tant que {user.full_name} via Google.")
        return redirect(next_url)


def _set_user_avatar_from_url(user, picture_url):
    """Download image from URL and set as user avatar."""
    from django.core.files.base import ContentFile
    from urllib.request import urlopen

    req = urllib.request.Request(picture_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=10) as resp:
        image_data = resp.read()

    filename = f"profiles/user_{user.id.hex[:8]}.jpg"
    user.avatar.save(filename, ContentFile(image_data), save=True)
