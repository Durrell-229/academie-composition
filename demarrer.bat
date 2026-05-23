@echo off
title Academie Numerique - Demarrage

echo.
echo  ============================================================
echo   ACADEMIE NUMERIQUE - Lancement du serveur local
echo  ============================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo  [ERREUR] Environnement virtuel introuvable.
    echo  Lancez d abord : python -m venv venv
    echo  puis : venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo  [1/3] Activation de l environnement virtuel...
call venv\Scripts\activate.bat

echo  [2/3] Application des migrations...
python manage.py migrate --run-syncdb

echo  [3/3] Initialisation des matieres par defaut...
python manage.py init_matieres

echo  [4/4] Ouverture du navigateur dans 2 secondes...
start "" cmd /c "timeout /t 2 /nobreak > nul && start http://127.0.0.1:8000"

echo.
echo  ============================================================
echo   Serveur disponible sur : http://127.0.0.1:8000
echo   Appuyez sur CTRL+C pour arreter le serveur
echo  ============================================================
echo.
python manage.py runserver

pause
