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

Sémantique (telle qu'appliquée sur les **cartes**) :
**rouge = critique / risque élevé / fraude**, **jaune = avertissement / risque moyen / escalader**,
**vert = ok / risque faible / légitime**.

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
| Critique (fraude, risque élevé) | `#B42318` | `#FEF3F2` | `#FECDCA` | `#D92D20` |
| Avertissement (escalader, risque moyen) | `#854D0E` | `#FEFCE8` | `#FDE68A` | `#CA8A04` |
| OK (légitime, risque faible) | `#067647` | `#ECFDF3` | `#ABEFC6` | `#17B26A` |

> **Note de cohérence (dette connue) :** le voile de swipe (`DIRS.fraud`) et le
> tableau de bord (`swipe_deck.py`) utilisent encore un **bleu** (`#1E40AF`) pour
> « fraude / élevé », là où les cartes utilisent le rouge ci-dessus. C'est un reste
> d'une ancienne direction, conservé volontairement pour l'instant. À aligner si on
> veut une cohérence parfaite (passer ces bleus au rouge `#D92D20`).

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
| Onglets | `inbox` (Révision) / `bar-chart` (Tableau de bord) |
| Actions | `arrow-left` / `arrow-up` / `arrow-right` |

---

## Composant : Carte Dossier

Rendue par `src/ui/cart_renderer_v2.py` (constante `CARD_CSS`, fonction
`render_card_inner`). Surface blanche, `border-radius: 16px`, ombre douce.
Anatomie (haut → bas) :

1. **Header** — avatar (icône carte) + `Dossier #ID` + compteur + **pill de risque** (couleur selon score)
2. **Métriques** — « Carte » / « Montant » + **jauge de score** (barre colorée selon risque)
3. **Analyse** — callout sobre avec le verdict en langage naturel (Gemini, ou repli)
4. **Signaux détectés** — lignes `icône · label · valeur (mono) · badge` (couleur par sévérité)
5. **Section basse adaptative** — change selon le **signal dominant** du dossier :
   - `montant` → historique de dépense de la carte
   - `poisson` → autres transactions sur le même terminal marchand (preuve du pic)
   - `vitesse` → chronologie de la rafale (card-testing)
   - `cross_card` → cartes liées au même marchand/appareil (réseau)

---

## Disposition du deck (écran de révision)

Rendu par `src/ui/swipe_deck.py` (JS vanilla dans une iframe `components.html`).
De haut en bas :

1. **Barre d'onglets** rectangulaire : `Révision` / `Tableau de bord` (boutons larges avec icône).
2. **Bannière d'apprentissage** (feedback) — verte (fiable) ou rouge (à risque), masquée par défaut.
3. **Barre d'actions** — **au-dessus de la carte** (toujours visible, sans scroll) : boutons
   Fraude / Escalader / Légitime + raccourcis + progression + bouton Annuler.
4. **Pile de cartes** (carte active + 2 fantômes derrière).

---

## Interaction : file de révision swipable

| Geste | Clavier | Décision |
|---|---|---|
| Swipe gauche | `A` / `←` | Fraude |
| Swipe haut | `E` / `↑` | Escalader |
| Swipe droite | `D` / `→` | Légitime |
| — | `Z` | Annuler la dernière décision |

- **Drag** : `translate` + légère rotation ; voile coloré + label selon direction/intensité.
- **Seuil** : relâchée au-delà de 110 px → la carte s'envole ; sinon retour en place.
- **Undo** : la carte revient depuis le côté de sa sortie.
- **Fin de file** : récap par décision + **export JSON** (rapport d'audit) + recommencer.

### Boucle de feedback (bidirectionnelle)
- **2 « légitime »** d'une même catégorie → catégorie **fiable** → flags similaires restants **dépriorisés** (drapeau vert, carte atténuée).
- **2 « fraude »** d'une même catégorie → catégorie **à risque confirmé** → flags similaires **remontés** (drapeau rouge).
- Recalculée depuis l'état → cohérente avec l'undo. Bannière + ligne du dashboard se colorent en conséquence.

---

## Accessibilité

- Contraste texte principal `#101828` sur `#FFFFFF` ≈ 16:1 (AAA).
- Toutes les actions au clavier (A/D/E/Z + flèches) **et** à la souris (boutons en haut).
- Le drag est une amélioration ; boutons + clavier restent le chemin principal.
- Valeurs longues tronquées en ellipse (jamais de débordement).
- Sidebar `Réglages` ouverte par défaut (`initial_sidebar_state="expanded"`) ; on ne cache que `stToolbarActions` (pas tout le header) pour garder le bouton de réouverture.

---

## Stack technique

- **Streamlit** + `st.components.v1.html` (iframe isolée) pour la carte/deck.
- Tout le HTML/CSS/JS de la carte est **self-contained** dans l'iframe. JS vanilla, pas de build.

### Anti-patterns techniques
- Pas de `plotly` pour les historiques (HTML/CSS pur suffit).
- Pas de composants Streamlit « lourds » qui imposeraient un autre langage visuel.

---

## Pre-delivery checklist

- [ ] Inter + IBM Plex Mono chargées (fallback `sans-serif` / `monospace`)
- [ ] Aucune icône emoji (Lucide SVG uniquement)
- [ ] Palette des cartes respectée : rouge/jaune/vert par sévérité
- [ ] Boutons d'action visibles **au-dessus** de la carte (pas de scroll pour agir)
- [ ] Boutons ET clavier ET drag fonctionnent
- [ ] Undo activé seulement s'il y a un historique
- [ ] Feedback bidirectionnel visible (bannière verte/rouge)
- [ ] Valeurs longues tronquées (pas de débordement)
- [ ] État vide géré (file sans dossier)
- [ ] Sidebar ouverte par défaut et ré-ouvrable après fermeture

---

## Historique des directions

- **v1–v2 (abandonnée)** : « paper detective » — chemise manille, tampons, post-it manuscrit. Jugée trop *cartoon*.
- **v3 (pro)** : refonte sobre (Linear/Stripe). Palette initiale bleu/jaune/vert.
- **v4 (actuelle)** : carte `cart_renderer_v2` avec section basse adaptative + palette **rouge**/jaune/vert ; onglets nav-bar ; barre d'actions en haut ; feedback bidirectionnel.
