# Plan — Fraud Hunter (Track Valsoft, MPC Hacks 2026)

> **Approche choisie : A + B**
> Moteur de détection statistique solide (pandas, scoring par carte + cross-carte) + UX type **"Dossier d'enquête"** où chaque flag est une affaire à instruire, avec explications en langage naturel générées par Claude API.

---

## Vue d'ensemble

Le système fait trois choses, dans cet ordre :

1. **Profiler** chaque carte (comportement normal) et chaque entité partagée (devices, IPs, marchands).
2. **Scorer** chaque transaction selon 4 patterns de fraude, combinés en un score final pondéré.
3. **Présenter** les transactions suspectes au reviewer dans une UI type "dossier d'enquête" — une affaire à la fois, navigation clavier, décisions tracées.

---

## Étape 1 — Profilage (comportement normal)

L'objectif de cette étape est de **comprendre le comportement normal avant de chercher les anomalies**. Aucune transaction n'est filtrée ici — on construit seulement des profils de référence qui serviront aux couches de détection.

### 1.1 Profil par carte (`card_id`)

Pour chaque carte, on calcule :

- Nombre total de transactions
- Montant moyen, médian, maximal
- Pays habituel du marchand
- Catégories de marchands les plus fréquentes
- Canaux utilisés (online, in_person, atm)
- Liste des devices et IPs déjà vus pour cette carte

Cela permet ensuite de détecter des phrases du type *"cette transaction est 12× la dépense habituelle de cette carte"*.

### 1.2 Profil par device (`device_id`)

Pour chaque device :

- Nombre de cartes distinctes l'ayant utilisé
- Nombre total de transactions
- Montant total traité

**Signal :** un device utilisé par beaucoup de cartes distinctes est suspect.

### 1.3 Profil par IP (`ip_address`)

Même logique :

- Nombre de cartes distinctes ayant utilisé cette IP
- Nombre total de transactions

**Signal :** une IP utilisée par 8+ cartes différentes est un signal fort.

### 1.4 Profil par marchand (`merchant_name`)

- Marchands utilisés par beaucoup de cartes
- Marchands avec des montants anormalement élevés

*Note : cette analyse est moins prioritaire — à inclure seulement si le temps le permet.*

---

## Étape 2 — Détection : 4 couches en parallèle

Chaque transaction est passée à travers 4 couches indépendantes. Chacune cible un pattern de fraude distinct et retourne un score entre 0 et 1.

### Couche 1 — Écart de montant anormal

**Ce qu'elle cherche :** une transaction dont le montant explose par rapport aux habitudes du propriétaire de la carte.

**Exemple :** une carte qui paie habituellement 12$ de café fait soudainement un achat de 1 500$ chez Best Buy.

**Indicateur :** `amount > N × médiane(card_id)`, avec N à calibrer (5–15).

### Couche 2 — Vitesse impossible

**Ce qu'elle cherche :** une carte utilisée physiquement dans deux pays différents dans un laps de temps trop court pour un être humain.

**Indicateur :** deux transactions consécutives avec le même `card_id`, `channel = in_person`, où `merchant_country` change en moins de quelques heures.

### Couche 3 — Siphonnement rapide

**Ce qu'elle cherche :** un fraudeur qui teste la carte avec des micro-transactions répétitives, ou qui découpe un gros montant pour éviter de déclencher le plafond.

**Indicateur :** rafale de transactions (> 3) sur 10 minutes pour le même `card_id`, montants proches ou identiques, catégories à risque (`gift_card`, `online_retail`).

### Couche 4 — Fraude croisée (cross-card)

**Ce qu'elle cherche :** un fraudeur professionnel qui utilise un seul appareil/téléphone pour vider plusieurs cartes volées. **Pattern invisible si on regarde les cartes une par une.**

**Indicateur :** un même `device_id` ou `ip_address` associé à plus de 3 `card_id` distincts dans le dataset.

**Exemple :** l'IP `192.168.1.55` fait des achats en ligne avec 6 cartes différentes en 2 heures.

---

## Étape 3 — Score final pondéré

Les 4 scores sont combinés via une moyenne pondérée :

```
fraud_score = w1·s1 + w2·s2 + w3·s3 + w4·s4
avec w1 + w2 + w3 + w4 = 1
```

Les poids `w1..w4` sont **ajustables via un slider dans l'UI** ("coût d'un faux positif vs fraude manquée"). C'est le bonus "cost-aware tuning" demandé par le brief.

Une transaction est flaggée si `fraud_score > seuil` (seuil par défaut à calibrer).

---

## Étape 4 — Génération d'explication (Claude API)

Pour chaque transaction flaggée, on appelle Claude API avec les features (montants, déviations, devices, IPs, etc.) pour générer **une explication en langage naturel** :

