#!/bin/bash
# ============================================================
# Deploy Script — Déploiement automatisé vers Render.com
# Usage : ./deploy-render.sh
# ============================================================

set -o errexit

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ────────────────────────────────────────────────────────
# 1. VÉRIFICATIONS INITIALES
# ────────────────────────────────────────────────────────

check_prerequisites() {
    echo -e "${CYAN}🔍 Vérification des prérequis...${NC}"

    local missing=""

    # Vérifier Git
    if ! command -v git &> /dev/null; then
        missing="${missing}git "
    fi

    # Vérifier le repository
    if [ ! -d .git ]; then
        missing="${missing}repository-git "
    fi

    # Vérifier les fichiers
    for file in render.yaml Procfile render-build.sh requirements.txt; do
        if [ ! -f "$file" ]; then
            missing="${missing}$file "
        fi
    done

    if [ ! -z "$missing" ]; then
        echo -e "${RED}❌ Éléments manquants : $missing${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Tous les prérequis sont présents${NC}"
    return 0
}

# ────────────────────────────────────────────────────────
# 2. VÉRIFIER L'ÉTAT GIT
# ────────────────────────────────────────────────────────

check_git_status() {
    echo -e "${CYAN}📝 Vérification du statut Git...${NC}"

    if [ ! -z "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  Fichiers modifiés détectés :${NC}"
        git status --short

        read -p "Voulez-vous continuer ? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    echo -e "${GREEN}✅ État Git OK${NC}"
    return 0
}

# ────────────────────────────────────────────────────────
# 3. VÉRIFIER LE FICHIER RENDER.YAML
# ────────────────────────────────────────────────────────

check_render_yaml() {
    echo -e "${CYAN}📋 Vérification du render.yaml...${NC}"

    if [ ! -f render.yaml ]; then
        echo -e "${RED}❌ render.yaml non trouvé${NC}"
        return 1
    fi

    if grep -q "^services:" render.yaml && grep -q "type: web" render.yaml; then
        echo -e "${GREEN}✅ render.yaml valide${NC}"
        return 0
    fi

    echo -e "${RED}❌ render.yaml semble invalide${NC}"
    return 1
}

# ────────────────────────────────────────────────────────
# 4. RÉSUMÉ PRÉ-DÉPLOIEMENT
# ────────────────────────────────────────────────────────

show_deployment_summary() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}   RÉSUMÉ PRÉ-DÉPLOIEMENT${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"

    echo ""
    echo -e "${CYAN}Repository :${NC} $(git config --get remote.origin.url)"
    echo -e "${CYAN}Branch :${NC} $(git rev-parse --abbrev-ref HEAD)"
    echo -e "${CYAN}Commit :${NC} $(git rev-parse --short HEAD)"
    echo -e "${CYAN}Render YAML :${NC} render.yaml ✓"
    echo -e "${CYAN}Procfile :${NC} Procfile ✓"
    echo -e "${CYAN}Build script :${NC} render-build.sh ✓"

    echo ""
    echo -e "${YELLOW}Services à créer sur Render :${NC}"
    echo "  • academie-numerique-web (Web - Daphne)"
    echo "  • academie-celery-worker (Worker)"
    echo "  • academie-celery-beat (Beat scheduler)"
    echo "  • academie-redis (Redis)"
    echo "  • academie-db (PostgreSQL)"

    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
}

# ────────────────────────────────────────────────────────
# 5. MAIN WORKFLOW
# ────────────────────────────────────────────────────────

main() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   ACADÉMIE NUMÉRIQUE — Deploy vers Render         ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Vérifications
    check_prerequisites || exit 1
    check_git_status || exit 1
    check_render_yaml || exit 1

    echo ""
    show_deployment_summary
    echo ""

    # Instructions
    echo -e "${GREEN}🚀 Prêt pour le déploiement !${NC}"
    echo ""
    echo -e "${CYAN}Prochaines étapes :${NC}"
    echo "  1. Aller à https://render.com/dashboard"
    echo "  2. Cliquer 'New' → 'Blueprint'"
    echo "  3. Sélectionner ce repository GitHub"
    echo "  4. Render détecte render.yaml automatiquement"
    echo "  5. Configurer les variables d'environnement"
    echo "  6. Cliquer 'Deploy'"
    echo ""

    # Optionnel : Push si les fichiers ont changé
    read -p "Voulez-vous pousser les changements vers GitHub ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}📤 Push vers GitHub...${NC}"
        git add render.yaml Procfile render-build.sh .env.render RENDER_DEPLOYMENT.md
        git commit -m "feat: add Render deployment configuration" || true
        git push origin
        echo -e "${GREEN}✅ Push complété${NC}"
    fi

    echo ""
    echo -e "${GREEN}✨ Configuration prête pour Render !${NC}"
}

# Lancer le script
main "$@"
