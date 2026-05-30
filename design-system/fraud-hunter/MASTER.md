# Design System Master File — Fraud Hunter

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Fraud Hunter — MPC Hacks 2026 (Track Valsoft)
**Direction visuelle :** Paper Detective + Tinder Swipe
**Métaphore :** Fiche d'enquête tapée à la machine, swipée comme dans Tinder

---

## Identité visuelle

L'utilisateur incarne un inspecteur qui passe en revue des dossiers de fraude. Chaque dossier est une **fiche d'enquête papier** posée sur un bureau. Le reviewer la lit, tamponne sa décision, et passe au suivant — à la manière d'un swipe Tinder.

### Anti-vibes (à éviter absolument)
- **Pas** de dark mode (on est dans un bureau, pas dans une salle de serveurs)
- **Pas** de gradients (anti-pattern paper)
- **Pas** d'animations modernes type scale/elevation (anti-pattern paper)
- **Pas** d'émojis comme icônes
- **Pas** de purple/pink (vibe AI playground — perte de crédibilité)
- **Pas** de néon ni de couleurs flashy

---

## Palette de couleurs

| Rôle | Hex | Usage |
|---|---|---|
| **Paper Background** | `#FDFBF7` | Fond global de l'app et des cartes |
| **Paper Off-White** | `#F5F0E6` | Variante pour zones de contraste subtil (header carte) |
| **Ink Black** | `#1A1A1A` | Texte principal (haut contraste) |
| **Pencil Grey** | `#4A4A4A` | Texte secondaire, labels |
| **Faded Sepia** | `#D4A574` | Bordures, séparateurs, métadonnées discrètes |
| **Kraft Brown** | `#C4A77D` | Accent papier (mentions, étiquettes anciennes) |
| **Stamp Red** | `#B91C1C` | Tampon "FRAUDE CONFIRMÉE" |
| **Stamp Green** | `#15803D` | Tampon "CLASSÉ INNOCENT" |
| **Stamp Amber** | `#B45309` | Tampon "À ESCALADER" |
| **Warning Yellow** | `#FEF3C7` | Highlights jaunes (style surligneur) |

### Variables CSS
```css
:root {
  --paper-bg: #FDFBF7;
  --paper-off: #F5F0E6;
  --ink: #1A1A1A;
  --pencil: #4A4A4A;
  --sepia: #D4A574;
  --kraft: #C4A77D;
  --stamp-red: #B91C1C;
  --stamp-green: #15803D;
  --stamp-amber: #B45309;
  --highlight: #FEF3C7;
}
```

---

## Typographie

**Une seule famille : Space Mono.** Brutalist Raw aesthetic — vibe "rapport tapé à la machine d'enquête". Mono partout = précision data + authenticité.

### Import
```css
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
```

