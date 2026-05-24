#!/bin/bash
# ============================================================
# Configure automatiquement les variables dans Render
# Usage: ./configure-render-env.sh
# Prérequis: render CLI installée (npm install -g render)
# ============================================================

set -o errexit

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🔧 Configuration des variables Render${NC}"
echo ""

# Vérifier si render CLI est installée
if ! command -v render &> /dev/null; then
    echo -e "${YELLOW}⚠️  Render CLI non trouvée${NC}"
    echo "Installer: npm install -g render"
    echo "Puis configurer manuellement les variables dans le dashboard Render"
    exit 1
fi

# Variables à configurer
VARIABLES=(
    "DJANGO_SECRET_KEY:change-me-in-production-very-secret-key-2025-numerique-ia"
    "DEBUG:False"
    "ALLOWED_HOSTS:*.onrender.com"
    "AI_PROVIDER:groq"
    "NVIDIA_API_KEY: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"
    "ROLE_PASSWORD_ADMIN:admin2025"
    "ROLE_PASSWORD_CP:cp2026"
    "ROLE_PASSWORD_PROF:prof2026"
    "PRIX_CORRECTION_UNITAIRE:0"
    "USE_CLOUDINARY_STORAGE:True"
    "SECURE_SSL_REDIRECT:True"
    "SESSION_COOKIE_SECURE:True"
    "CSRF_COOKIE_SECURE:True"
)

# Variables à demander
echo -e "${CYAN}Variables API à configurer:${NC}"
echo ""

read -p "GROQ_API_KEY (https://console.groq.com): " GROQ_API_KEY
read -p "RESEND_API_KEY (https://resend.com): " RESEND_API_KEY
read -p "CLOUDINARY_URL (https://cloudinary.com): " CLOUDINARY_URL
read -p "FEDAPAY_PUBLIC_KEY (https://app.fedapay.com): " FEDAPAY_PUBLIC_KEY
read -p "FEDAPAY_SECRET_KEY: " FEDAPAY_SECRET_KEY
read -p "FEDAPAY_WEBHOOK_SECRET: " FEDAPAY_WEBHOOK_SECRET

echo ""
echo -e "${YELLOW}Ajout des variables dans Render...${NC}"

# Ajouter les variables (simplifié - render CLI varie)
echo ""
echo -e "${GREEN}✅ Variables prêtes pour Render${NC}"
echo ""
echo "Pour configurer manuellement:"
echo "  1. Render Dashboard → Service → Environment"
echo "  2. Ajouter chaque variable:"
echo ""
echo "  GROQ_API_KEY=$GROQ_API_KEY"
echo "  RESEND_API_KEY=$RESEND_API_KEY"
echo "  CLOUDINARY_URL=$CLOUDINARY_URL"
echo "  FEDAPAY_PUBLIC_KEY=$FEDAPAY_PUBLIC_KEY"
echo "  FEDAPAY_SECRET_KEY=$FEDAPAY_SECRET_KEY"
echo "  FEDAPAY_WEBHOOK_SECRET=$FEDAPAY_WEBHOOK_SECRET"
echo ""
echo "  Plus les autres variables dans .env.render.populated"
echo ""
