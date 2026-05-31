# Explication technique complète — Fraud Hunter

---

## Section 1 — Le profilage

Avant de chercher des anomalies, le système construit une référence pour chaque carte à partir de l'ensemble du fichier CSV. Voici ce que chaque valeur représente et pourquoi elle existe.

**Montant médian** : la valeur centrale de toutes les transactions de cette carte, telle que la moitié sont en dessous et l'autre moitié au-dessus. On utilise la médiane et non la moyenne parce qu'une seule grosse dépense exceptionnelle (voyage, achat électronique) ferait monter la moyenne et rendrait la référence inutilisable. La médiane est stable face à ces valeurs extrêmes. Elle est consommée par la couche 1 pour calculer l'écart de montant.

**IQR (écart interquartile)** : la différence entre le 75e et le 25e percentile des montants de la carte. Il mesure la variabilité habituelle sans être influencé par les valeurs extrêmes. Une carte avec un IQR de 5$ dépense très régulièrement ; une carte avec un IQR de 200$ a des habitudes très variables. L'IQR est consommé par la couche 1 comme échelle du z-score.

**Montant moyen et montant maximum** : calculés dans le profil mais non consommés par aucune couche de détection. Ils existent pour un usage futur potentiel ou un affichage dans l'UI.

**Pays habituel** : le pays du marchand le plus fréquent pour cette carte. Il est enregistré dans le profil mais n'est pas consommé directement dans le scoring — il est utilisé par le contrôleur comme contexte géographique transmis à Gemini pour enrichir les verdicts.

**Top 3 catégories, canaux, devices connus, IPs connues** : enregistrés dans le profil mais non consommés par les couches de détection actuelles. Les champs `device_is_new` et `ip_is_new` sont calculés directement par requête sur le CSV complet dans le contrôleur, pas depuis ces listes. Ces champs existent pour des usages futurs ou un affichage dans l'UI.

---

## Section 2 — Couche 1 : le z-score robuste

**Pourquoi la médiane et non la moyenne** : si une carte a fait un achat exceptionnel de 2 000$ une seule fois en six mois, la moyenne de ses transactions monte à 180$ là où la médiane reste à 25$. Utiliser la moyenne ferait croire que des achats de 300$ sont normaux pour cette carte alors qu'ils ne le sont pas.

**Pourquoi l'IQR et non l'écart-type** : l'écart-type est sensible aux valeurs extrêmes — exactement les transactions que l'on cherche à détecter. Si une fraude a déjà eu lieu sur la carte et n'a pas été signalée, son montant gonflerait l'écart-type et rendrait la carte moins sensible à des fraudes futures. L'IQR ignore les extrêmes par construction.

