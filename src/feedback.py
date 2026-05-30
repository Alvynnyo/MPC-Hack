# src/feedback.py
from __future__ import annotations

class FeedbackManager:
    """
    Gère la boucle de rétroaction (Feedback Loop) de la session en cours.
    Conserve en mémoire les ajustements de score basés sur les décisions du réviseur.
    """
    def __init__(self):
        self.category_modifiers = {}
        self.device_modifiers = {}

    def record_decision(self, transaction_data: dict, decision: str) -> None:
        """
        Appelé par l'interface UI à chaque clic du réviseur.
        """
        cat = transaction_data.get('merchant_category')
        dev = transaction_data.get('device_id')

        if decision == 'Innocenter' and cat:
            self.category_modifiers[cat] = self.category_modifiers.get(cat, 0.0) - 0.05
            
        elif decision == 'Classer' and dev:
            self.device_modifiers[dev] = self.device_modifiers.get(dev, 0.0) + 0.10