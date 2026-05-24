# ============================================================
# Deploy Script — Déploiement automatisé vers Render.com
# Usage : ./deploy-render.ps1
# ============================================================

param(
    [string]$ACTION = "check",
    [string]$ENV_FILE = ".env.render"
)

# Couleurs pour l'affichage
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

# ────────────────────────────────────────────────────────
# 1. VÉRIFICATIONS INITIALES
# ────────────────────────────────────────────────────────

function Check-Prerequisites {
    Write-Info "🔍 Vérification des prérequis..."

    $missing = @()

    # Vérifier Git
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        $missing += "git"
    }

    # Vérifier le repository GitHub
    if (-not (Test-Path .git)) {
        $missing += "repository Git"
    }

    # Vérifier les fichiers de déploiement
    $requiredFiles = @("render.yaml", "Procfile", "render-build.sh", "requirements.txt")
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missing += $file
        }
    }

    if ($missing.Count -gt 0) {
        Write-Error "❌ Éléments manquants : $($missing -join ', ')"
        return $false
    }

    Write-Success "✅ Tous les prérequis sont présents"
    return $true
}

# ────────────────────────────────────────────────────────
# 2. VÉRIFIER L'ÉTAT GIT
# ────────────────────────────────────────────────────────

function Check-GitStatus {
    Write-Info "📝 Vérification du statut Git..."

    $status = git status --porcelain

    if ($status) {
        Write-Warning "⚠️  Fichiers modifiés détectés :"
        git status --short

        $response = Read-Host "Voulez-vous continuer ? (y/n)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            return $false
        }
    }

    Write-Success "✅ État Git OK"
    return $true
}

# ────────────────────────────────────────────────────────
# 3. VÉRIFIER LE FICHIER RENDER.YAML
# ────────────────────────────────────────────────────────

function Check-RenderYAML {
    Write-Info "📋 Vérification du render.yaml..."

    if (-not (Test-Path render.yaml)) {
        Write-Error "❌ render.yaml non trouvé"
        return $false
    }

    # Vérifier la syntaxe YAML basique
    $content = Get-Content render.yaml
    if ($content -match 'services:' -and $content -match 'web') {
        Write-Success "✅ render.yaml valide"
        return $true
    }

    Write-Error "❌ render.yaml semble invalide"
    return $false
}

# ────────────────────────────────────────────────────────
# 4. VÉRIFIER LES VARIABLES D'ENVIRONNEMENT
# ────────────────────────────────────────────────────────

function Check-EnvVars {
    Write-Info "🔐 Vérification des variables d'environnement..."

    $requiredVars = @(
        "DJANGO_SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "GROQ_API_KEY",
        "CLOUDINARY_URL",
        "RESEND_API_KEY",
        "FEDAPAY_PUBLIC_KEY"
    )

    $missing = @()
    foreach ($var in $requiredVars) {
        if (-not [Environment]::GetEnvironmentVariable($var)) {
            $missing += $var
        }
    }

    if ($missing.Count -gt 0) {
        Write-Warning "⚠️  Variables manquantes : $($missing -join ', ')"
        Write-Info "   → À configurer dans le dashboard Render"
        return $true  # Continue quand même
    }

    Write-Success "✅ Variables d'environnement détectées"
    return $true
}

# ────────────────────────────────────────────────────────
# 5. VÉRIFIER LES DÉPENDANCES PYTHON
# ────────────────────────────────────────────────────────

function Check-Dependencies {
    Write-Info "📦 Vérification des dépendances..."

    $requiredPackages = @("daphne", "celery", "channels", "gunicorn", "psycopg2")
    $missingPackages = @()

    foreach ($package in $requiredPackages) {
        if (-not (pip show $package -ErrorAction SilentlyContinue)) {
            $missingPackages += $package
        }
    }

    if ($missingPackages.Count -gt 0) {
        Write-Warning "⚠️  Packages manquants : $($missingPackages -join ', ')"
        Write-Info "   → À installer : pip install -r requirements.txt"
        return $false
    }

    Write-Success "✅ Dépendances OK"
    return $true
}

# ────────────────────────────────────────────────────────
# 6. RÉSUMÉ PRÉ-DÉPLOIEMENT
# ────────────────────────────────────────────────────────

function Show-DeploymentSummary {
    Write-Host ""
    Write-Info "════════════════════════════════════════════════════"
    Write-Info "   RÉSUMÉ PRÉ-DÉPLOIEMENT"
    Write-Info "════════════════════════════════════════════════════"

    Write-Host ""
    Write-Info "Repository : $(git config --get remote.origin.url)"
    Write-Info "Branch : $(git rev-parse --abbrev-ref HEAD)"
    Write-Info "Commit : $(git rev-parse --short HEAD)"
    Write-Info "Render YAML : render.yaml ✓"
    Write-Info "Procfile : Procfile ✓"
    Write-Info "Build script : render-build.sh ✓"

    Write-Host ""
    Write-Warning "Services à créer sur Render :"
    Write-Host "  • academie-numerique-web (Web - Daphne)"
    Write-Host "  • academie-celery-worker (Worker)"
    Write-Host "  • academie-celery-beat (Beat scheduler)"
    Write-Host "  • academie-redis (Redis)"
    Write-Host "  • academie-db (PostgreSQL)"

    Write-Host ""
    Write-Info "════════════════════════════════════════════════════"
}

# ────────────────────────────────────────────────────────
# 7. MAIN WORKFLOW
# ────────────────────────────────────────────────────────

function Main {
    Clear-Host
    Write-Info "╔════════════════════════════════════════════════════╗"
    Write-Info "║   ACADÉMIE NUMÉRIQUE — Deploy vers Render         ║"
    Write-Info "╚════════════════════════════════════════════════════╝"
    Write-Host ""

    # Vérifications
    if (-not (Check-Prerequisites)) { exit 1 }
    if (-not (Check-GitStatus)) { exit 1 }
    if (-not (Check-RenderYAML)) { exit 1 }
    if (-not (Check-EnvVars)) { exit 1 }
    # Check-Dependencies (optionnel, peut être skippé)

    Write-Host ""
    Show-DeploymentSummary
    Write-Host ""

    # Instructions
    Write-Success "🚀 Prêt pour le déploiement !"
    Write-Host ""
    Write-Info "Prochaines étapes :"
    Write-Host "  1. Aller à https://render.com/dashboard"
    Write-Host "  2. Cliquer 'New' → 'Blueprint'"
    Write-Host "  3. Sélectionner ce repository GitHub"
    Write-Host "  4. Render détecte render.yaml automatiquement"
    Write-Host "  5. Configurer les variables d'environnement"
    Write-Host "  6. Cliquer 'Deploy'"
    Write-Host ""

    # Optionnel : Push si les fichiers ont changé
    $response = Read-Host "Voulez-vous pousser les changements vers GitHub ? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Info "📤 Push vers GitHub..."
        git add render.yaml Procfile render-build.sh .env.render RENDER_DEPLOYMENT.md
        git commit -m "feat: add Render deployment configuration" -ErrorAction SilentlyContinue
        git push origin
        Write-Success "✅ Push complété"
    }

    Write-Host ""
    Write-Success "✨ Configuration prête pour Render !"
}

# Lancer le script
Main