**Le facteur 0.7413** : pour une distribution normale, l'IQR vaut exactement 1.3490 fois l'écart-type (parce que l'IQR couvre du 25e au 75e percentile, soit ±0.6745 écarts-types). En multipliant l'IQR par 0.7413 (qui est 1 / 1.3490), on obtient une estimation de l'écart-type de la distribution. Cela permet au z-score de la couche 1 d'avoir la même interprétation qu'un z-score classique : une valeur de 2 signifie que le montant est à 2 écarts-types de la médiane.

**Pourquoi diviser par 6** : un z-score de 6 est statistiquement quasi impossible pour une distribution normale (probabilité inférieure à un milliardième). En divisant le z-score par 6, on mappe l'intervalle [0, 6σ] sur [0, 1]. Un montant à plus de 6σ de la médiane donne un score saturé à 1.0. Un montant à 3σ donne 0.5 — suspects mais pas certains.

**Le fallback `médiane × 0.1`** : il s'active quand l'IQR est nul (toutes les transactions de la carte ont exactement le même montant) ou quand la carte n'a qu'une seule transaction historique. Dans ce cas il est impossible de calculer une dispersion. Le fallback utilise 10% de la médiane comme échelle de substitution — c'est une valeur arbitrairement petite qui rend le score sensible sans être absurde. Si la médiane est aussi nulle, le fallback final est 1.0 pour éviter une division par zéro.

**Exemple chiffré** : médiane = 30$, IQR = 20$, montant de la transaction = 300$.
- Échelle : 20 × 0.7413 = 14.83$
- Z-score : (300 − 30) / 14.83 = 270 / 14.83 = 18.2
- Score : 18.2 / 6 = 3.03 → plafonné à 1.0

La transaction est à 18σ de la médiane de la carte — score maximum.

---

## Section 3 — Couche 2 : la loi de Poisson

**λ pour le burst marchand** : on calcule d'abord le taux historique du marchand en divisant le nombre total de ses transactions dans le dataset par la durée totale du dataset en heures. Si le dataset couvre 720 heures et que QuickPay a traité 72 transactions, son taux est 0.1 transaction par heure. Pour la fenêtre d'observation de 2 heures, l'espérance est λ = 0.1 × 2 = 0.2. Le facteur 2.0 correspond exactement à la durée de la fenêtre en heures.

**λ pour le burst carte** : même logique, mais la fenêtre est de 30 minutes (0.5 heure). Si une carte effectue en moyenne 0.04 transaction par heure, l'espérance pour une fenêtre de 30 minutes est λ = 0.04 × 0.5 = 0.02. Le facteur 0.5 correspond exactement à la durée de la fenêtre en heures.

**Pourquoi 2.0 pour le marchand et 0.5 pour la carte** : ce sont simplement les durées des fenêtres d'observation exprimées en heures. Le marchand est surveillé sur 2 heures (7 200 secondes) parce qu'un terminal compromis produit des fraudes étalées sur une session de caisse. La carte est surveillée sur 30 minutes (1 800 secondes) parce que le card testing est une opération rapide — le fraudeur veut valider la carte avant qu'elle soit bloquée.

**Ce que `1 − CDF(k−1, λ)` calcule** : CDF(k−1, λ) est la probabilité d'observer strictement moins de k événements quand on attend λ. En soustrayant de 1, on obtient la probabilité d'observer k ou plus — c'est la p-valeur : quelle est la chance que ce niveau d'activité arrive par hasard ? Si p = 0.001, il y a une chance sur mille que ce soit normal.

**Pourquoi `−log10(p) / 8`** : prendre le logarithme négatif transforme une petite probabilité en un grand nombre. Si p = 0.01 (1 chance sur 100), −log10(0.01) = 2. Si p = 0.000001, −log10 = 6. En divisant par 8, on mappe cette échelle sur [0, 1] : le score atteint 1.0 quand p ≤ 10⁻⁸, c'est-à-dire une chance sur cent millions. En dessous de cette probabilité, le score est saturé.

**Pourquoi le plancher λ = 0.01** : si un marchand n'a eu qu'une seule transaction dans tout le dataset, son taux calculé est quasi nul. Diviser par un λ nul ou quasi nul rendrait tous les volumes anomaux chez ce marchand. Le plancher à 0.01 signifie qu'on suppose qu'il y a toujours au minimum une chance sur cent par heure d'une transaction — une hypothèse raisonnable même pour un petit commerce.

**Exemple chiffré** : un marchand reçoit normalement 2 transactions par heure et en voit 8 en 2 heures.
- λ_marchand = 2.0 × 2.0 = 4.0 (attendu dans la fenêtre de 2h)
- k = 8 (observé)
- P(X ≥ 8 | λ=4) = 1 − CDF(7, 4) ≈ 1 − 0.9489 = 0.0511 (5.1% de chance)
- Score = −log10(0.0511) / 8 = 1.29 / 8 = 0.16

Un score de 0.16 est modéré — 4× la normale en 2h est suspect mais pas exceptionnel. Si le même marchand recevait 15 transactions en 2h (7.5× la normale), p tomberait sous 0.0001 et le score dépasserait 0.5.

---

## Section 4 — Couche 3 : le siphonnement

**Pourquoi 10 minutes** : les tests de carte sont des opérations rapides. Le fraudeur veut valider la carte et déclencher l'exploitation avant que le détenteur légitime ou la banque ne remarque. Une fenêtre de 5 minutes manquerait des séquences légèrement étalées ; une fenêtre de 30 minutes produirait trop de faux positifs (deux cafés dans la même matinée).

**Pourquoi le seuil est à 3 et non 2** : deux transactions rapides sur une même carte sont fréquentes (stationnement + café, two taps dans le même magasin). Trois transactions en moins de 10 minutes sur la même carte est un comportement rare pour un usage légitime et caractéristique du card testing.

**Pourquoi 0.4 pour ≥3** : trois transactions rapides sont suspectes mais pas certaines. Un score de 0.4 est en dessous du threshold de flagging seul (0.28 n'est atteint que combiné avec d'autres couches), ce qui évite les faux positifs sur ce seul signal.

**Pourquoi +0.3 pour ≥5** : cinq transactions en 10 minutes sur la même carte sont quasi impossibles dans un usage normal. Le score total atteint 0.7 (0.4+0.3), bien au-dessus du threshold, suffisant pour déclencher un flag même si les autres couches ne voient rien.

**Pourquoi +0.3 pour gift_card et online_retail** : ces catégories sont les plus utilisées dans les fraudes de card testing parce qu'elles sont immédiatement convertibles en valeur (revente de cartes cadeaux, achat de biens numériques). Le bonus s'applique dès 3 transactions, pas seulement à 5.

**Pourquoi uniquement vers le passé** : regarder dans le futur pour scorer une transaction est une fuite de données — en production réelle, les transactions futures n'existent pas encore au moment du traitement. La fenêtre rétrospective seule garantit que le score est calculable en temps réel.

**Exemple chiffré** : 4 transactions gift_card à t=0, t=2, t=4, t=6 minutes sur la même carte.
- Transaction à t=0 : fenêtre [−10min, 0] → 1 transaction dans la fenêtre → score = 0.0
- Transaction à t=2 : fenêtre [−8min, 2] → 2 transactions → score = 0.0
- Transaction à t=4 : fenêtre [−6min, 4] → 3 transactions, catégorie gift_card → 0.4 + 0.3 = 0.7
- Transaction à t=6 : fenêtre [−4min, 6] → 4 transactions, catégorie gift_card → 0.4 + 0.3 = 0.7

Les deux premières transactions ne voient pas encore de contexte passé suffisant. Les deux dernières sont flaggées à 0.7.

---

## Section 5 — Couche 4 : le burst marchand cross-card

**Pourquoi le marchand et non le device ou l'IP** : le champ `device_id` n'est renseigné que pour les transactions en ligne, ce qui laisse un angle mort sur les fraudes physiques (terminal skimmé en caisse). L'IP a le même problème. Le marchand est présent pour toutes les transactions, ce qui permet de détecter aussi bien les terminaux physiques compromis que les sites de e-commerce piratés.

**Pourquoi 6 cartes → 0.9 et 4 cartes → 0.7** : ces seuils ont été calibrés sur les patterns observés dans le dataset. Les bursts QuickPay impliquaient 6 à 7 cartes en 70 minutes — le seuil de 6 capte exactement ce pattern avec un score quasi certain (0.9). Le seuil à 4 cartes capture les cas intermédiaires avec un score fort mais pas maximal. En dessous de 4, il est possible qu'un marchand populaire voie simplement beaucoup de clients différents à la même heure.

**Pourquoi une fenêtre de 2 heures** : une session de fraude avec plusieurs cartes se déroule typiquement en une à deux heures. Au-delà, le fraudeur s'expose à ce que les premières cartes soient bloquées avant de terminer. En dessous d'une heure, la fenêtre manquerait des sessions étalées dans le temps.

**Le bonus de ratio de montant** : si le score cross-card est déjà positif (au moins 4 cartes détectées), et que le montant de la transaction dépasse 3 fois la médiane de la carte, un bonus plafonné à 0.1 est ajouté. La formule est `min((ratio − 1) / 20, 0.1)` — un ratio de 4 ajoute 0.15 plafonné à 0.1, un ratio de 10 ajoute aussi 0.1. Ce bonus ne s'active qu'en renfort d'un signal cross-card déjà présent, jamais seul.

**Pourquoi les paramètres `device_profiles` et `ip_profiles` ont été retirés** : la conception initiale prévoyait de détecter la fraude via les identifiants partagés (un seul appareil utilisé avec plusieurs cartes). Cette approche a été abandonnée en cours de développement car le champ `device_id` est absent pour les transactions physiques, réduisant la couverture de moitié. L'implémentation a pivoté vers la détection par marchand. Les paramètres ont donc été retirés de la signature car ils n'étaient jamais lus dans le corps de la fonction.

---

## Section 6 — Le score composite

**Les poids actuels** : w1 (montant) = 0.20, w2 (Poisson) = 0.30, w3 (siphonnement) = 0.25, w4 (cross-card) = 0.25. Ils ne sont pas égaux parce que les quatre couches ne sont pas également discriminantes sur ce dataset. Le burst Poisson (w2) est le signal le plus fiable : quand une p-value dépasse le seuil de signification statistique, il est très rare que ce soit du bruit. Le montant (w1) reçoit le poids le plus faible parce qu'une dépense élevée peut être parfaitement légitime — voyage, achat exceptionnel — et génère des faux positifs si sur-pondérée. Les couches 3 et 4 reçoivent 0.25 chacune parce qu'elles sont fiables mais spécifiques à des patterns précis qui ne s'appliquent pas à toutes les fraudes.

**Ce que représente un score de 0.28** : une transaction qui accumule environ 28% d'un score maximal toutes couches confondues. Concrètement, une transaction avec un léger écart de montant (s1=0.3), un rythme un peu inhabituel (s2=0.2), et deux transactions rapides mais pas suffisantes pour s3, atteindrait déjà 0.28 par accumulation.

**Pourquoi le threshold est à 0.28** : calibré empiriquement sur l'effet observé. À 0.28, le système flag 69 transactions sur 1 000, soit 6.9% — cohérent avec les taux de fraude typiques dans le brief (environ 7%). À 0.40, il n'en reste que 46 — probablement des faux négatifs. À 0.20, on en flagge 112 — trop de faux positifs pour un analyste.

**Le feedback loop** : quand un analyste marque une transaction comme légitime, le `FeedbackManager` ajoute −0.05 aux scores futurs de la même catégorie de marchand. Quand il confirme une fraude sur un device identifié, il ajoute +0.10 aux scores des transactions du même device. Ces modificateurs sont appliqués après le calcul du score de base lors d'une prochaine session avec le même gestionnaire actif. La limite est que ces modifications ne persistent pas entre sessions sans export/import manuel.

**Exemple chiffré** : s1=0.8, s2=1.0, s3=0.7, s4=0.0.
- Score = 0.20×0.8 + 0.30×1.0 + 0.25×0.7 + 0.25×0.0
- Score = 0.16 + 0.30 + 0.175 + 0.0 = 0.635
- S1 ≥ 0.8 → vérification du boost : si la catégorie est gift_card ou electronics, +0.05 → 0.685 (sinon reste à 0.635)
- Dans les deux cas, score ≥ 0.28 → transaction flaggée, niveau de risque ÉLEVÉ (≥ 0.60)

---

## Section 7 — Le pipeline complet

**Étape 1 — Lecture du CSV** : `pd.read_csv` charge les 1 000 lignes avec la colonne timestamp parsée en objet datetime. Résultat : un DataFrame de 1 000 lignes avec toutes les colonnes du dataset d'origine.

**Étape 2 — Profilage** : `build_card_profiles` parcourt le DataFrame et calcule pour chaque carte unique sa médiane, son IQR, son pays habituel, etc. Résultat : un dictionnaire indexé par `card_id`, consommé uniquement par l'étape suivante.

**Étape 3 — Score s1** : `score_amount_deviation` lit la médiane et l'IQR de chaque carte depuis le profil, calcule le z-score robuste de chaque montant, et produit une colonne s1 dans le DataFrame. Résultat : 1 000 valeurs entre 0 et 1.

**Étape 4 — Score s2** : `score_burst_poisson` calcule les taux historiques par marchand et par carte, puis pour chaque transaction compte les transactions dans la fenêtre glissante (7 200s pour le marchand, 1 800s pour la carte), calcule la p-value Poisson et la normalise. Produit la colonne s2.

**Étape 5 — Score s3** : `score_burst` compte pour chaque transaction le nombre de transactions de la même carte dans les 10 minutes qui précèdent strictement, applique les seuils de score par paliers, et produit la colonne s3.

**Étape 6 — Score s4** : `score_cross_card` compte pour chaque transaction le nombre de cartes distinctes ayant utilisé le même marchand dans une fenêtre de ±2 heures, applique les seuils à 4 et 6 cartes, et produit la colonne s4.

**Étape 7 — Score final et flagging** : `process_scoring_pipeline` calcule `final_score = 0.20×s1 + 0.30×s2 + 0.25×s3 + 0.25×s4`, applique le boost de +0.05 pour les transactions à s1 ≥ 0.8 dans les catégories gift_card ou electronics, applique les modificateurs du feedback loop si présents, puis marque comme flaggée toute transaction avec final_score ≥ 0.28. Retourne uniquement les lignes flaggées, triées par score décroissant.

**Étape 8 — Export CSV** : dans `run_pipeline_and_export` uniquement (pas dans le flux UI), après le scoring, le `final_score` et `is_flagged` sont recalculés directement sur le DataFrame complet (1 000 lignes) et écrits dans `transactions_scored.csv`. Cet export contient toutes les transactions avec leurs six colonnes ajoutées : s1, s2, s3, s4, final_score, is_flagged. La colonne `is_flagged` est un booléen calculé par `final_score >= 0.28`.

---

## Section 8 — Les limites et leurs raisons

**Pourquoi s4 produit des scores faibles sur ce dataset** : la couche 4 nécessite 4 à 6 cartes distinctes chez le même marchand dans une fenêtre de 2 heures. Sur 1 000 transactions réparties sur 50 cartes et 30 jours, la densité de transactions par marchand par heure est très faible — seuls les marchands les plus fréquentés (comme QuickPay lors des bursts) atteignent les seuils. Sur un vrai dataset de production avec des millions de transactions, s4 serait beaucoup plus actif.

**Pourquoi s3 n'apparaît jamais comme couche dominante** : le contrôleur sélectionne la couche avec le score le plus élevé parmi celles qui dépassent 0.3 pour identifier le signal dominant. Les transactions détectées par s3 (card testing) déclenchent presque toujours aussi s2 (Poisson) avec un score plus élevé — une rafale sur une carte est à la fois un burst carte (s2) et un siphonnement (s3). S2 l'emporte systématiquement parce que son score est proportionnel à la rareté statistique tandis que s3 est plafonné à 0.7 sur des sequences de 4+ transactions.

**Pourquoi les poids sont calibrés manuellement** : sans données étiquetées (colonne indiquant "cette transaction est une vraie fraude"), il est impossible de calculer un F1 score et donc d'optimiser les poids par gradient ou grid search. Les poids reflètent une intuition sur la fiabilité relative de chaque signal, validée par l'observation que les patterns attendus sont bien détectés. Une optimisation mathématique nécessiterait un historique d'alertes confirmées.

**Pourquoi le feedback loop ne persiste pas entre sessions** : le `FeedbackManager` vit en mémoire Python dans l'état de session Streamlit. À chaque redémarrage du serveur ou changement d'onglet, il est réinitialisé. Les décisions prises dans le deck JavaScript (swipe) restent côté navigateur et ne sont pas transmises automatiquement à Python — il n'existe pas de pont bidirectionnel entre l'iframe et Streamlit sans composant custom. L'export JSON + réimport manuel est le mécanisme de persistance intentionnellement choisi pour sa robustesse, au prix de ne pas être automatique.
