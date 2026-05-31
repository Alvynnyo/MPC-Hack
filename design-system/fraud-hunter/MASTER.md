# Design System Master File — Fraud Hunter

> **LOGIC:** When building a specific page, first check `design-system/fraud-hunter/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Fraud Hunter — MPC Hacks 2026 (Track Valsoft)
**Direction visuelle :** Outil de triage professionnel (style Linear / Stripe / Mercury)
**Interaction signature :** file de révision swipable (type Tinder), une carte à la fois

---

## Identité visuelle

Un outil de revue de fraude clair, sobre et crédible. L'analyste passe en revue
des dossiers signalés, un à la fois, et tranche (fraude / légitime / escalader)
au clavier ou en swipant la carte. Esthétique fond clair, typographie nette,
icônes vectorielles — aucun effet « gadget ».

### Anti-vibes (à éviter)
- **Pas** de fond sombre (le canvas est clair)
- **Pas** d'emojis comme icônes (icônes SVG Lucide uniquement)
- **Pas** de police manuscrite / décorative
- **Pas** de gradients voyants, de tampons, de scotch, de texture papier
- **Pas** de violet/rose « vibe IA »
- **Pas** d'animation qui déplace le layout (scale au hover, etc.)

---

## Palette de couleurs

Sémantique : **bleu sombre = critique/fraude**, **jaune clair = avertissement/escalader**,
**vert = ok/légitime**. Le rouge n'est pas utilisé.

| Rôle | Hex |
|---|---|
| Canvas (fond app) | `#F2F4F7` |
| Surface (cartes) | `#FFFFFF` |
| Bordure | `#E4E7EC` |
| Bordure forte | `#D0D5DD` |
| Texte principal | `#101828` |
| Texte secondaire | `#475467` |
| Texte tertiaire | `#98A2B3` |

### Couleurs sémantiques (badges, jauge, boutons)

| Niveau | Texte (fg) | Fond (bg) | Bordure | Accent/jauge |
|---|---|---|---|---|
| Critique (fraude, risque élevé) | `#1E3A8A` | `#EFF4FF` | `#C7D7FE` | `#1E40AF` |
| Avertissement (escalader, risque moyen) | `#854D0E` | `#FEFCE8` | `#FDE68A` | `#CA8A04` |
| OK (légitime, risque faible) | `#067647` | `#ECFDF3` | `#ABEFC6` | `#17B26A` |

---

## Typographie

| Usage | Police |
|---|---|
| Texte, titres, UI | **Inter** (400/500/600/700) |
| Chiffres, IDs, montants, scores | **IBM Plex Mono** (tabular-nums) |

Import :
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
```

---

## Iconographie

Icônes **Lucide** en SVG inline (stroke `currentColor`, width 2). Jamais d'emoji.

| Sens | Icône Lucide |
|---|---|
| Signal critique | `x-circle` |
| Signal avertissement | `alert-triangle` |
| Signal ok | `check-circle` |
| Carte bancaire (avatar) | `credit-card` |
| Actions | `arrow-left` / `arrow-up` / `arrow-right` |

---

## Composant : Carte Dossier

Surface blanche, `border-radius: 16px`, ombre douce en couches. Anatomie
(haut → bas) :

1. **Header** — avatar (icône carte) + `Dossier #ID` + compteur + **pill de risque** (couleur selon score)
2. **Métriques** — cartes « Carte » / « Montant » + **jauge de score** (barre colorée selon risque)
3. **Analyse IA** — callout sobre (bordure gauche bleue) avec le verdict en langage naturel
4. **Signaux détectés** — lignes `icône · label · valeur (mono) · badge` (couleur par sévérité)
5. **Historique récent** — table des transactions précédentes, ligne courante surlignée (bleu)

Tokens : voir `src/ui/case_card.py` (constante `CARD_CSS`, fonction `render_card_inner`).

---

## Interaction : file de révision swipable

Implémentée dans `src/ui/swipe_deck.py` (JS vanilla dans une iframe `components.html`).

| Geste | Clavier | Décision | Couleur |
|---|---|---|---|
| Swipe gauche | `A` / `←` | Fraude | bleu `#1E40AF` |
| Swipe haut | `E` / `↑` | Escalader | jaune `#CA8A04` |
| Swipe droite | `D` / `→` | Légitime | vert `#17B26A` |
| — | `Z` | Annuler la dernière décision | — |

- **Pile** : 2 cartes fantômes décalées derrière la carte active.
- **Drag** : `translate` + légère rotation ; un voile coloré + un label apparaissent selon la direction et l'intensité.
- **Seuil** : relâchée au-delà de 110 px → la carte s'envole ; sinon retour en place.
- **Undo** : la carte revient depuis le côté de sa sortie.
- **Fin de file** : écran récapitulatif (compteur par décision) + export CSV + recommencer.

---

## Accessibilité

- Contraste texte principal `#101828` sur `#FFFFFF` ≈ 16:1 (AAA).
- Focus visible : `outline: 2px solid #1E40AF; outline-offset: 2px;`.
- Toutes les actions sont accessibles au clavier (A/D/E/Z + flèches) **et** à la souris (boutons).
- Le drag (pointer events) est une amélioration ; boutons + clavier restent le chemin principal.
- Les valeurs longues tronquent en ellipse (jamais de débordement).

---

## Stack technique

- **Streamlit** + `st.components.v1.html` (iframe isolée) pour la carte/deck.
- Tout le HTML/CSS/JS de la carte est **self-contained** dans l'iframe.
- `streamlit-shortcuts` disponible si l'on doit remonter des raccourcis au niveau Streamlit (non requis pour le deck, qui gère son propre clavier).
- Pas de framework JS, pas de build : JS vanilla.

### Anti-patterns techniques
- Pas de `plotly` pour l'historique (HTML/CSS pur suffit).
- Pas de composants Streamlit « lourds » qui imposeraient un autre langage visuel.

---

## Pre-delivery checklist

- [ ] Inter + IBM Plex Mono chargées (fallback `sans-serif` / `monospace`)
- [ ] Aucune icône emoji (Lucide SVG uniquement)
- [ ] Palette respectée : bleu/jaune/vert, pas de rouge ni de violet
- [ ] Focus visible au clavier
- [ ] Boutons ET clavier ET drag fonctionnent
- [ ] Undo activé seulement s'il y a un historique
- [ ] Valeurs longues tronquées (pas de débordement)
- [ ] État vide géré (file sans dossier)
- [ ] Carte centrée et lisible de 1024 px à 1440 px

---

## Historique des directions

- **v1–v2 (abandonnée)** : « paper detective » — chemise manille, tampons, post-it manuscrit, swipe Tinder ludique. Jugée trop *cartoon* / pas assez pro.
- **v3+ (actuelle)** : refonte professionnelle (ce document). Le swipe est conservé mais en version sobre.
