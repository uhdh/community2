"""
agents/white_agent.py
White Team strategy:
- Maintains market dominance via controlled jewel issuance
- Utilizes majority voting power and alliance defense
- Prioritizes life acquisition to sustain its 6-member populace
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
        White decides how many jewels to mint.
        Balances survival need (minting to buy life) against inflation (diluting prize per jewel).
        """
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        needed_life = my_state.surviving_members * days_left
        current_life = my_state.resources.life
        life_deficit = max(0, needed_life - current_life)

        # Base minting logic
        if life_deficit > 10:
            # High urgency: mint more jewels to aggressively trade for life
            mint_amount = random.randint(30, 50)
        elif life_deficit > 4:
            # Moderate urgency
            mint_amount = random.randint(15, 30)
        else:
            # Sufficient life: minimize inflation to preserve jewel unit value
            mint_amount = random.randint(5, 12)

        return {"mint_jewels": mint_amount}

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Upgrades tech if credits are abundant (> 12) and life is not in immediate danger."""
        if my_state.resources.life >= my_state.surviving_members * 2:
            return my_state.tech.can_upgrade(my_state.resources.credits)
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        White creates trade offers:
        - Buys Life from Blue using newly minted Jewels.
        - Buys Credits from Red using Jewels to fund shields/reclaim searches.
        """
        offers: List[TradeOffer] = []
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        needed_life = my_state.surviving_members * days_left
        life_deficit = max(0, needed_life - my_state.resources.life)

        # 1. Offer to Blue: Jewels for Life
        if life_deficit > 0 and my_state.resources.jewels >= 25:
            # White pays premium for life when in crisis
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
        """
        White evaluates incoming offers:
        - Always eager to accept Life in exchange for Jewels/Credits.
        - Reluctant to give away Life.
        """
        if not my_state.resources.can_afford(offer.requesting):
            return False

        # Never give away life if running short
        if offer.requesting.life > 0:
            if my_state.resources.life <= my_state.surviving_members * 2:
                return False

        # If incoming offer grants Life, highly favored
        if offer.offering.life > 0:
            return True

        # If gaining credits for reasonable jewels
        if offer.offering.credits >= 6 and offer.requesting.jewels <= 15:
            return True

        return False

    def decide_reclaim_search(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """White uses excess credits to find Reclaim Pieces against Black."""
        cost = global_state.config.RECLAIM_SEARCH_CREDIT_COST
        # Only search if basic life needs are reasonably met and credits available
        if (
            my_state.resources.credits >= cost + 4
            and my_state.resources.life >= my_state.surviving_members
        ):
            return random.random() < 0.6
        return False

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        """White is primarily defensive and does not initiate unprovoked bomb strikes."""
        return []

    def decide_black_purchases(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        catalog: List[BlackMarketItem],
    ) -> List[str]:
        """
        White buys a Shield if not currently protected and Red has bomb capability (credits >= 10).
        """
        purchases: List[str] = []
        if not my_state.has_shield:
            red_state = global_state.teams.get("RED")
            red_threat = red_state and red_state.resources.credits >= 10
            if red_threat and my_state.resources.credits >= 8:
                purchases.append(WeaponType.SHIELD.value)
            elif red_threat and my_state.resources.jewels >= 30:
                purchases.append(WeaponType.SHIELD.value)
        return purchases
