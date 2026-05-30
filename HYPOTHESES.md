# Journal des hypothèses

> À mettre à jour au fur et à mesure des expérimentations.
>
> Format : Hypothèse → ce qu'on a essayé → résultat (F1 si applicable) → garde / jette / à creuser.

## Template

```
### H## — Titre de l'hypothèse

**Idée :**

**Implémentation :**

**Résultat :**

**Décision :** ☐ Gardé  ☐ Jeté  ☐ À creuser

**Notes :**
```

---

## H01 — Seuil N pour l'écart de montant (couche 1)

**Idée :** une transaction est anormale si son montant > N × médiane de la carte.

**Implémentation :** À tester avec N = 5, 10, 15.

**Résultat :** TBD

**Décision :** TBD

---

## H02 — Fenêtre de temps pour la vitesse impossible (couche 2)

**Idée :** deux transactions in-person dans des pays différents en moins de X heures = fraude.

**Implémentation :** Tester X = 2h, 4h, 6h.

**Résultat :** TBD

**Décision :** TBD

---

## H03 — Seuil de cartes par device pour la fraude croisée (couche 4)

**Idée :** un device utilisé par > K cartes distinctes = fraude probable.

**Implémentation :** Tester K = 2, 3, 5.

**Résultat :** TBD

**Décision :** TBD
