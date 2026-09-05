"""
agents/blue_agent.py
Blue Team strategy:
- Monopolizes life production and leverages the secret 50-unit global life reserve
- Price-gouges desperate teams (White/Red) demanding jewels and credits
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
        Blue calculates its own personal security needs and surplus to sell.
        """
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        blue_own_needed = my_state.surviving_members * days_left
        blue_deficit = max(0, blue_own_needed - my_state.resources.life)

        # Credits needed per life depends on tech level
        credit_per_life = my_state.tech.get_blue_credit_per_life()
        max_producible = int(my_state.resources.credits // credit_per_life)
        actual_producible = min(max_producible, global_state.life_reserve)

        # Blue wants to produce enough for its own survival plus 2-3 surplus for trading
        desired_production = min(actual_producible, blue_deficit + 3)

        return {"produce_life": desired_production}

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """
        Tech level 2 reduces credit cost to 1.5, Level 3 to 1.0!
        High priority for Blue if life reserve is still substantial (> 15).
        """
        if global_state.life_reserve > 15 and my_state.tech.can_upgrade(
            my_state.resources.credits
        ):
            # Reserve enough credits for at least 2 life production
            req = my_state.tech.upgrade_cost + 4
            return my_state.resources.credits >= req
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        Blue sells Life at premium prices:
        - To White: Sells 1-2 life for 20-30 jewels.
        - To Red: Sells 1 life for 10-15 credits (if not under embargo).
        """
        offers: List[TradeOffer] = []
        days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
        safe_margin = my_state.surviving_members * days_left
        surplus_life = max(0, my_state.resources.life - safe_margin)

        # If Blue has surplus or can afford to risk 1-2 life for massive jewels
        tradable_life = surplus_life
        if tradable_life == 0 and my_state.resources.life >= my_state.surviving_members * 3:
            tradable_life = 1

        if tradable_life >= 1:
            # High price offer to White
            offers.append(
                TradeOffer(
                    offer_id="",
                    sender="BLUE",
                    receiver="WHITE",
                    offering=ResourceBundle(life=1),
                    requesting=ResourceBundle(jewels=22.0),
                )
            )
            # Offer to Red for credits (to fund more life production) unless embargoed
            if not self.embargo_red and tradable_life >= 2:
                offers.append(
                    TradeOffer(
                        offer_id="",
                        sender="BLUE",
                        receiver="RED",
                        offering=ResourceBundle(life=1),
                        requesting=ResourceBundle(credits=10.0),
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
        Blue accepts offers that give high jewels or credits,
        only parting with life if price is sufficiently high.
        """
        if not my_state.resources.can_afford(offer.requesting):
            return False

        if offer.sender == "RED" and self.embargo_red:
            return False

        # If giving away life, verify compensation is lucrative
        if offer.requesting.life > 0:
            jewel_ratio = offer.offering.jewels / offer.requesting.life
            credit_ratio = offer.offering.credits / offer.requesting.life
            # Requires at least 18 jewels per life or 9 credits per life
            if jewel_ratio >= 18.0 or credit_ratio >= 9.0:
                # Ensure Blue doesn't starve itself
                days_left = global_state.config.TOTAL_DAYS - global_state.day + 1
                if my_state.resources.life - offer.requesting.life >= my_state.surviving_members * 2:
                    return True
            return False

        # Accepting incoming goods without giving life
        if offer.offering.life > 0:
            return True

        return False

    def decide_reclaim_search(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Blue participates in reclaim searches only when credits are abundant."""
        cost = global_state.config.RECLAIM_SEARCH_CREDIT_COST
        if my_state.resources.credits >= cost + 6:
            return random.random() < 0.4
        return False

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        """Blue does not have bomb capability; relies on life diplomacy."""
        return []

    def decide_black_purchases(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        catalog: List[BlackMarketItem],
    ) -> List[str]:
        """Blue purchases a shield if Red has bombed anyone or has high credits."""
        purchases: List[str] = []
        if not my_state.has_shield:
            red_state = global_state.teams.get("RED")
            if red_state and red_state.resources.credits >= 10:
                if my_state.resources.credits >= 8:
                    purchases.append(WeaponType.SHIELD.value)
                elif my_state.resources.jewels >= 25:
                    purchases.append(WeaponType.SHIELD.value)
        return purchases
