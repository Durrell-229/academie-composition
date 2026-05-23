# Mémoire Projet — Intégration Paiement Admin
## Académie Numérique · Django 5.2 · Mise à jour : 2026-05-16

---

## 1. Architecture des paiements

### App `payments` (frais scolaires + abonnements FedaPay)

| Modèle | Description | Enregistré admin |
|--------|------------|-----------------|
| `FraisScolaire` | Types de frais (inscription, scolarité, examen…) | ✅ |
| `Paiement` | Paiements scolaires élèves (XOF) | ✅ |
| `EcheancierPaiement` | Échéances liées à un paiement | ✅ |
| `TransactionPaiement` | Historique de chaque transaction | ✅ |
| `BourseScolaire` | Bourses d'excellence / sociales | ✅ |
| `RapportFinancier` | Rapports mensuels/trimestriels/annuels | ✅ |
| `PlanAbonnementScolaire` | Plans (Basique/Standard/Premium/Elite) | ✅ |
| `AbonnementEleve` | Abonnement actif d'un élève | ✅ |
| `PaiementAbonnement` | Transaction FedaPay liée à un abonnement | ✅ |
| `ConfigurationFedaPay` | Clés API + webhook par établissement | ✅ |
| `PromotionAbonnement` | Codes promo | ✅ |
| `ConfigurationCommission` | Taux admin / commercial / prestataire | ✅ |
| `PayoutCommission` | Payout automatique post-paiement | ✅ |
| `PaiementCorrectionUnitaire` | Paiement ponctuel pour débloquer 1 correction IA | ✅ |
| `ConfigTarifCandidature` | Tarifs par type de candidat (académie / libre) | ✅ |
| `PlanEchelonnement` | Plan de paiement en tranches | ✅ |
| `TranchePaiement` | Tranche individuelle d'échelonnement | ✅ |
| `DocumentRequis` | Documents requis pour une candidature | ✅ |
| `DossierCandidature` | Dossier d'un élève | ✅ |
| `SoumissionDocument` | Document soumis dans un dossier | ✅ |

### App `subscriptions` (abonnements génériques utilisateurs)

| Modèle | Description | Enregistré admin |
|--------|------------|-----------------|
| `SubscriptionPlan` | Plans FREE / PRO / ELITE | ✅ |
| `UserSubscription` | Abonnement d'un utilisateur | ✅ |

---

## 2. Provider de paiement : FedaPay

- **Devise** : XOF (Francs CFA)
- **Environnements** : `sandbox` (tests) / `production`
- **Configuration** : modèle `ConfigurationFedaPay` (une entrée par établissement)
- **Webhook** : `payments/views.py` → traitement des événements FedaPay
- **Service** : `payments/fedapay_service.py`
- **Variables d'environnement nécessaires** :
  - `FEDAPAY_PUBLIC_KEY`
  - `FEDAPAY_SECRET_KEY`
  - `FEDAPAY_WEBHOOK_SECRET`

---

## 3. Flux de paiement abonnement

```
Élève → Sélection plan → Initiation FedaPay → URL de paiement
→ Webhook FedaPay → PaiementAbonnement.statut = "succes"
→ AbonnementEleve.statut = "actif"
→ PayoutCommission × 3 (admin / commercial / prestataire)
```

---

## 4. Système de commissions

- **Admin** : `taux_admin` % du montant
- **Commercial** : `taux_commercial` %
- **Prestataire** : `taux_prestataire` %
- Somme = 100 % (validé par `clean()`)
- Chaque paiement génère **3 lignes** `PayoutCommission`

---

## 5. Modes de paiement supportés

| Mode | Code |
|------|------|
| Mobile Money (MTN) | `mobile_money` |
| Orange Money | `om` |
| Wave | `wave` |
| Carte bancaire | `carte` |
| Espèces | `especes` |
| Virement | `virement` |

---

## 6. Fichiers modifiés (2026-05-16)

| Fichier | Action |
|---------|--------|
| `payments/admin.py` | **Réécrit complet** — 20 modèles enregistrés avec badges colorés et fieldsets détaillés |
| `subscriptions/admin.py` | **Créé** — `SubscriptionPlan` + `UserSubscription` enregistrés (était vide) |

### Modèles qui manquaient avant cette mise à jour
- Importés mais non enregistrés : `EcheancierPaiement`, `BourseScolaire`, `RapportFinancier`
- Complètement absents : `ConfigurationCommission`, `PayoutCommission`, `PaiementCorrectionUnitaire`, `ConfigTarifCandidature`, `PlanEchelonnement`, `TranchePaiement`, `DocumentRequis`, `DossierCandidature`, `SoumissionDocument`
- `subscriptions/admin.py` totalement vide

---

## 7. Commandes à exécuter après modification

```bash
# Vérifier qu'il n'y a pas d'erreur d'import
python manage.py check

# Si nouvelles migrations nécessaires
python manage.py makemigrations payments subscriptions
python manage.py migrate

# Créer/vérifier le superuser
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

---

## 8. URL Admin

```
http://127.0.0.1:8000/admin/
```

**Sections visibles dans l'admin après cette mise à jour :**
- **Payments** → Frais scolaires, Paiements, Échéances, Transactions, Bourses, Rapports, Abonnements, Plans, Promotions, Commissions, Payouts, Corrections unitaires, Tarifs candidature, Échelonnements, Tranches, Documents, Dossiers candidature
- **Subscriptions** → Plans, Abonnements utilisateurs

---

## 9. Stack technique

- **Framework** : Django 5.2
- **Auth** : Modèle custom `accounts.User` (rôle `eleve`, `admin`, etc.)
- **Paiement** : FedaPay (Mobile Money Bénin)
- **DB** : SQLite (dev) / PostgreSQL (prod Render)
- **Email** : Resend SMTP
- **IA** : Groq / Gemini / Mistral / DeepSeek / NVIDIA (fallback)
- **Hébergement** : Render.com

---

*Généré automatiquement par Claude · Académie Numérique · 2026-05-16*
