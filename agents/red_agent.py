"""
agents/red_agent.py
Red Team strategy:
- Produces heavy credit volumes via clean or polluting production
- Exercises military deterrence via Bomb crafting (10 credits -> -3 life)
- Uses Pollution Index brinkmanship as systemic leverage
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
        If pollution is safely under threshold (e.g. < 40) and Red needs credits for bombs/trades,
        it uses polluting production.
        """
        current_pollution = global_state.pollution_index
        threshold = global_state.config.POLLUTION_DISASTER_THRESHOLD

        # If pollution is close to threshold (> 42), produce clean to avoid self-disaster
        # unless Red is dying and desperate (kamikaze brinkmanship)
        days_of_life = my_state.resources.life / max(1, my_state.surviving_members)

        if current_pollution + global_state.config.RED_POLLUTION_INCREMENT > threshold:
            if days_of_life <= 1.0 and my_state.resources.credits < 10:
                # Desperation: trigger disaster to drag others down
                use_pollution = True
            else:
                use_pollution = False
        else:
            # Under threshold: use pollution to generate military/economic advantage
            use_pollution = True

        return {"use_polluting_production": use_pollution}

    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Upgrades tech if credits >= upgrade_cost + 10 (keeping 10 credits for bomb defense)."""
        if my_state.tech.can_upgrade(my_state.resources.credits):
            return my_state.resources.credits >= my_state.tech.upgrade_cost + 10
        return False

    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[TradeOffer]:
        """
        Red desperately needs Life!
        Offers high credits or jewels for Life to Blue and White.
        """
        offers: List[TradeOffer] = []
        days_of_life = my_state.resources.life / max(1, my_state.surviving_members)

        # High priority offer to Blue for life
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

        # Offer jewels for life if credits are low
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

        # If incoming offer gives life, strongly accept (unless it demands too much life, which is impossible)
        if offer.offering.life > 0:
            return True

        # If trading surplus credits for jewels
        if offer.offering.jewels >= 18 and offer.requesting.credits <= 10:
            if my_state.resources.credits >= 15:
                return True

        return False

    def decide_reclaim_search(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Red searches for Reclaim Pieces if it has excess credits (> 20)."""
        cost = global_state.config.RECLAIM_SEARCH_CREDIT_COST
        if my_state.resources.credits >= cost + 12:
            return random.random() < 0.5
        return False

    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List[AttackAction]:
        """
        Red uses Bomb if credits >= 10 and:
        - Red is running low on life (< 2 days) and Blue/White won't trade.
        - Or Red targets the leader (White) to level the playing field.
        """
        actions: List[AttackAction] = []
        cost = global_state.config.BOMB_CREDIT_COST

        if my_state.resources.credits >= cost:
            days_of_life = my_state.resources.life / max(1, my_state.surviving_members)

            # Attack target decision
            white_state = global_state.teams.get("WHITE")
            blue_state = global_state.teams.get("BLUE")

            target = None
            # If Blue has monopoly and won't trade life, retaliate against Blue
            if days_of_life <= 2.0 and blue_state and blue_state.surviving_members > 0:
                target = "BLUE"
            # Otherwise attack White (the leader with 6 members)
            elif white_state and white_state.surviving_members > 2 and random.random() < 0.45:
                target = "WHITE"
            elif random.random() < 0.25:
                target = "BLUE"

            if target:
                actions.append(
                    AttackAction(
                        attacker="RED",
                        target=target,
                        weapon_type=WeaponType.RED_BOMB,
                        credit_spent=float(cost),
                        description="Red team detonates a lethal bomb strike!",
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
        """Red may buy sabotage or shield if credits exceed 22."""
        purchases: List[str] = []
        if my_state.resources.credits >= 22 and not my_state.has_shield:
            purchases.append(WeaponType.SHIELD.value)
        return purchases
