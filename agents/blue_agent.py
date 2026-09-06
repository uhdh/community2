"""
agents/blue_agent.py
Blue Team strategy:
- Monopolizes life production from the secret 50-unit global life reserve
- Price-gouges desperate teams demanding jewels and credits
- Secures its own 3 members' survival while controlling other teams' survival thresholds
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


class BluePolicy(BasePolicy):
    def __init__(self):
        super().__init__("BLUE")
        self.embargo_red: bool = False

    def decide_morning_production(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> Dict[str, Any]:
        """
        Blue produces Life from the secret Life Reserve using credits.
        """
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        blue_own_needed = my_state.surviving_members * days_left
        blue_deficit = max(0, blue_own_needed - my_state.resources.life)

        credit_per_life = my_state.tech.get_blue_credit_per_life()
        max_producible = int(my_state.resources.credits // credit_per_life)
        actual_producible = min(max_producible, global_state.life_reserve)

        desired_production = min(actual_producible, blue_deficit + 3)
        return {"produce_life": desired_production}

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        if global_state.life_reserve > 15 and my_state.tech.can_upgrade(
            my_state.resources.credits
        ):
            req = my_state.tech.upgrade_cost + 4
            return my_state.resources.credits >= req
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        Blue sells Life at premium prices.
        """
        offers: List[TradeOffer] = []
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        safe_margin = my_state.surviving_members * days_left
        surplus_life = max(0, my_state.resources.life - safe_margin)

        tradable_life = surplus_life
        if tradable_life == 0 and my_state.resources.life >= my_state.surviving_members * 3:
            tradable_life = 1

        if tradable_life >= 1:
            # Dynamic Market Pricing (The Invisible Hand):
            # Price scales with life reserve depletion and jewel inflation
            scarcity_ratio = max(0.0, (50 - global_state.life_reserve) / 50.0)
            inflation_ratio = (
                global_state.total_circulating_jewels / 200.0
                if global_state.total_circulating_jewels > 0
                else 1.0
            )
            # Baseline 22.0 jewels, rising up to 45+ jewels as scarcity worsens
            asking_jewels = round(22.0 * (1.0 + scarcity_ratio * 1.0) * max(1.0, inflation_ratio), 1)
            asking_credits = round(10.0 * (1.0 + scarcity_ratio * 0.8), 1)

            # High price offer to White
            offers.append(
                TradeOffer(
                    offer_id="",
                    sender="BLUE",
                    receiver="WHITE",
                    offering=ResourceBundle(life=1),
                    requesting=ResourceBundle(jewels=asking_jewels),
                )
            )
            if not self.embargo_red and tradable_life >= 2:
                offers.append(
                    TradeOffer(
                        offer_id="",
                        sender="BLUE",
                        receiver="RED",
                        offering=ResourceBundle(life=1),
                        requesting=ResourceBundle(credits=asking_credits),
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

        if offer.sender == "RED" and self.embargo_red:
            return False

        if offer.requesting.life > 0:
            jewel_ratio = offer.offering.jewels / offer.requesting.life
            credit_ratio = offer.offering.credits / offer.requesting.life
            if jewel_ratio >= 18.0 or credit_ratio >= 9.0:
                if my_state.resources.life - offer.requesting.life >= my_state.surviving_members * 2:
                    return True
            return False

        if offer.offering.life > 0:
            return True

        return False

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
