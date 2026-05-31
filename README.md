# Fraud Hunter — MPC Hacks 2026 (Track Valsoft)

Outil de détection de fraude par carte de crédit + **file de révision** pour un
analyste : une carte à la fois, swipe / clavier, explications en langage naturel,
tableau de bord et **boucle de feedback** en session.

## Quick start

```bash
pip install -r requirements.txt

# (optionnel) clé Gemini pour de vraies explications IA ; sans clé, un verdict
# de repli est affiché — l'app fonctionne quand même.
cp .env.example .env        # puis renseigner GEMINI_API_KEY

# Lancer l'interface (une commande, depuis la racine)
python -m streamlit run src/ui/app.py
```

Rapport de détection en ligne de commande (sans UI) :

```bash
python main.py              # affiche les transactions flaggées + exporte data/transactions_scored.csv
```

Tests :

```bash
python -m pytest -q
```

## Ce que fait l'outil

1. **Ingestion** de `data/transactions.csv` (1 000 transactions, 50 cartes, 1 mois).
2. **Détection** : 4 couches indépendantes → score pondéré → ~69 transactions flaggées.
3. **Explication** : chaque flag reçoit un verdict en langage naturel (Gemini).
4. **Révision** : file type Tinder — `←/A` fraude, `→/D` légitime, `↑/E` escalader, `Z` annuler.
5. **Tableau de bord** : KPIs (taux de fraude, temps moyen), restants par importance, traités par décision.
6. **Boucle de feedback** : innocenter 2 cas d'une même catégorie ⇒ les flags similaires restants sont dépriorisés en direct.
7. **Audit / export** : décisions exportables (JSON), réimportables côté serveur → `audit_log.json` + modificateurs de scoring.

## Stratégie de détection

Score final = somme pondérée de 4 couches (`final_score = w1·s1 + w2·s2 + w3·s3 + w4·s4`),
plus un *boost* « account takeover » (gros montant + catégorie à risque), flag si
`final_score ≥ seuil` (défaut 0.28).

| Couche | Cible | Idée |
|---|---|---|
| **s1 — Montant** | Achat anormal pour la carte | z-score sur la médiane/IQR par carte |
| **s2 — Burst (Poisson)** | Terminal compromis / card-testing | rythme de transactions improbable vs taux normal (p-value Poisson) |
| **s3 — Siphonnement** | Micro-transactions répétées | rafale sur fenêtre courte, catégories à risque (gift_card, online_retail) |
| **s4 — Fraude croisée** | 1 dispositif → plusieurs cartes | nombre de cartes distinctes sur un même marchand dans une fenêtre de 2 h |

La file est triée par score décroissant. Les poids/seuil sont ajustables (cost-aware) depuis l'UI.

## Structure du projet

```
MPC-Hack/
├── main.py                      # pipeline de détection en CLI + export CSV
├── data/
│   ├── transactions.csv         # dataset d'entrée
│   └── transactions_scored.csv  # sortie annotée (s1..s4, final_score, is_flagged)
├── src/
│   ├── profiling.py             # [P1] profils par carte / device / IP / marchand
│   ├── detection/               # [P1] 4 couches (layer1_amount, layer2_poisson, layer3_burst, layer4_cross_card)
│   ├── scoring.py               # [P2] score pondéré + boost + feedback
│   ├── explanations.py          # [P2] verdicts en langage naturel (Gemini)
│   ├── pipeline.py              # orchestration détection → scoring
│   ├── controler.py             # construit la file de CaseFile pour l'UI
│   ├── feedback.py              # FeedbackManager (modificateurs en session)
│   ├── audit.py                 # audit_log.json (load / append / undo)
│   └── ui/                      # [P3] app.py, swipe_deck.py, case_card.py, mock_data.py, INTERFACE.md
├── tests/                       # pytest (profiling, détection, scoring)
├── design-system/               # référence visuelle (MASTER.md)
└── PLAN.md / PRD.md / IMPLEMENTATION.md / HYPOTHESES.md
```

## If we had another week

- **Brancher le feedback live sur les vraies données** : exposer `merchant_category` (et `device_id`) dans `controler.py` pour que la boucle apprenne aussi hors mock.
- **Pont iframe → Python automatique** (composant bidirectionnel) pour enregistrer les décisions sans étape d'export/import.
- **Cache disque des explications** pour un démarrage instantané (aujourd'hui recalculé par session).
- **Calibration des seuils sur un jeu étiqueté** pour mesurer un vrai F1 et optimiser les poids.
- **Receipt / preuve par décision** plus riche dans l'audit (features ayant déclenché le flag).
