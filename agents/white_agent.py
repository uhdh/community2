"""
agents/white_agent.py
White Team strategy:
- Controls jewel issuance and liquidity
- Manages food supply via bulk purchases from Blue
- Procures weapons from Black Mart with abundant jewels if defensive deterrence is required
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


class WhitePolicy(BasePolicy):
    def __init__(self):
        super().__init__("WHITE")

    def decide_morning_production(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> Dict[str, Any]:
        """
        White mints jewels balancing life purchase needs against currency dilution.
        """
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        needed_life = my_state.surviving_members * days_left
        current_life = my_state.resources.life
        life_deficit = max(0, needed_life - current_life)

        if life_deficit > 10:
            mint_amount = random.randint(30, 50)
        elif life_deficit > 4:
            mint_amount = random.randint(15, 30)
        else:
            mint_amount = random.randint(5, 12)

        return {"mint_jewels": mint_amount}

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Upgrades tech if credits are abundant (> 12)."""
        if my_state.resources.life >= my_state.surviving_members * 2:
            return my_state.tech.can_upgrade(my_state.resources.credits)
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        White creates trade offers to acquire Life from Blue and Credits from Red.
        """
        offers: List[TradeOffer] = []
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        needed_life = my_state.surviving_members * days_left
        life_deficit = max(0, needed_life - my_state.resources.life)

        # 1. Offer to Blue: Jewels for Life
        if life_deficit > 0 and my_state.resources.jewels >= 25:
            jewels_to_offer = 25.0 if life_deficit > 6 else 18.0
            life_to_request = min(3, life_deficit)
            if life_to_request > 0:
                offers.append(
                    TradeOffer(
                        offer_id="",
                        sender="WHITE",
                        receiver="BLUE",
                        offering=ResourceBundle(jewels=jewels_to_offer),
                        requesting=ResourceBundle(life=life_to_request),
                    )
                )

        # 2. Offer to Red: Jewels for Credits
        if my_state.resources.credits < 10 and my_state.resources.jewels >= 20:
            offers.append(
                TradeOffer(
                    offer_id="",
                    sender="WHITE",
                    receiver="RED",
                    offering=ResourceBundle(jewels=20.0),
                    requesting=ResourceBundle(credits=8.0),
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

        if offer.requesting.life > 0:
            if my_state.resources.life <= my_state.surviving_members * 2:
                return False

        if offer.offering.life > 0:
            return True

        if offer.offering.credits >= 6 and offer.requesting.jewels <= 15:
            return True

        return False

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        """White is generally defensive, but may purchase weapons to retaliate if attacked."""
        actions: List[AttackAction] = []
        if global_state.war_attacks_count > 0 and my_state.resources.jewels >= 40 and random.random() < 0.25:
            actions.append(
                AttackAction(
                    attacker="WHITE",
                    target="RED",
                    weapon_type=WeaponType.WEAPON_TIER_B,
                    jewels_spent=20.0,
                    description="White retaliates with Tier B weapon from Black Mart!",
                )
            )
        return actions

    def decide_black_purchases(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        catalog: List[BlackMarketItem],
    ) -> List[str]:
        return []
