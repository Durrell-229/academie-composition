# 🎨 Guide d'Ajustement - Template Bulletin Simple

## ✅ Système en Place

Le système génère maintenant un **bulletin HTML simple et propre** qui :
- ✅ Se convertit correctement en PDF (sans erreurs)
- ✅ Respecte le format officiel Bénin
- ✅ Affiche les coefficients dynamiques
- ✅ Gère les zéros automatiquement

**Fichier template:** `templates/bulletins/bulletin_simple.html`

---

## 🎯 Comment Ajuster le Rendu

### 1. Ouvrir et Examiner le PDF

```
C:/tmp/bulletin_simple.pdf
```

Vérifiez :
- ✓ Espaces entre les sections
- ✓ Taille des polices
- ✓ Largeurs des colonnes du tableau
- ✓ Couleurs (vert Bénin, rouge décision)

---

### 2. Modifier le CSS du Template

**Chemin:** `templates/bulletins/bulletin_simple.html`

Modifiez les sections CSS ci-dessous selon vos besoins :

#### A. Espacements

```css
/* Modifier les marges */
.page {
    padding: 10mm;  /* ← Augmenter/diminuer l'espacement autour */
}

.titre-bulletin {
    margin-bottom: 5mm;  /* ← Espace sous le titre */
}

.identite-box {
    margin-bottom: 5mm;  /* ← Espace sous l'identité */
}
```

#### B. Tailles des Polices

```css
/* En-tête */
.header-title {
    font-size: 10px;  /* ← Augmenter/diminuer */
}

.school-name {
    font-size: 11px;  /* ← Plus grand/petit */
}

/* Tableau */
.notes-table th {
    font-size: 7px;  /* ← Titres du tableau */
}

.notes-table td {
    font-size: 8px;  /* ← Données du tableau */
}

/* Résultats */
.resultat-value {
    font-size: 14px;  /* ← Chiffres grande taille */
}
```

#### C. Couleurs

```css
/* Couleur Bénin (vert) */
.school-name {
    color: #008751;  /* ← Modifier si besoin */
}

.resultat-value {
    color: #008751;  /* ← Vert pour moyennes */
}

/* Couleur décision (rouge) */
.obs-decision {
    color: #E8112D;  /* ← Rouge pour décision */
}
```

#### D. Tableau des Notes

```css
.notes-table th {
    background: #e0e0e0;  /* ← Couleur en-tête */
}

.notes-table tbody tr:nth-child(even) {
    background: #fafafa;  /* ← Alternance lignes */
}

.notes-table td {
    padding: 2mm 1mm;  /* ← Augmenter pour plus d'espace */
}
```

---

## 🔧 Exemples d'Ajustements Courants

### Exemple 1: Augmenter l'Espace du Tableau

**Chercher :**
```css
.notes-table td {
    border: 1px solid #ccc;
    padding: 2mm 1mm;  ← CETTE LIGNE
    text-align: center;
}
```

**Changer en :**
```css
.notes-table td {
    border: 1px solid #ccc;
    padding: 4mm 2mm;  ← Plus d'espace
    text-align: center;
}
```

**Résultat:** Tableau plus aéré

---

### Exemple 2: Augmenter la Taille du Titre

**Chercher :**
```css
.titre-bulletin {
    font-size: 11px;  ← CETTE LIGNE
}
```

**Changer en :**
```css
.titre-bulletin {
    font-size: 13px;  ← Plus gros
}
```

**Résultat:** Titre plus visible

---

### Exemple 3: Réduire l'En-Tête

**Chercher :**
```css
.header {
    margin-bottom: 8mm;  ← CETTE LIGNE
}
```

**Changer en :**
```css
.header {
    margin-bottom: 4mm;  ← Moins d'espace
}
```

**Résultat:** En-tête plus compact

---

## 📊 Workflow d'Ajustement

