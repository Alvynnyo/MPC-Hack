# Journal des hypothèses

Décisions de détection retenues, avec leur logique. Le F1 réel n'est pas
mesurable en local (clé de réponses cachée) — on documente donc la règle, le
réglage retenu, et l'effet observé sur l'ensemble signalé (nombre de flags).

---

### H01 — Écart de montant : z-score robuste plutôt que ratio brut (couche 1)

**Idée :** un montant anormal pour *cette* carte, pas dans l'absolu.

**Retenu :** z-score robuste `z = (amount − médiane) / (IQR × 0.7413)`, score =
`min(|z| / 6, 1)`. L'IQR×0.7413 estime l'écart-type sans être sensible aux
valeurs extrêmes (contrairement à la moyenne/écart-type classiques).

**Effet :** une transaction à 500 $ sur une carte habituée à 20 $ (IQR 10) →
score ≈ 1.0 ; une à 22 $ → score < 0.2. **Gardé.**

---

### H02 — Burst : test de Poisson plutôt qu'un simple comptage (couche 2)

**Idée :** un rythme de transactions *statistiquement* improbable signale un
terminal compromis (par marchand) ou du card-testing (par carte).

**Retenu :** p-value de Poisson sur deux fenêtres (marchand 2 h, carte 30 min),
score = `min(1, −log10(p) / 8)`, on prend le max des deux. Plus robuste qu'un
seuil « > N transactions » qui dépend du volume du marchand.

**Effet :** capte les bursts QuickPay multi-cartes et les rafales de micro-tx.
**Gardé.** C'est la couche au poids le plus fort (voir H05).

---

### H03 — Siphonnement : fenêtre glissante 10 min + catégories à risque (couche 3)

**Idée :** découpage d'un gros montant ou test de carte via micro-transactions.

**Retenu :** comptage sur fenêtre glissante de ±10 min par carte. `count ≥ 3`
→ +0.4 ; `count ≥ 5` → +0.3 (cumulatif) ; bonus +0.3 si `count ≥ 3` **et**
catégorie à risque (`gift_card`, `online_retail`). Score plafonné à 1.0.

**Effet :** 4 achats gift_card en 8 min → score > 0.6 ; 2 restos espacés de 2 h
→ < 0.2. **Gardé.**

---

### H04 — Fraude croisée : cartes distinctes par marchand, pas par device (couche 4)

**Idée initiale :** « un device utilisé par > K cartes ». **Abandonnée** car le
device n'est présent que pour les transactions `online` → angle mort sur le reste.

**Retenu :** nombre de cartes distinctes sur un même `merchant_name` dans une
fenêtre de ±2 h. `≥ 6` → 0.9 ; `≥ 4` → 0.7. Capte le pattern « invisible carte
par carte » même hors online.

**Effet :** 6 cartes sur un marchand en 2 h → score élevé ; 1 carte → 0.
**Gardé** (la version device-only a été jetée).

---

### H05 — Pondération des couches

**Idée :** toutes les couches ne se valent pas.

**Retenu :** `w1=0.20, w2=0.30, w3=0.25, w4=0.25` (le burst Poisson, le signal le
plus discriminant, pèse le plus). Les poids somment à 1.0 (validé par test).

**À creuser :** une vraie optimisation des poids nécessiterait un jeu étiqueté.

---

### H06 — Boost « account takeover »

**Idée :** un gros montant sur une catégorie liquide (revente facile) est
particulièrement suspect.

**Retenu :** `+0.05` au score final si `merchant_category ∈ {gift_card,
electronics}` **et** `s1 ≥ 0.8`. Petit coup de pouce ciblé, pas une couche à part.

**Gardé.**

---

### H07 — Seuil de signalement (cost-aware)

**Idée :** le seuil encode le compromis faux positif vs fraude manquée.

**Retenu :** seuil par défaut **0.28**, ajustable via un slider dans l'UI.

**Effet observé (ensemble signalé) :**

| Seuil | Transactions signalées |
|---|---|
| 0.20 | 112 |
| **0.28** | **69** |
| 0.40 | 46 |
| 0.50 | 36 |

Le brief annonce ~7 % de fraude (~70 transactions) : **0.28 → 69** est cohérent.
**Gardé** comme défaut, mais laissé réglable.
