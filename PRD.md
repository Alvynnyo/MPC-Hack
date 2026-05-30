# PRD — Fraud Hunter

> **Statut :** Brouillon. À compléter par P4.

## Utilisateur cible

Un analyste de l'équipe Trust & Safety d'une compagnie de paiement.

## Problème

Cet analyste reçoit chaque jour des milliers de transactions à triager. Il ne peut pas tout regarder, et chaque mauvaise décision coûte cher (faux positif = client perdu, faux négatif = fraude qui passe).

## Ce qu'on construit

Un outil qui :

- Ingère un CSV de transactions
- Identifie les transactions suspectes selon 4 patterns connus de fraude
- Présente chaque cas suspect comme un "dossier d'enquête" avec contexte complet
- Permet une décision rapide au clavier (approuver / innocenter / escalader)
- Trace toutes les décisions dans un audit log

## Succès

- F1 > 0.85 sur le jeu de test caché
- Un reviewer non-technique peut triager 50 cas en 10 minutes sans formation
- Chaque flag est accompagné d'une raison lisible en français
- L'app se lance avec une seule commande depuis un clone propre

## Hors-scope explicite

- Pas de détection temps réel — c'est un outil batch
- Pas de modèle ML supervisé — pas de labels disponibles
- Pas de multi-utilisateurs
- Pas de base de données — fichiers JSON et CSV
- Pas de mobile / responsive — desktop only