### Étape 1: Générer le PDF
```bash
python manage.py shell
# Dans Django shell:
from bulletins.models import Bulletin
from bulletins.services import BulletinService
b = Bulletin.objects.first()
BulletinService.generate_bulletin_from_image_pdf(b)
```

### Étape 2: Ouvrir C:/tmp/bulletin_simple.pdf
- Examiner le rendu
- Identifier ce qui ne va pas

### Étape 3: Modifier templates/bulletins/bulletin_simple.html
- Changer les CSS comme décrit ci-dessus
- Sauvegarder le fichier

### Étape 4: Régénérer et Vérifier
- Relancer la génération
- Ouvrir le nouveau PDF
- Répéter jusqu'à satisfaction

---

## 🎨 CSS Sections Disponibles pour Ajustement

| Section | Classe CSS | Ajuste |
|---------|-----------|--------|
| **Drapeau** | `.drapeau` | Hauteur, couleurs |
| **En-tête** | `.header` | Marges, espacements |
| **Titre** | `.titre-bulletin` | Taille, fond, bordures |
| **Identité** | `.identite-box` | Layout, espacements |
| **Tableau** | `.notes-table` | Tailles, couleurs, padding |
| **Résultats** | `.resultats` | Disposition, polices |
| **Observations** | `.observations` | Hauteur, font |
| **Décision** | `.obs-decision` | Couleur, taille, lettrage |

---

## 💡 Astuces

### Augmenter Espace Entre Champs
```css
.identite-ligne {
    gap: 3mm 8mm;  /* ← Augmenter 8mm à 10mm ou plus */
}
```

### Changer Arrière-Plan Section
```css
.identite-box {
    background: #f5f5f5;  /* ← Ajouter une couleur */
}
```

### Ajouter Bordures Supplémentaires
```css
.resultats {
    border: 2px solid #008751;  /* ← Bordure plus épaisse/couleur */
}
```

### Modifier Hauteur Bloc Observations
```css
.obs-content {
    min-height: 12mm;  /* ← Augmenter à 15mm ou 20mm */
}
```

---

## 🚀 Modification Rapide

**Si vous voulez SIMPLEMENT :**

1. **Plus d'espace** → Augmentez tous les `margin` et `padding`
2. **Moins d'espace** → Diminuez tous les `margin` et `padding`
3. **Plus gros** → Augmentez `font-size` partout
4. **Plus compact** → Diminuez `font-size` partout

Exemple complet :
```css
/* COMPACT */
.page { padding: 6mm; }
.header { margin-bottom: 4mm; }
.titre-bulletin { font-size: 10px; margin-bottom: 3mm; }
.notes-table td { padding: 1.5mm 0.5mm; font-size: 7px; }

/* AÉRÉ */
.page { padding: 15mm; }
.header { margin-bottom: 10mm; }
.titre-bulletin { font-size: 12px; margin-bottom: 8mm; }
.notes-table td { padding: 4mm 2mm; font-size: 9px; }
```

---

## ✅ Vérification Final

Après chaque ajustement, vérifiez :

- [ ] Le titre est lisible
- [ ] Les colonnes du tableau ne débordent pas
- [ ] L'espace entre sections est cohérent
- [ ] Les observations tiennent sur une page
- [ ] La décision est bien visible
- [ ] Pas de texte coupé en bas de page

---

## 📞 Support

**Si le PDF déborde ou se coupe :**
- Réduisez `font-size` partout
- Diminuez `padding` et `margin`
- Augmentez `page { padding }` pour donner plus d'air

**Si c'est trop compact :**
- Augmentez `font-size`
- Augmentez `padding` et `margin`
- Réduisez `page { padding }`

---

## 🎉 Résultat Final

Une fois ajusté selon vos préférences, chaque bulletin généré aura :
- ✅ Coefficients dynamiques (du prof)
- ✅ Zéros automatiques (si pas de notes)
- ✅ Layout parfait (votre choix CSS)
- ✅ Format professionnel

**C'est simple, flexible, et totalement customisable !** 🚀
