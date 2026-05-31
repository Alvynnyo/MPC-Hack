"""Lance le pipeline de détection de fraude sur transactions.csv et affiche un résumé."""
import pandas as pd
from src.pipeline import run_pipeline_and_export

if __name__ == "__main__":
    try:
        flagged = run_pipeline_and_export(
            csv_path="data/transactions.csv",
            output_path="data/transactions_scored.csv",
        )
    except FileNotFoundError:
        print("Erreur : fichier data/transactions.csv introuvable à la racine du projet")
        raise SystemExit(1)

    # Médiane par carte pour les explications
    df_full = pd.read_csv("data/transactions.csv")
    card_median = df_full.groupby('card_id')['amount'].median().to_dict()

    def explain(row) -> str:
        motifs = []
        if row['s1'] >= 0.8:
            median = card_median.get(row['card_id'], row['amount'])
            ratio = row['amount'] / median if median > 0 else 1
            motifs.append(f"montant {ratio:.0f}x la médiane ({median:.0f}$)")
        if row['s2'] >= 0.5:
            motifs.append("burst Poisson")
        if row['s3'] >= 0.4:
            motifs.append("card testing (micro-tx <10min)")
        if row['s4'] >= 0.7:
            motifs.append("terminal compromis (multi-cartes)")
        if row['merchant_category'] in ['gift_card', 'electronics'] and row['s1'] >= 0.8:
            motifs.append(f"catégorie à risque ({row['merchant_category']})")
        return " | ".join(motifs) if motifs else "score agrégé élevé"

    flagged = flagged.copy()
    flagged['motif'] = flagged.apply(explain, axis=1)

    score_cols = ["s1", "s2", "s3", "s4"]
    layer_labels = {0: "s1 (montant)", 1: "s2 (burst Poisson)", 2: "s3 (siphon)", 3: "s4 (cross-card)"}

    print(f"\n{'='*60}")
    print(f"Transactions flaggées : {len(flagged)}")

    dominant = flagged[score_cols].values.argmax(axis=1)
    print("\nRépartition par couche dominante :")
    for idx, label in layer_labels.items():
        count = (dominant == idx).sum()
        print(f"  {label} : {count}")

    print(f"\n{'transaction_id':<15} {'card_id':<12} {'amount':>8}  {'score':>6}  motif")
    print(f"{'-'*100}")
    for _, row in flagged.iterrows():
        print(f"{row['transaction_id']:<15} {row['card_id']:<12} {row['amount']:>8.2f}$  {row['final_score']:>6.3f}  {row['motif']}")
    print('='*60)