# Contrat d'interface — UI (P3)

Ce document définit **ce que l'UI consomme** et **ce qu'elle produit**, pour que
les parties détection/scoring (P1/P2) et glue/audit (P4) puissent s'y brancher
sans modifier le code de l'UI.

L'UI ne fait **aucun calcul de fraude**. Elle affiche des objets `CaseFile` et
émet des décisions. Tant que la forme ci-dessous est respectée, l'UI fonctionne.

---

## 1. Ce que l'UI consomme : `CaseFile`

Défini dans `src/ui/mock_data.py`. L'écran de révision attend une **liste de
`CaseFile`**, déjà filtrée (uniquement les transactions signalées) et triée
(les plus risquées d'abord, idéalement).

```python
@dataclass
class CaseFile:
    case_id: str        # identifiant du dossier, ex. "0142"
    case_index: int     # position affichée, ex. 42  (pour "42 / 67")
    case_total: int     # total de dossiers signalés, ex. 67
    card_id: str        # ex. "card_042"
    amount: float       # montant de la transaction (CAD)
    score: float        # score de risque, 0.0 → 1.0
    risk_label: str     # "ÉLEVÉ" | "MOYEN" | "FAIBLE"
    verdict: str        # explication en langage naturel (Gemini) — 2-4 phrases
    merchant_category: str = ""   # ex. "online_retail" — clé du feedback loop (voir §4)
    evidence: list[Evidence]      # signaux détectés (voir ci-dessous)
    previous: list[PreviousTx]    # historique récent de la carte
```

> **`merchant_category`** alimente la boucle de feedback (§4). **Branché** :
> `controler.py` le renseigne via `merchant_category=ctx.merchant_category`.
> Sans lui, l'apprentissage en session n'aurait pas de clé de similarité.

**Attributs dynamiques** (posés par `controler.py` après construction, lus par
`cart_renderer_v2.py` pour la section basse adaptative — optionnels, valeurs par
défaut sûres) :

```python
case.dominant_signal = "montant" | "poisson" | "vitesse" | "cross_card"
case.merchant        = "Amazon.ca"        # nom du marchand
case.merchant_data   = [ ... ]            # autres tx sur le terminal (signal "poisson")
case.device_data     = [ ... ]            # cartes liées à l'appareil (signal "cross_card")
```

```python
@dataclass
class Evidence:
    label: str     # ex. "Device", "IP", "Montant", "Vitesse"
    value: str     # ex. "dev_a3f9c821", "89.234.117.42", "890.00 $"
    tag: str       # libellé court du badge, ex. "JAMAIS VU", "14× MÉDIANE"
    severity: str  # "critical" | "warning" | "info"

@dataclass
class PreviousTx:
    date: str       # ex. "05-01 02:47"  (format libre, affiché tel quel)
    merchant: str   # ex. "Amazon.ca"
    amount: float   # montant (CAD)
    status: str     # "ok" | "suspect" | "current"
                    # "current" = la transaction du dossier en cours
```

### Règles de mapping (côté producteur P1/P2)

- `score` ∈ [0, 1]. La couleur de la jauge/pill est dérivée automatiquement
  (`cart_renderer_v2._risk_tokens`) : `≥ 0.60` élevé (rouge), `≥ 0.40` moyen
  (jaune), sinon faible (vert).
- `risk_label` doit être cohérent avec `score` (texte affiché tel quel).
- `severity` d'un `Evidence` pilote la couleur du badge et de l'icône :
  - `critical` → rouge (signal fort : device/IP partagé, rafale, montant ≥ 0.8…)
  - `warning` → jaune (signal modéré : montant atypique, heure, pays…)
  - `info` → vert (élément rassurant : device connu, montant normal…)
- `previous` : mettre **exactement une** entrée à `status="current"`
  (la transaction analysée) ; les autres en `"ok"` ou `"suspect"`.

### Point d'entrée (branché)

`controler.initialize_fraud_queue(csv_path, threshold, feedback_manager)`
renvoie la `list[CaseFile]` triée par score. Elle enchaîne :

1. `pipeline.run_pipeline(...)` → transactions signalées (scoring + seuil) ;
2. `explanations.precompute_explanations(...)` → `{transaction_id: verdict}` (cache disque) ;
3. mapping en `CaseFile` (+ `Evidence`, `PreviousTx`, attributs dynamiques).

`src/ui/app.py` l'appelle directement (via `@st.cache_data`, clé = seuil) ;
`MOCK_CASES` ne sert plus que pour les aperçus de dev hors pipeline.

---

## 2. Ce que l'UI produit : les décisions

Pour chaque dossier, l'analyste choisit une décision parmi :

| Décision | Valeur émise | Geste / touche |
|---|---|---|
| Fraude confirmée | `"fraud"` | swipe gauche / `A` / `←` |
| À escalader | `"escalate"` | swipe haut / `E` / `↑` |
| Légitime | `"legit"` | swipe droite / `D` / `→` |

Aujourd'hui, les décisions sont accumulées **côté client** (dans l'iframe) et
exportables en **JSON** depuis l'écran de fin (voir plus bas).

### Boucle de feedback — partie LIVE (côté client, faite)

Implémentée dans `swipe_deck.py`. **Elle apprend dans les deux sens**, par
`merchant_category` (clé fournie par le `CaseFile`) :

| Déclencheur (en session) | Effet sur les dossiers similaires restants |
|---|---|
| **2 « légitime »** d'une même catégorie | catégorie jugée **fiable** → flags similaires **dépriorisés** (drapeau vert, carte atténuée) |
| **2 « fraude »** d'une même catégorie | catégorie **à risque confirmé** → flags similaires **remontés en priorité** (drapeau rouge) |

> ⚠️ Important : c'est le sens **fraude** qui rend la boucle visible dans une
> file de fraude réelle (le réviseur clique surtout « Fraude »). Le sens
> légitime sert à faire taire les faux positifs récurrents.

Une **bannière** (verte = fiable / rouge = à risque) et une ligne du **tableau
de bord** reflètent l'état. Tout est **recalculé depuis l'état** (décisions +
position) à chaque changement → automatiquement cohérent avec l'undo. Seuils :
`TRUST_LEGIT = TRUST_FRAUD = 2`. Aucune dépendance backend.

### Boucle de feedback — partie EXPORT / IMPORT vers Python (faite)

À la fin de la file, l'UI exporte un **rapport JSON** (`decisions.json`) :

```json
[
  {
    "case_id": "tx_000998",
    "card_id": "card_046",
    "score": 0.75,
    "category": "online_retail",
    "decision": "fraud"          // "fraud" | "escalate" | "legit" | null
  }
]
```

Côté serveur, `app.py` (`render_decision_importer`) le réimporte via un
`st.file_uploader` et le rejoue : `FeedbackManager.record_decision()` met à jour
les modificateurs (legit→`Innocenter`, fraud→`Classer`) et `audit.log_decision()`
persiste l'audit log. Le transport est donc un **export → upload** (robuste,
sans dépendance) plutôt qu'un pont iframe→Streamlit automatique.

---

## 3. Résumé des responsabilités

| Qui | Produit | Consomme |
|---|---|---|
| P1 / P2 | `list[CaseFile]` (via `load_cases()`) | — |
| **P3 (UI)** | décisions (`case_id` → `fraud/escalate/legit`) | `list[CaseFile]` |
| P4 | audit log, feedback | décisions de l'UI |

Tant que `load_cases()` renvoie des `CaseFile` bien formés, l'UI est plug-and-play.
