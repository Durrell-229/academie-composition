#!/bin/bash
# ============================================================
# Build script pour Render.com
# À utiliser comme buildCommand dans render.yaml
# ============================================================
set -o errexit

echo "🔄 Installation des dépendances..."
pip install -U pip setuptools wheel
pip install -r requirements.txt

echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear

echo "🗄️ Migration de la base de données..."
python manage.py migrate --noinput

echo "✅ Configuration complétée avec succès !"
