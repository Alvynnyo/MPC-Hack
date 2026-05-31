# Implementation Plan — Fraud Hunter

## Stack

- **Python 3.11+**, **pandas** / **numpy** / **scipy** (détection, 1 000 lignes en mémoire)
- **Streamlit** (UI) + carte/deck en **HTML/CSS/JS vanilla** dans une iframe (`components.html`)
- **Google Gemini** (`gemini-2.5-flash`) pour les explications, avec repli sans clé
- Persistance par fichiers : `audit_log.json`, `data/explanations_cache.json`, `data/transactions_scored.csv`
- **pytest** pour les tests

## Architecture

```
 transactions.csv
        │
        ▼
 profiling.py            profils par carte / device / IP / marchand
        │
        ▼
 detection/              s1 montant (z-score) · s2 burst Poisson
   layer1..layer4        s3 siphon · s4 cross-card (fenêtre marchand 2h)
        │
        ▼
 scoring.py              final_score = Σ wi·si  + boost account-takeover
        │                flag si final_score ≥ seuil ; tri décroissant
        ▼
 pipeline.py             orchestration détection → scoring (run_pipeline)
        │
        ▼
 controler.py            mappe chaque transaction signalée en CaseFile
        │  (+ explanations.py : verdicts Gemini, mis en cache)
        ▼
 ui/ (Streamlit)         swipe_deck.py / cart_renderer_v2.py — file de révision
        │                + tableau de bord + feedback loop + export
        ▼
 feedback.py / audit.py  modificateurs en session · audit_log.json
```

## Découpage des modules

| Module | Rôle |
|---|---|
| `src/profiling.py` | Statistiques de référence par carte / device / IP / marchand |
| `src/detection/layer1_amount.py` | Écart de montant (z-score médiane/IQR par carte) |
| `src/detection/layer2_poisson.py` | Rythme improbable (p-value Poisson, marchand + carte) |
| `src/detection/layer3_burst.py` | Siphonnement (rafale sur fenêtre courte, catégories à risque) |
| `src/detection/layer4_cross_card.py` | Cartes distinctes sur un marchand en 2 h |
| `src/scoring.py` | Somme pondérée + boost + application du feedback + seuil |
| `src/explanations.py` | Verdicts Gemini, parallélisés, cache disque, repli sans clé |
| `src/pipeline.py` | Enchaîne détection → scoring |
| `src/controler.py` | Construit la file de `CaseFile` consommée par l'UI |
| `src/feedback.py` | `FeedbackManager` : modificateurs catégorie/device en session |
| `src/audit.py` | Audit log JSON (load / append / undo) |
| `src/ui/app.py` | Page Streamlit : sidebar cost-aware, deck, import des décisions |
| `src/ui/swipe_deck.py` | Deck swipable (JS vanilla) : onglets, barre d'actions en haut, dashboard, feedback |
| `src/ui/cart_renderer_v2.py` | Rendu HTML/CSS d'une carte (section basse adaptative au signal dominant) |
| `src/ui/mock_data.py` / `INTERFACE.md` | Dataclasses + données mock ; contrat UI ↔ backend |

Le contrat UI ↔ backend est figé dans [`src/ui/INTERFACE.md`](src/ui/INTERFACE.md)
(forme des `CaseFile` consommés, forme des décisions émises).

## Choix assumés (et ce qu'on a sciemment laissé de côté)

- **Règles statistiques, pas de ML** : 1 000 lignes sans labels → des règles transparentes qu'on peut défendre en démo valent mieux qu'une boîte noire.
- **Score pondéré + seuil ajustable** plutôt que des seuils en dur : permet le cost-aware tuning.
- **Boucle de feedback bidirectionnelle côté client** (dans le deck) : 2 « légitime » → catégorie fiable (dépriorise), 2 « fraude » → catégorie à risque (remonte). Visible, sans latence ; export JSON pour la persistance serveur.
- **Pas de pont iframe→Python automatique** : on passe par un export/import JSON (robuste, zéro dépendance) plutôt qu'un composant bidirectionnel à builder.
- **Cache disque des explications** pour ne pas re-payer l'API à chaque session.

## Répartition de l'équipe

| Personne | Domaine | Fichiers |
|---|---|---|
| P1 | Détection | `profiling.py`, `detection/*`, tests détection |
| P2 | Scoring / LLM | `scoring.py`, `explanations.py` |
| P3 | UI | `ui/*` (carte, deck, dashboard, feedback, export) |
| P4 | Intégration / Docs | `pipeline.py`, `controler.py`, `feedback.py`, `main.py`, docs |
