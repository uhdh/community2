"""
agents/black_agent.py
Black Agent strategy:
- Hidden arms dealer and mart operator
- Stokes inter-team conflict to maximize arms revenue
- Wiretaps communications and sells intelligence
- Protects assets from 3-piece Reclaim confiscation
- Requires 1 daily life for mart operation
"""

import random
from typing import List, Dict, Any, TYPE_CHECKING
from agents.policy import BasePolicy
from models.resources import ResourceBundle
from models.market import TradeOffer
from models.war import AttackAction, BlackMarketItem, WeaponType

if TYPE_CHECKING:
    from simulation.engine import GlobalState
    from models.team import TeamState


class BlackPolicy(BasePolicy):
    def __init__(self):
        super().__init__("BLACK")
        self.wiretap_logs: List[str] = []

    def decide_morning_production(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> Dict[str, Any]:
        """
        Black prepares the mart catalog and adjusts prices based on global tension.
        Tension rises if Red has bombs/credits or teams are in life crisis.
        """
        red_state = global_state.teams.get("RED")
        red_threat = red_state and red_state.resources.credits >= 10
        disaster_risk = global_state.pollution_index >= 35.0

        price_multiplier = 1.0
        if red_threat or disaster_risk:
            # Wartime / crisis inflation on defense items
            price_multiplier = 1.35

        return {
            "price_multiplier": price_multiplier,
            "wiretap_active": True,
        }

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Black upgrades tech to increase arms profit margins if credits allow."""
        if my_state.resources.credits >= 15 and my_state.tech.can_upgrade(my_state.resources.credits):
            return True
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        Black trades accumulated jewels/credits to acquire 1 Life for mart maintenance
        if Black has 0 life.
        """
        offers: List[TradeOffer] = []
        if my_state.resources.life < 1:
            # Black needs 1 life for daily mart operation cost
            if my_state.resources.credits >= 10:
                offers.append(
                    TradeOffer(
                        offer_id="",
                        sender="BLACK",
                        receiver="BLUE",
                        offering=ResourceBundle(credits=10.0),
                        requesting=ResourceBundle(life=1),
                    )
                )
            elif my_state.resources.jewels >= 25:
                offers.append(
                    TradeOffer(
                        offer_id="",
                        sender="BLACK",
                        receiver="BLUE",
                        offering=ResourceBundle(jewels=25.0),
                        requesting=ResourceBundle(life=1),
                    )
                )
        return offers

    def evaluate_trade_offer(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        offer: "TradeOffer",
    ) -> bool:
        """Black accepts trades that yield Life for mart operation or highly profitable jewels."""
        if not my_state.resources.can_afford(offer.requesting):
            return False

        # Black always accepts Life if at 0 life
        if offer.offering.life > 0 and my_state.resources.life == 0:
            return True

        # Black accepts offers where incoming value exceeds outgoing by 30%+
        val_in = offer.offering.jewels * 1.0 + offer.offering.credits * 2.0
        val_out = offer.requesting.jewels * 1.0 + offer.requesting.credits * 2.0
        return val_in > val_out * 1.3

    def decide_reclaim_search(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Black does not search for reclaim pieces (they confiscate Black's own assets)."""
        return False

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        """Black operates as dealer, not direct combatant."""
        return []

    def decide_black_purchases(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        catalog: List[BlackMarketItem],
    ) -> List[str]:
        return []
