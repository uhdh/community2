"""
agents/red_agent.py
Red Team strategy:
- Produces heavy credit volumes via clean or polluting production
- Conducts trade negotiations to secure vital Life
- Procures weapons from Black Mart with surplus jewels when strategic deterrence is required
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


class RedPolicy(BasePolicy):
    def __init__(self):
        super().__init__("RED")
        self.attack_history_count: int = 0

    def decide_morning_production(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> Dict[str, Any]:
        """
        Red decides between clean credit production and polluting credit production.
        If pollution is safely under threshold, it may use polluting production.
        """
        current_pollution = global_state.pollution_index
        threshold = global_state.config.POLLUTION_DISASTER_THRESHOLD
        days_of_life = my_state.resources.life / max(1, my_state.surviving_members)

        if current_pollution + global_state.config.RED_POLLUTION_INCREMENT > threshold:
            if days_of_life <= 1.0 and my_state.resources.credits < 10:
                # Desperation: risk disaster
                use_pollution = True
            else:
                use_pollution = False
        else:
            use_pollution = True

        return {"use_polluting_production": use_pollution}

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Upgrades tech if credits >= upgrade_cost + 6."""
        if my_state.tech.can_upgrade(my_state.resources.credits):
            return my_state.resources.credits >= my_state.tech.upgrade_cost + 6
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        Red urgently trades for Life using credits and jewels.
        """
        offers: List[TradeOffer] = []
        days_of_life = my_state.resources.life / max(1, my_state.surviving_members)

        # High priority offer to Blue for life using credits
        if days_of_life <= 3.0 and my_state.resources.credits >= 10:
            offers.append(
                TradeOffer(
                    offer_id="",
                    sender="RED",
                    receiver="BLUE",
                    offering=ResourceBundle(credits=10.0),
                    requesting=ResourceBundle(life=1),
                )
            )

        # Offer jewels for life if life is critically low
        if days_of_life <= 2.0 and my_state.resources.jewels >= 25:
            offers.append(
                TradeOffer(
                    offer_id="",
                    sender="RED",
                    receiver="BLUE",
                    offering=ResourceBundle(jewels=25.0),
                    requesting=ResourceBundle(life=1),
                )
            )

        # Offer surplus credits to White in exchange for jewels (arms funding & prize pool conversion)
        if my_state.resources.credits >= 16.0 and my_state.resources.jewels < 40.0:
            offers.append(
                TradeOffer(
                    offer_id="",
                    sender="RED",
                    receiver="WHITE",
                    offering=ResourceBundle(credits=10.0),
                    requesting=ResourceBundle(jewels=20.0),
                )
            )

        return offers

    def evaluate_trade_offer(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        offer: "TradeOffer",
    ) -> bool:
        """Red accepts any trade providing Life, and trades credits for jewels."""
        if not my_state.resources.can_afford(offer.requesting):
            return False

        # If incoming offer gives life, evaluate price tolerance
        if offer.offering.life > 0:
            credit_per_life = offer.requesting.credits / max(1, offer.offering.life)
            jewel_per_life = offer.requesting.jewels / max(1, offer.offering.life)
            if credit_per_life > 16.0 or jewel_per_life > 35.0:
                self.price_discontent = True
                return False
            return True

        # If trading surplus credits for jewels
        if offer.offering.jewels >= 18 and offer.requesting.credits <= 10:
            if my_state.resources.credits >= 15:
                return True

        return False

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        """
        Red procures weapons or declares war via Black Mart if in crisis or prices are unacceptable.
        """
        actions: List[AttackAction] = []
        days_of_life = my_state.resources.life / max(1, my_state.surviving_members)

        # Economic War Trigger: If Blue demanded an exorbitant price for Life, Red declares war (15 jewels)!
        if getattr(self, "price_discontent", False) and my_state.resources.jewels >= 15.0:
            blue_team = global_state.teams.get("BLUE")
            if blue_team and blue_team.resources.life >= 2:
                self.price_discontent = False
                return [
                    AttackAction(
                        attacker="RED",
                        target="BLUE",
                        weapon_type=WeaponType.WAR_DECLARATION,
                        jewels_spent=15.0,
                        description="레드가 블루의 라이프 독점 폭리(가격 불만)에 반발하여 공식 전쟁 선포! (15보석 지불)",
                    )
                ]

        # If Red has jewels for at least Tier C (10) or Tier B (20) and is in severe life crisis
        if days_of_life <= 1.5 and my_state.resources.jewels >= 10:
            target = "BLUE" if global_state.teams.get("BLUE", my_state).surviving_members > 0 else "WHITE"
            if my_state.resources.jewels >= 30 and random.random() < 0.3:
                cost = 30.0
                w_type = WeaponType.WEAPON_TIER_A
            elif my_state.resources.jewels >= 20 and random.random() < 0.5:
                cost = 20.0
                w_type = WeaponType.WEAPON_TIER_B
            else:
                cost = 10.0
                w_type = WeaponType.WEAPON_TIER_C

            actions.append(
                AttackAction(
                    attacker="RED",
                    target=target,
                    weapon_type=w_type,
                    jewels_spent=cost,
                    description=f"Red purchases {w_type.value} from Black Mart and strikes {target}!",
                )
            )
            self.attack_history_count += 1

        return actions

    def decide_black_purchases(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        catalog: List[BlackMarketItem],
    ) -> List[str]:
        return []
