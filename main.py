"""Lance le pipeline de détection de fraude sur transactions.csv et affiche un résumé."""

import pandas as pd
from src.pipeline import run_pipeline_and_export

if __name__ == "__main__":
    try:
       flagged = run_pipeline_and_export(
    csv_path="data/transactions.csv",
    output_path="data/transactions_scored.csv",
    threshold=0.33,
)
    except FileNotFoundError:
        print("Erreur : fichier data/transactions.csv introuvable à la racine du projet")
        raise SystemExit(1)

    score_cols = ["s1", "s2", "s3", "s4"]
    layer_labels = {"s1": "s1 (montant)", "s2": "s2 (burst Poisson)", "s3": "s3 (siphon)", "s4": "s4 (cross-card)"}

    print(f"\n{'='*60}")
    print(f"Transactions flaggées : {len(flagged)}")

    df_scored = pd.read_csv("data/transactions_scored.csv")
    dominant = df_scored[["s1","s2","s3","s4"]].idxmax(axis=1)
    print("\nRépartition par couche dominante :")
    for col, label in layer_labels.items():
        count = (dominant == col).sum()
        print(f"  {label} : {count}")
    print(f"  Transactions avec s3 > 0 : {(df_scored['s3'] > 0).sum()}")
    print(f"  Transactions avec s4 > 0 : {(df_scored['s4'] > 0).sum()}")

    print("\nTop 10 transactions les plus suspectes :")
    display_cols = ["transaction_id", "card_id", "amount", "final_score"] + score_cols
    top10 = flagged.nlargest(10, "final_score")[display_cols]
    print(top10.to_string(index=False))

    print(f"\nRésultats exportés dans transactions_scored.csv")
    print('='*60)
