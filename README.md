# Fraud Hunter — MPC Hacks 2026 (Track Valsoft)

Un outil de détection de fraude par carte de crédit avec une UX type "dossier d'enquête".

## Quick start

```bash
pip install -r requirements.txt
streamlit run src/ui/app.py
```

## Structure du projet

```
MPC-Hack/
├── PLAN.md                  # Plan complet du projet (à lire avant tout)
├── PRD.md                   # Product Requirements Doc
├── IMPLEMENTATION.md        # Architecture et choix techniques
├── HYPOTHESES.md            # Journal des hypothèses testées
├── data/
│   └── transactions.csv     # Dataset (à déposer ici)
├── src/
│   ├── profiling.py         # [P1] Profilage par carte/device/IP/marchand
│   ├── detection/           # [P1] 4 couches de détection
│   │   ├── layer1_amount.py
│   │   ├── layer2_velocity.py
│   │   ├── layer3_burst.py
│   │   └── layer4_cross_card.py
│   ├── scoring.py           # [P2] Combinaison pondérée des couches
│   ├── explanations.py      # [P2] Génération d'explications via Claude API
│   ├── audit.py             # [P4] Audit log des décisions
│   └── ui/
│       └── app.py           # [P3] UI Streamlit "Dossier d'enquête"
└── tests/
    ├── test_profiling.py
    ├── test_detection.py
    └── test_scoring.py
```

## Qui fait quoi

| Rôle | Personne | Fichiers principaux |
|---|---|---|
| **P1 — Data** | TBD | `src/profiling.py`, `src/detection/*` |
| **P2 — Backend / LLM** | TBD | `src/scoring.py`, `src/explanations.py` |
| **P3 — Frontend** | TBD | `src/ui/app.py` |
| **P4 — Produit / Docs** | TBD | `src/audit.py`, `PRD.md`, `IMPLEMENTATION.md`, `HYPOTHESES.md` |

Voir [PLAN.md](PLAN.md) pour le plan détaillé.

## Stratégie de détection

Le système combine 4 couches indépendantes :

1. **Écart de montant** — montant >> médiane de la carte
2. **Vitesse impossible** — transactions in-person dans 2 pays en peu de temps
3. **Siphonnement rapide** — rafale de petites transactions sur des catégories à risque
4. **Fraude croisée** — même device/IP utilisé par >3 cartes (invisible sans vue cross-carte)

Chaque score est pondéré, l'utilisateur peut ajuster les poids via un slider (cost-aware tuning).

## If we had another week

À remplir en fin de hackathon.
