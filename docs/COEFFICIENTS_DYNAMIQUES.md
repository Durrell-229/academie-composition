# 📊 Coefficients Dynamiques - Guide Pratique

## ✅ Système Mis à Jour

Le bulletin récupère **automatiquement** les coefficients depuis chaque source où vous les avez définis.

**AUCUNE** configuration supplémentaire nécessaire - c'est transparent !

---

## 🎯 Où Définir les Coefficients ?

### 1️⃣ Interrogations Courantes (Academic)

**Lieu:** Django Admin → Academic → Evaluations → Créer une Evaluation

```
Titre: "Français - Interrogation"
Matière-Classe: Français (3ème A)
Type: "Interrogation"
Date: 2026-05-12
Note Maximale: 20
📌 Coefficient: 2  ← LE COEFFICIENT QUI APPARAÎTRA SUR LE BULLETIN
```

**Résultat sur le bulletin:**
- Colonne "Coefficient": `2`
- Utilisé pour moyenne pondérée: `(Note × 2) / 2`

---

### 2️⃣ Devoirs Nationaux

**Lieu:** Django Admin → Devoirs → Créer un Devoir

#### Option A : Coefficient uniforme (tous les profs)

```
Titre: "Devoir National de Français"
Année Scolaire: 2025-2026
📌 Coefficient par défaut: 1.5  ← S'applique à TOUTES les matières
```

**Résultat:**
- Français: coefficient 1.5
- Maths: coefficient 1.5
- SVT: coefficient 1.5

---

#### Option B : Coefficients spécifiques par matière

```
Titre: "Devoir National d'Avril"
Année Scolaire: 2025-2026
📌 Coefficients par matière:
{
  "Français": 2,
  "Mathématiques": 3,
  "SVT": 1.5,
  "Anglais": 1,
  ...
}
```

**Résultat:**
- Français: coefficient 2
- Mathématiques: coefficient 3
- SVT: coefficient 1.5
- Anglais: coefficient 1

**Comment remplir (format JSON) :**
```json
{"Français": 2, "Mathématiques": 3, "SVT": 1.5}
```

---

### 3️⃣ Compositions/Examens

**Lieu:** Django Admin → Exams → Créer un Exam

```
Titre: "Composition Trimestrielle"
Type: "Composition"
Matière: Français
📌 Coefficient: 4  ← LE COEFFICIENT QUI APPARAÎTRA SUR LE BULLETIN
Note Maximale: 20
```

**Résultat sur le bulletin:**
- Français (composition): coefficient 4
- Moyenne finale: `(Moy_Interro + Moy_Devoir + Note_Composition) / 3 × coefficient 4`

---

## 🔄 Flux Complet (Exemple)

### Scénario : Bulletin de Français pour élève "Jean"

**Définitions (Admin):**

1. **Interrogation 1** (30 avril)
   - Coefficient: `2`
   - Note Jean: `14/20`

2. **Interrogation 2** (5 mai)
   - Coefficient: `2`
   - Note Jean: `16/20`

3. **Devoir National**
   - Coefficient Français: `1.5`
   - Note Jean: `13/20`

4. **Composition Trimestre**
   - Coefficient: `4`
   - Note Jean: `17/20`

**Calcul Automatique du Bulletin:**

```
Moy_Interrogations = (14 + 16) / 2 = 15
Moy_Devoirs = 13
Moy_Composition = 17

Moyenne_Matière = (15 + 13 + 17) / 3 = 15

Bulletin affiche:
┌─────────────────────────┐
│ Français                │
│ Coefficient: 4          │ ← Du Exam
│ Moy. Interro: 15        │ ← De Evaluations (coeff 2 chacune)
│ Moy. Devoir: 13         │ ← De DevoirReponse (coeff 1.5)
│ Note Composition: 17    │ ← Du Resultat (coeff 4)
│ Moy. Finale: 15         │ ← Calculée (15+13+17)/3
└─────────────────────────┘

Moyenne Générale = (15 × 4) / 4 = 15 (si Français seule matière)
```

---

## ⚡ Cas Particuliers

### Si coefficient NOT défini (NULL)

**Fallback automatique:**
1. Essayer coefficient de la source (Exam, Devoir, Evaluation)
2. Si NULL → utiliser `1` (coefficient neutre)
3. Si vraiment rien → utiliser coefficient officiel Bénin

**Résultat:** Aucune erreur, le système gère gracieusement

---

### Si élève n'a pas de note dans une matière

**Résultat sur bulletin:**
```
Français
Coefficient: 4
Moy. Interro: —    (pas de données)
Moy. Devoir: —     (pas de données)
Moy. Composition: — (pas de données)
Moy. Finale: 0     (zéro automatique)
```

**Pas d'erreur** - juste 0 comme dans une vraie école

---

## 🎓 Cas Avancés

### Modifier le Coefficient après Épreuves

**Question:** Je veux changer le coefficient de Français de 4 à 5

**Réponse:** Modifiez l'Exam:
```
Django Admin → Exams → [Composition Française]
Coefficient: 4  →  5
Sauvegarder
```

**Résultat:** Le prochain bulletin généré utilisera 5

*Les bulletins déjà générés restent inchangés (fichiers PDF statiques)*

---

### Coefficients Mixtes

**Scenario:**
- Interrogations: coefficient 1 chacune
- Devoir: coefficient 2
- Composition: coefficient 4

**Résultat sur bulletin:**
```
Coefficient (principal): 4  ← De Exam (priorité)
Mais utilisés en interne:
  - Interrogations: × 1
  - Devoirs: × 2
  - Composition: × 4
Pour moyenne pondérée correcte
```

---

## 🔍 Vérifier les Coefficients

### Via Django Admin

1. Aller à **Exams** → Voir les coefficients
2. Aller à **Devoirs** → Voir coefficients par défaut/matière
3. Aller à **Evaluations** → Voir les coefficients

### Via Django Shell

```python
from exams.models import Exam
from devoirs.models import Devoir
from academic.models import Evaluation

# Exam
exam = Exam.objects.first()
print(f"Exam coefficient: {exam.coefficient}")

# Devoir
devoir = Devoir.objects.first()
print(f"Devoir coefficient par défaut: {devoir.coefficient_default}")
print(f"Devoir coefficients par matière: {devoir.coefficients_par_matiere}")

# Evaluation
eval = Evaluation.objects.first()
print(f"Evaluation coefficient: {eval.coefficient}")
```

---

## ✅ Résumé

| Source | Champ | Récupéré Par Bulletin |
|--------|-------|----------------------|
| **Interrogation** | Evaluation.coefficient | ✅ Automatique |
| **Devoir** | Devoir.coefficient_default | ✅ Automatique |
| **Devoir** | Devoir.coefficients_par_matiere | ✅ Automatique |
| **Composition** | Exam.coefficient | ✅ Automatique |

**Aucune configuration supplémentaire** - Tout est transparent et dynamique !

---

## 🚀 Prochaines Étapes

1. ✅ Créer une Interrogation avec coefficient 2
2. ✅ Créer un Devoir avec coefficients par matière
3. ✅ Créer une Composition avec coefficient 4
4. ✅ Générer un bulletin
5. ✅ Vérifier que les coefficients affichés correspondent à vos définitions

**Le système est prêt !** 🎉
