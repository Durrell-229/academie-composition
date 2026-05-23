@echo off
title 🎓 ACADÉMIE NUMÉRIQUE - Lancement de la Plateforme
color 0B

cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║         🎓 ACADÉMIE NUMÉRIQUE - Plateforme Éducative           ║
echo ║                                                              ║
echo ║         Système scolaire du Bénin 🇧🇯 - Version 2.0          ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Vérifier si l'environnement virtuel existe
if not exist ".venv\Scripts\activate.bat" (
    echo ⚠️  Environnement virtuel non trouvé !
    echo 🔧 Création de l'environnement virtuel...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Erreur lors de la création de l'environnement virtuel
        pause
        exit /b 1
    )
    echo ✅ Environnement virtuel créé
)

:: Activer l'environnement virtuel
echo.
echo 🔌 Activation de l'environnement virtuel...
call .venv\Scripts\activate

:: Vérifier les dépendances
echo.
echo 📦 Vérification des dépendances...
python -c "import django" 2>nul
if errorlevel 1 (
    echo 🔧 Installation des dépendances...
    pip install -r requirements.txt
    pip install pillow qrcode google-generativeai requests xhtml2pdf
)

:: Vérifier si les migrations existent
echo.
echo 🗄️  Vérification des migrations...
if not exist "schools\migrations\0001_initial.py" (
    echo 🔧 Création des migrations...
    python manage.py makemigrations schools academic schedule attendance cahier messaging certificats payments parents library analytics
)

:: Appliquer les migrations
echo.
echo 🔄 Application des migrations...
python manage.py migrate

:: Vérifier si un superutilisateur existe
echo.
echo 👤 Vérification du superutilisateur...
python -c "from accounts.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo ⚠️  Aucun superutilisateur trouvé !
    echo 📝 Voulez-vous créer un superutilisateur maintenant ?
    choice /C ON /N /M "Appuyez sur O pour Oui, N pour Non: "
    if errorlevel 2 goto :skip_admin
    if errorlevel 1 goto :create_admin
)
goto :skip_admin

:create_admin
echo.
echo 🔑 Création du superutilisateur...
python manage.py createsuperuser
echo.
echo ✅ Superutilisateur créé !
goto :skip_admin

:skip_admin
:: Lancer le serveur
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🚀 LANCEMENT DU SERVEUR                   ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  🌐 Interface Admin:  http://127.0.0.1:8000/admin/           ║
echo ║  🎓 Application:     http://127.0.0.1:8000/                 ║
echo ║  📊 Architecture:   docs/architecture_uml.html              ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  📧 Admin:          admin@academie.bj                       ║
echo ║  📱 Support:        support@academie.bj                     ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🖥️  Appuyez sur Ctrl+C pour arrêter le serveur
echo.

python manage.py runserver

:: Désactiver l'environnement à la fermeture
call .venv\Scripts\deactivate

echo.
echo 👋 Au revoir !
pause