### Hiérarchie
| Élément | Taille | Poids | Letter-spacing |
|---|---|---|---|
| Titre dossier (DOSSIER #042) | 20px | 700 | 0.05em |
| Section header (PIÈCES À CONVICTION) | 13px | 700 uppercase | 0.1em |
| Labels (SUSPECT, MONTANT, SCORE) | 12px | 400 uppercase | 0.08em |
| Valeurs principales | 16px | 700 | normal |
| Texte verdict IA | 14px | 400 | normal |
| Métadonnées (dates, IDs) | 12px | 400 | normal |
| Tampons | 24px | 700 uppercase | 0.15em |

---

## Textures

### Grain papier (subtle)
Overlay SVG noise sur le fond, 12% opacity. Donne l'impression d'un papier scanné, pas d'un écran propre.

```css
body {
  background-color: var(--paper-bg);
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
}
```

### Bordure crénelée (ticket style)
Headers de carte avec bordure dentelée pour évoquer un coupon administratif.

---

## Composant : Carte Dossier

### Anatomie (top → bottom)
1. **Header crénelé** (`#F5F0E6`) — "DOSSIER #042  •  42/67 traités"
2. **Bloc identité** — labels mono + valeurs alignées sur grille
3. **Score bar** — barre ASCII `▰▰▰▰▰▰▰▰▰░ 0.91`
4. **Séparateur tiret** — `─── VERDICT IA ───`
5. **Verdict IA** (Claude) — paragraphe naturel, 3-4 lignes max
6. **Séparateur** — `─── PIÈCES À CONVICTION ───`
7. **Pièces à conviction** — liste à puces avec marqueurs `✗` (rouge) `⚠` (ambre) `✓` (vert)
8. **Séparateur** — `─── 5 DERNIÈRES TRANSACTIONS ───`
9. **Timeline** — tableau mono des transactions précédentes de la carte
10. **Footer actions** — boutons + raccourcis clavier annoncés

### Dimensions
- Largeur carte : `min(640px, 90vw)`
- Padding interne : `32px`
- Bordure : `1px solid var(--sepia)`
- Box-shadow : `0 2px 0 var(--pencil), 0 4px 12px rgba(0,0,0,0.08)` (subtle paper drop)

### Pile derrière
2-3 cartes en `position: absolute` derrière la carte principale, `translateY(8px) translateX(4px) rotate(0.5deg)`, z-index décroissant, opacity 0.6/0.3. Donne l'impression "il en reste à traiter".

---

## Comportement : Swipe Tinder

### Inputs
| Geste | Clavier | Résultat |
|---|---|---|
| Swipe gauche | `←` ou `A` | Classer fraude (rouge) |
| Swipe droite | `→` ou `D` | Innocenter (vert) |
| Swipe haut | `↑` ou `E` | Escalader (ambre) |
| Annuler | `Z` | Undo (carte précédente revient) |

### Animation de sortie
- **Gauche** : `transform: translateX(-120%) rotate(-15deg); opacity: 0;` en 400ms
- **Droite** : `transform: translateX(120%) rotate(15deg); opacity: 0;` en 400ms
- **Haut** : `transform: translateY(-120%); opacity: 0;` en 400ms
- Easing : `cubic-bezier(0.4, 0.0, 0.2, 1)`

### Tampon stamp
Pendant la sortie, un grand tampon (24px uppercase, border 4px, rotate -12deg, opacity 0.85) apparaît au centre de la carte avant qu'elle ne disparaisse :
- `FRAUDE` (rouge) sur swipe gauche
- `INNOCENT` (vert) sur swipe droite
- `ESCALADÉ` (ambre) sur swipe haut

### Drag souris/touch (Phase 2)
Implémenter via JS dans le composant HTML iframe. Pointer events `pointerdown/pointermove/pointerup`. Seuil de swipe : 30% de la largeur écran OU vélocité > 0.5 px/ms.

---

## Accessibilité (CRITICAL)

- **Tab order** matches visual order (top → bottom → footer buttons)
- **Focus rings** visibles : `outline: 2px solid var(--ink); outline-offset: 2px;`
- **Raccourcis clavier** affichés en permanence dans le footer
- **Contraste** : Ink (`#1A1A1A`) sur Paper (`#FDFBF7`) → 17.4:1 (AAA)
- **prefers-reduced-motion** : swipe devient un fade instantané sans translate
- **ARIA labels** sur les boutons (icon-only friendly)
- **Cursor pointer** sur tous les éléments cliquables

---

## Stack technique

### Libs Streamlit
- `streamlit-shortcuts` — raccourcis clavier A/D/E/Z
- `st.components.v1.html` — iframe pour la carte avec animation JS
- `st.session_state` — état (index courant, historique décisions)

### Anti-patterns techniques
- Pas de `streamlit-shadcn-ui` (vibe trop moderne)
- Pas de `plotly` pour la timeline (overkill, on fait du HTML/CSS pur)
- Pas de `streamlit-card` (pas assez customizable pour notre design)

---

## Pre-delivery checklist

- [ ] Police Space Mono chargée et fallback `monospace`
- [ ] Grain papier visible mais discret (12% max)
- [ ] Tampons rotate -12deg, jamais 0deg
- [ ] Animation swipe respecte `prefers-reduced-motion`
- [ ] Focus ring visible sur tab navigation
- [ ] Boutons keyboard shortcuts annoncés (label visuel)
- [ ] Contraste text ink sur paper > 4.5:1 (testé)
- [ ] Pile derrière visible (2-3 cartes fantômes)
- [ ] Undo fonctionne sur la dernière décision
- [ ] Test responsive : carte centrée à 1440px et 1024px (pas obligé < 768px)

---

## Pages overrides

À ajouter dans `design-system/fraud-hunter/pages/` si besoin de spécificités :
- `case-view.md` — la carte d'enquête (le principal écran)
- `intake.md` — l'écran d'upload du CSV
- `summary.md` — l'écran de fin (récap décisions)
