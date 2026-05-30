# Implementation Plan — Fraud Hunter

> **Statut :** Brouillon. À compléter par P4.

## Stack

- **Langage :** Python 3.11+
- **Données :** pandas (1000 lignes, en mémoire)
- **Détection :** scoring statistique, pas de ML
- **UI :** Streamlit (rapide à construire, navigation clavier OK)
- **LLM :** Claude API (Anthropic SDK) pour les explications
- **Persistance :** JSON (audit log), CSV (output flaggé)
- **Tests :** pytest

## Architecture

```
                 ┌─────────────────┐
 transactions.csv│  profiling.py   │  profils par carte / device / IP
                 └────────┬────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │  detection/                    │
         │  ├─ layer1_amount              │
         │  ├─ layer2_velocity            │  scores s1..s4
         │  ├─ layer3_burst               │
         │  └─ layer4_cross_card          │
         └────────────────┬───────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  scoring.py     │  fraud_score pondéré
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ explanations.py │  appel Claude API
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   ui/app.py     │  ◄── reviewer (clavier)
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   audit.py      │  audit_log.json
                 └─────────────────┘
```

## Division du travail (à valider)

| Personne | Domaine | Fichiers |
|---|---|---|
| P1 | Data | `src/profiling.py`, `src/detection/*`, `tests/test_profiling.py`, `tests/test_detection.py` |
| P2 | Scoring + LLM | `src/scoring.py`, `src/explanations.py`, `tests/test_scoring.py` |
| P3 | UI | `src/ui/app.py` |
| P4 | Glue + Docs | `src/audit.py`, `PRD.md`, `IMPLEMENTATION.md`, `HYPOTHESES.md`, README final |

## Ce qu'on a choisi de skip

- **ML supervisé** : 1000 lignes sans labels, ça n'a pas de sens. Règles statistiques transparentes > boîte noire qu'on ne sait pas défendre.
- **Stockage persistant complexe** : un JSON pour l'audit, un CSV pour la sortie. Pas de Postgres pour 1000 lignes.
- **Authentification** : un seul reviewer en demo, pas de login.
