# PRD — Fraud Hunter

## Utilisateur cible

Un analyste de l'équipe Trust & Safety d'une compagnie de paiement. Il triage
chaque jour des transactions signalées et doit trancher vite et juste.

## Problème

L'analyste ne peut pas tout regarder. Chaque erreur coûte : un faux positif
froisse un client légitime, un faux négatif laisse passer de la fraude. Il lui
faut un outil qui **priorise**, **explique**, et **apprend** de ses décisions.

## Ce qu'on construit

Un outil de bout en bout qui :

1. **Ingère** `transactions.csv` (1 000 transactions, 50 cartes, 1 mois).
2. **Détecte** la fraude via 4 couches complémentaires → score pondéré → ~69 transactions signalées.
3. **Explique** chaque signalement par un verdict en langage naturel (Gemini), avec repli si pas de clé API.
4. **Présente** une file de révision type Tinder : une carte à la fois, swipe / clavier (`←/A` fraude, `→/D` légitime, `↑/E` escalader, `Z` annuler), undo.
5. **Récapitule** dans un tableau de bord : KPIs (taux de fraude, temps moyen), restants par importance, traités par décision.
6. **Apprend en session (feedback bidirectionnel)** : 2 « légitime » sur une catégorie ⇒ flags similaires dépriorisés ; 2 « fraude » ⇒ flags similaires remontés en priorité. En direct.
7. **Trace et exporte** : décisions exportables (JSON), réimportables côté serveur → audit log persistant + modificateurs de scoring.
8. **Cost-aware** : un slider « seuil de signalement » montre en direct comment la file grossit/rétrécit selon le compromis faux positif / fraude manquée.

## Succès

- Un ensemble de ~69 transactions signalées (≈ les ~7 % de fraude attendus), trié par risque.
- Un réviseur non-technique triage une file sans formation, au clavier.
- Chaque signalement porte une raison lisible.
- L'app se lance en une commande depuis un clone propre (`python -m streamlit run src/ui/app.py`).
- Boucle de feedback + audit log fonctionnels (bonus du brief).

## Hors-scope explicite

- Pas de détection temps réel — outil batch sur un CSV.
- Pas de modèle ML supervisé — pas de labels ; on assume des règles transparentes et défendables.
- Pas de multi-utilisateurs / authentification.
- Pas de base de données — fichiers JSON (audit, cache) et CSV.
- Pas de mobile — desktop (la carte reste lisible de 1024 à 1440 px).
