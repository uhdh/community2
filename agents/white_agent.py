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
            # Check price per life (The Invisible Hand tolerance)
            # If Blue demands exorbitant price (> 35.0 jewels/life), reject offer due to price discontent!
            price_per_life = offer.requesting.jewels / max(1, offer.offering.life)
            if price_per_life > 35.0:
                self.price_discontent = True
                return False
            return True

        if offer.offering.credits >= 6 and offer.requesting.jewels <= 22:
            if my_state.resources.jewels >= 30:
                return True

        return False

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        """White declares war on Blue if price gouging is detected, or retaliates defensively."""
        actions: List[AttackAction] = []

        # Economic War Trigger: If Blue demanded an exorbitant price for Life (price discontent)
        # Declaring war (15 jewels) and looting 50% of Blue's resources is cheaper than paying extortionate prices!
        if getattr(self, "price_discontent", False) and my_state.resources.jewels >= 35.0:
            blue_team = global_state.teams.get("BLUE")
            if blue_team and blue_team.resources.life >= 3:
                self.price_discontent = False
                return [
                    AttackAction(
                        attacker="WHITE",
                        target="BLUE",
                        weapon_type=WeaponType.WAR_DECLARATION,
                        jewels_spent=15.0,
                        description="화이트가 블루의 라이프 독점 폭리(가격 불만)에 반발하여 공식 전쟁 선포! (15보석)",
                    ),
                    AttackAction(
                        attacker="WHITE",
                        target="BLUE",
                        weapon_type=WeaponType.WEAPON_TIER_B,
                        jewels_spent=20.0,
                        description="화이트가 B급 무기로 블루를 타격하여 전리품 50% 강탈!",
                    ),
                ]

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
