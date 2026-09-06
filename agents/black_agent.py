"""
agents/black_agent.py
Black Agent strategy:
- Operates the Shadow Mart selling War Declaration and Weapons (A/B/C) for jewels
- Stokes inter-team conflict to maximize arms revenue
- Exempt from mart life cost on Day 1; consumes 1 life daily starting Day 2
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

    def decide_morning_production(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> Dict[str, Any]:
        return {}

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        if my_state.resources.credits >= 15 and my_state.tech.can_upgrade(my_state.resources.credits):
            return True
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        Black trades accumulated jewels/credits to acquire 1 Life for mart maintenance
        if Black has 0 life (especially from Day 2 onwards).
        """
        offers: List[TradeOffer] = []
        if global_state.day >= 2 and my_state.resources.life < 1:
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
        if not my_state.resources.can_afford(offer.requesting):
            return False

        if offer.offering.life > 0 and my_state.resources.life == 0:
            return True

        val_in = offer.offering.jewels * 1.0 + offer.offering.credits * 2.0
        val_out = offer.requesting.jewels * 1.0 + offer.requesting.credits * 2.0
        return val_in > val_out * 1.3

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        return []

    def decide_black_purchases(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        catalog: List[BlackMarketItem],
    ) -> List[str]:
        return []