> *"card_042 — Risque élevé (0.91). Cette carte fait habituellement des achats entre 20$ et 80$ dans des restaurants canadiens. Ce soir : 4 transactions sous 5$ sur un nouveau marchand en ligne entre 2h et 3h du matin, suivies d'un achat Amazon de 890$. Schéma classique de card-testing avant exploitation."*

Toutes les explications sont **pré-générées à l'ingestion** pour éviter la latence pendant la demo.

---

## Étape 5 — UI "Dossier d'enquête"

Pas de tableau de 1000 lignes. Le reviewer ouvre **un dossier à la fois**, navigation clavier, et passe au suivant après décision.

### Structure d'un dossier

Chaque transaction flaggée s'affiche comme un **Case #XXX** avec :

- **En-tête :** ID de transaction, carte, score, niveau de risque
- **Verdict IA :** explication en langage naturel (Claude)
- **Pièces à conviction :**
  - Le montant comparé à la médiane de la carte
  - Le device (connu / nouveau)
  - L'IP (connue / nouvelle / étrangère)
  - La catégorie de marchand (habituelle / atypique)
  - Le pays (habituel / nouveau)
- **Timeline visuelle** des 5 transactions précédentes de la carte
- **Boutons :**
  - `[A]` Classer (approuver — fraude confirmée)
  - `[D]` Innocenter (faux positif)
  - `[E]` Escalader (besoin d'une enquête plus poussée)
- **Undo** (`[Z]`) pour revenir sur la décision précédente

### Feedback loop intra-session

Chaque décision du reviewer est tracée et **influence les seuils en temps réel** :

- Plusieurs "Innocenter" sur des transactions de catégorie X → le poids de cette catégorie baisse
- Plusieurs "Classer" sur un même device → le score lié à ce device monte

C'est le bonus "feedback loop" du brief.

### Audit log

Chaque décision est écrite dans un fichier `audit_log.json` avec :

- Timestamp de la décision
- ID de la transaction
- Décision prise
- Score initial
- Raisons affichées

C'est le bonus "receipt / audit trail".

---

## Étape 6 — Livrables finaux

À soumettre :

1. **Code fonctionnel** (Python + Streamlit, lancement en une commande)
2. **`transactions_flagged.csv`** — version annotée du CSV original
3. **README.md** — quoi, comment, stratégie de détection, "if we had another week"
4. **PRD.md** — 1–2 pages : user, problème, succès, hors-scope
5. **IMPLEMENTATION.md** — 1 page : tech stack, architecture, division du travail
6. **Hypothesis log** (bonus) — `HYPOTHESES.md` documentant ce qu'on a essayé et gardé/jeté

---

## Division du travail (4 personnes, 23h)

| Personne | Rôle | Responsabilités |
|---|---|---|
| **P1 — Data** | Backend détection | Étapes 1 et 2 (profilage + 4 couches), tests unitaires sur le détecteur |
| **P2 — Backend** | Scoring + LLM | Étapes 3 et 4 (pondération, intégration Claude API, pré-génération explications) |
| **P3 — Frontend** | UI "Dossier" | Étape 5 (Streamlit, navigation clavier, undo, feedback loop) |
| **P4 — Produit** | Docs + audit + glue | Audit log, PRD, README, IMPLEMENTATION, hypothesis log, démo |

### Découpage temporel

| Heures | Objectif |
|---|---|
| H0–H2 | Setup repo, exploration du dataset par P1, scaffolding Streamlit par P3 |
| H2–H8 | P1 livre profilage + 4 couches ; P3 livre une UI minimale ; P2 prépare Claude API ; P4 démarre PRD |
| H8–H14 | Intégration : scoring pondéré, explications LLM branchées sur l'UI |
| H14–H18 | Calibration des seuils (viser F1 > 0.85), feedback loop, audit log |
| H18–H21 | Tests, polish UI, écriture README + IMPLEMENTATION |
| H21–H23 | Répétition de la démo, derniers ajustements, soumission |

---

## Ce qu'on ne fait PAS (hors-scope explicite)

- Pas de ML supervisé (random forest, XGBoost) — overkill pour 1000 lignes, et on n'a pas de labels
- Pas de détection temps réel — c'est un outil batch sur un CSV
- Pas de gestion multi-utilisateurs — un seul reviewer à la fois
- Pas de base de données — tout en mémoire / fichiers JSON

---

## Ce qui nous différencie

1. **Un détecteur multi-couches transparent** au lieu d'un score boîte noire
2. **Une UX d'enquête** au lieu d'un dashboard froid
3. **Des explications racontées** par Claude au lieu de "score 0.87"
4. **Un feedback loop intra-session** au lieu de seuils figés
5. **Un audit log défendable** au lieu d'une simple action utilisateur
