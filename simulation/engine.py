"""
simulation/engine.py
Daily 3-Phase Turn Loop Engine for 'The Community 2: Invisible Hand'.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from config import SimulationConfig, DEFAULT_CONFIG
from models.resources import ResourceBundle
from models.tech import TechTree
from models.war import WeaponType, AttackAction, AttackResult, get_default_black_catalog
from models.market import TradeOffer, MarketEngine
from models.team import TeamType, TeamState
from agents.policy import BasePolicy
from agents.white_agent import WhitePolicy
from agents.blue_agent import BluePolicy
from agents.red_agent import RedPolicy
from agents.black_agent import BlackPolicy


@dataclass
class GlobalState:
    day: int = 1
    config: SimulationConfig = field(default_factory=SimulationConfig)
    life_reserve: int = 50
    pollution_index: float = 0.0
    disaster_occurred: bool = False
    reclaim_pieces_collected: int = 0
    black_confiscated: bool = False
    black_arms_revenue: float = 0.0
    jewel_unit_value: float = 0.0
    total_circulating_jewels: float = 0.0
    war_attacks_count: int = 0
    teams: Dict[str, TeamState] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    def log(self, message: str):
        entry = f"[Day {self.day}] {message}"
        self.logs.append(entry)


class SimulationEngine:
    def __init__(
        self,
        config: SimulationConfig = DEFAULT_CONFIG,
        policies: Optional[Dict[str, BasePolicy]] = None,
    ):
        self.config = config
        self.market_engine = MarketEngine()
        self.state = self._initialize_state()
        
        # Assign agent policies
        if policies is None:
            self.policies: Dict[str, BasePolicy] = {
                "WHITE": WhitePolicy(),
                "BLUE": BluePolicy(),
                "RED": RedPolicy(),
                "BLACK": BlackPolicy(),
            }
        else:
            self.policies = policies

    def _initialize_state(self) -> GlobalState:
        teams = {
            "WHITE": TeamState(
                team_type=TeamType.WHITE,
                initial_members=self.config.WHITE_MEMBERS,
                surviving_members=self.config.WHITE_MEMBERS,
                resources=ResourceBundle(
                    jewels=float(self.config.WHITE_JEWELS),
                    life=self.config.WHITE_LIFE,
                    credits=float(self.config.WHITE_CREDITS),
                ),
            ),
            "BLUE": TeamState(
                team_type=TeamType.BLUE,
                initial_members=self.config.BLUE_MEMBERS,
                surviving_members=self.config.BLUE_MEMBERS,
                resources=ResourceBundle(
                    jewels=float(self.config.BLUE_JEWELS),
                    life=self.config.BLUE_LIFE,
                    credits=float(self.config.BLUE_CREDITS),
                ),
            ),
            "RED": TeamState(
                team_type=TeamType.RED,
                initial_members=self.config.RED_MEMBERS,
                surviving_members=self.config.RED_MEMBERS,
                resources=ResourceBundle(
                    jewels=float(self.config.RED_JEWELS),
                    life=self.config.RED_LIFE,
                    credits=float(self.config.RED_CREDITS),
                ),
            ),
            "BLACK": TeamState(
                team_type=TeamType.BLACK,
                initial_members=self.config.BLACK_MEMBERS,
                surviving_members=self.config.BLACK_MEMBERS,
                resources=ResourceBundle(
                    jewels=float(self.config.BLACK_JEWELS),
                    life=self.config.BLACK_LIFE,
                    credits=float(self.config.BLACK_CREDITS),
                ),
            ),
        }

        circulating_jewels = sum(t.resources.jewels for t in teams.values())
        unit_val = (
            self.config.TOTAL_PRIZE_POOL / circulating_jewels
            if circulating_jewels > 0
            else 0.0
        )

        return GlobalState(
            day=1,
            config=self.config,
            life_reserve=self.config.INITIAL_LIFE_RESERVE,
            pollution_index=0.0,
            disaster_occurred=False,
            reclaim_pieces_collected=0,
            black_confiscated=False,
            black_arms_revenue=0.0,
            jewel_unit_value=unit_val,
            total_circulating_jewels=circulating_jewels,
            teams=teams,
        )

    def run_phase_1_morning_production(self):
        """Phase 1: Morning Production and Resource Generation."""
        self.state.log("--- Phase 1: Morning Production Begins ---")
        
        # 1. White Jewel Issuance
        white_team = self.state.teams["WHITE"]
        if white_team.is_alive:
            white_dec = self.policies["WHITE"].decide_morning_production(
                self.state, white_team
            )
            mint_amount = max(0, min(self.config.WHITE_JEWEL_MINT_MAX, white_dec.get("mint_jewels", 0)))
            white_team.resources.jewels += mint_amount
            self.state.log(f"White minted {mint_amount} jewels. Total jewels: {white_team.resources.jewels:.1f}")

        # 2. Blue Life Production
        blue_team = self.state.teams["BLUE"]
        if blue_team.is_alive and self.state.life_reserve > 0:
            blue_dec = self.policies["BLUE"].decide_morning_production(
                self.state, blue_team
            )
            desired_life = blue_dec.get("produce_life", 0)
            cost_per_life = blue_team.tech.get_blue_credit_per_life()
            max_possible = int(blue_team.resources.credits // cost_per_life)
            producible = min(desired_life, max_possible, self.state.life_reserve)
            
            if producible > 0:
                credit_spent = producible * cost_per_life
                blue_team.resources.credits -= credit_spent
                blue_team.resources.life += producible
                self.state.life_reserve -= producible
                self.state.log(
                    f"Blue produced {producible} Life (Spent {credit_spent:.1f} credits). "
                    f"Remaining Life Reserve: {self.state.life_reserve}"
                )

        # 3. Red Credit Production (Clean vs Polluting)
        red_team = self.state.teams["RED"]
        if red_team.is_alive:
            red_dec = self.policies["RED"].decide_morning_production(
                self.state, red_team
            )
            use_polluting = red_dec.get("use_polluting_production", False)
            mult = red_team.tech.get_production_multiplier()

            if use_polluting:
                yield_credits = self.config.RED_POLLUTING_CREDIT_YIELD * mult
                red_team.resources.credits += yield_credits
                self.state.pollution_index += self.config.RED_POLLUTION_INCREMENT
                self.state.log(
                    f"Red engaged in POLLUTING production: +{yield_credits:.1f} credits. "
                    f"Pollution Index rose to {self.state.pollution_index:.1f}"
                )
            else:
                yield_credits = self.config.RED_CLEAN_CREDIT_YIELD * mult
                red_team.resources.credits += yield_credits
                self.state.log(
                    f"Red engaged in CLEAN production: +{yield_credits:.1f} credits. "
                    f"Pollution Index remains {self.state.pollution_index:.1f}"
                )

            # Check Pollution Disaster
            if self.state.pollution_index > self.config.POLLUTION_DISASTER_THRESHOLD and not self.state.disaster_occurred:
                self.state.disaster_occurred = True
                self.state.log(
                    f"[DISASTER] Pollution Index ({self.state.pollution_index:.1f}) > 50.0! "
                    "30% of all goods across all teams are destroyed!"
                )
                for t_name, team in self.state.teams.items():
                    team.resources = team.resources.apply_disaster(self.config.DISASTER_PENALTY_RATIO)

        # 4. Black Mart adjustments
        black_team = self.state.teams["BLACK"]
        if black_team.is_alive:
            black_dec = self.policies["BLACK"].decide_morning_production(
                self.state, black_team
            )
            mult = black_dec.get("price_multiplier", 1.0)
            self.state.log(f"Black Mart catalog prepared with price index x{mult:.2f}")

    def run_phase_2_afternoon(self):
        """Phase 2: Afternoon Trade, Tech Investment, and War Actions."""
        self.state.log("--- Phase 2: Afternoon Market, Tech, and War Begins ---")
        
        # 1. Tech Upgrades
        for t_name, team in self.state.teams.items():
            if team.is_alive:
                policy = self.policies[t_name]
                if policy.decide_tech_upgrade(self.state, team):
                    cost = team.tech.upgrade_cost
                    if team.resources.credits >= cost:
                        team.resources.credits -= cost
                        team.tech.upgrade()
                        self.state.log(f"{t_name} upgraded Tech to Level {team.tech.level} (Spent {cost} credits).")

        # 2. Market Trading
        offers_pool: List[TradeOffer] = []
        for t_name, team in self.state.teams.items():
            if team.is_alive:
                offers = self.policies[t_name].generate_trade_offers(self.state, team)
                for off in offers:
                    off.offer_id = f"{t_name}_{self.state.day}_{random.randint(100, 999)}"
                    offers_pool.append(off)

        # Shuffle offers to avoid turn order bias
        random.shuffle(offers_pool)
        for offer in offers_pool:
            receiver_team = self.state.teams.get(offer.receiver)
            sender_team = self.state.teams.get(offer.sender)
            if receiver_team and sender_team and receiver_team.is_alive and sender_team.is_alive:
                receiver_policy = self.policies[offer.receiver]
                if receiver_policy.evaluate_trade_offer(self.state, receiver_team, offer):
                    success = self.market_engine.execute_trade(
                        self.state.day, offer, sender_team.resources, receiver_team.resources
                    )
                    if success:
                        self.state.log(
                            f"[TRADE] Executed: {offer.sender} gave {offer.offering} -> "
                            f"{offer.receiver} gave {offer.requesting}"
                        )

        # 3. Black Mart Purchases (Shields, Sabotage)
        black_team = self.state.teams["BLACK"]
        catalog = get_default_black_catalog()
        for t_name, team in self.state.teams.items():
            if t_name != "BLACK" and team.is_alive:
                items_wanted = self.policies[t_name].decide_black_purchases(
                    self.state, team, catalog
                )
                for item_name in items_wanted:
                    if item_name == WeaponType.SHIELD.value:
                        # Price check: prefer credits, else jewels
                        if team.resources.credits >= self.config.SHIELD_CREDIT_PRICE:
                            team.resources.credits -= self.config.SHIELD_CREDIT_PRICE
                            black_team.resources.credits += self.config.SHIELD_CREDIT_PRICE
                            self.state.black_arms_revenue += self.config.SHIELD_CREDIT_PRICE
                            team.has_shield = True
                            self.state.log(f"[SHIELD] {t_name} purchased Bomb Shield from Black for {self.config.SHIELD_CREDIT_PRICE} credits.")
                        elif team.resources.jewels >= self.config.SHIELD_JEWEL_PRICE:
                            team.resources.jewels -= self.config.SHIELD_JEWEL_PRICE
                            black_team.resources.jewels += self.config.SHIELD_JEWEL_PRICE
                            self.state.black_arms_revenue += self.config.SHIELD_JEWEL_PRICE
                            team.has_shield = True
                            self.state.log(f"[SHIELD] {t_name} purchased Bomb Shield from Black for {self.config.SHIELD_JEWEL_PRICE} jewels.")

        # 4. War & Military Actions (Red Bomb)
        for t_name, team in self.state.teams.items():
            if team.is_alive:
                attacks = self.policies[t_name].decide_war_actions(self.state, team)
                for attack in attacks:
                    if attack.weapon_type == WeaponType.RED_BOMB:
                        target_team = self.state.teams.get(attack.target)
                        cost = self.config.BOMB_CREDIT_COST
                        if team.resources.credits >= cost and target_team and target_team.is_alive:
                            team.resources.credits -= cost
                            self.state.war_attacks_count += 1
                            if target_team.has_shield:
                                target_team.has_shield = False
                                self.state.log(f"[BOMB] {t_name} bombed {attack.target}, but it was BLOCKED by Bomb Shield!")
                            else:
                                damage = min(self.config.BOMB_LIFE_DAMAGE, target_team.resources.life)
                                target_team.resources.life -= damage
                                self.state.log(f"[BOMB] {t_name} bombed {attack.target}! Dealt {damage} Life damage!")

        # 5. Reclaim Pieces Search (Anti-Black Alliance)
        if not self.state.black_confiscated:
            for t_name, team in self.state.teams.items():
                if t_name != "BLACK" and team.is_alive:
                    if self.policies[t_name].decide_reclaim_search(self.state, team):
                        cost = self.config.RECLAIM_SEARCH_CREDIT_COST
                        if team.resources.credits >= cost:
                            team.resources.credits -= cost
                            team.search_attempts += 1
                            if random.random() < self.config.RECLAIM_SEARCH_SUCCESS_PROB:
                                self.state.reclaim_pieces_collected += 1
                                self.state.log(
                                    f"[RECLAIM] {t_name} uncovered a Reclaim Piece! "
                                    f"Total Collected: {self.state.reclaim_pieces_collected}/{self.config.RECLAIM_PIECES_NEEDED}"
                                )
                                # Check 3 pieces confiscation
                                if self.state.reclaim_pieces_collected >= self.config.RECLAIM_PIECES_NEEDED:
                                    self._confiscate_black_assets()
                                    break

    def _confiscate_black_assets(self):
        """Confiscate Black's assets and distribute among surviving mortal teams."""
        self.state.black_confiscated = True
        black_team = self.state.teams["BLACK"]
        black_team.is_confiscated = True
        seized_jewels = black_team.resources.jewels
        seized_credits = black_team.resources.credits
        black_team.resources.jewels = 0.0
        black_team.resources.credits = 0.0

        surviving_teams = [
            t for name, t in self.state.teams.items() if name != "BLACK" and t.is_alive
        ]
        if surviving_teams:
            j_share = seized_jewels / len(surviving_teams)
            c_share = seized_credits / len(surviving_teams)
            for t in surviving_teams:
                t.resources.jewels += j_share
                t.resources.credits += c_share
            self.state.log(
                f"[CONFISCATION] 3 RECLAIM PIECES COLLECTED! Black's assets seized! "
                f"Distributed {j_share:.1f} jewels and {c_share:.1f} credits to each surviving team!"
            )
        else:
            self.state.log("[CONFISCATION] Black assets confiscated, but no mortal teams remain.")

    def run_phase_3_evening(self):
        """Phase 3: Evening Life Submission and Survival Check."""
        self.state.log("--- Phase 3: Evening Life Submission Begins ---")
        
        # Submit life for mortal teams
        for t_name in ["WHITE", "BLUE", "RED"]:
            team = self.state.teams[t_name]
            if team.is_alive:
                prev_members = team.surviving_members
                deaths = team.submit_daily_life(self.config.DAILY_LIFE_REQUIREMENT)
                if deaths > 0:
                    self.state.log(f"[CASUALTY] {t_name} lost {deaths} members due to life shortage. Surviving: {team.surviving_members}")
                else:
                    self.state.log(f"[SURVIVAL] {t_name} all {team.surviving_members} members survived. Life left: {team.resources.life}")

        # Black Mart daily life cost (Day 1 exemption confirmed on 2026.09.06)
        black_team = self.state.teams["BLACK"]
        if self.state.day == 1 and self.config.BLACK_MART_DAY1_LIFE_EXEMPT:
            self.state.log("[BLACK MART] Day 1 special exemption: Mart opened without life deduction (0 life spent).")
        else:
            black_team.submit_daily_life(self.config.BLACK_MART_DAILY_LIFE_COST)

        # Exception Rule: Last 1 survivor guarantee
        # "어떠한 상황에서도 최후의 1인 생존은 보장됩니다."
        total_mortal_survivors = sum(
            self.state.teams[t].surviving_members for t in ["WHITE", "BLUE", "RED"]
        )
        if total_mortal_survivors == 0:
            # Pick the team with the highest remaining assets or White by default
            fallback_team = max(
                ["WHITE", "BLUE", "RED"],
                key=lambda t: (self.state.teams[t].resources.jewels + self.state.teams[t].resources.credits),
            )
            self.state.teams[fallback_team].surviving_members = 1
            self.state.log(
                f"[EXCEPTION] EXCEPTION RULE ACTIVATED: Last 1 survivor guaranteed! "
                f"1 member of {fallback_team} survives against all odds!"
            )

        # Update circulating jewels & unit value
        circulating = sum(t.resources.jewels for t in self.state.teams.values())
        self.state.total_circulating_jewels = circulating
        self.state.jewel_unit_value = (
            self.config.TOTAL_PRIZE_POOL / circulating if circulating > 0 else 0.0
        )
        self.state.log(
            f"[VALUE] Day {self.state.day} End: Total Jewels={circulating:.1f}, "
            f"Jewel Value={self.state.jewel_unit_value:,.0f} KRW"
        )

    def step_day(self):
        """Execute all 3 phases of a single day."""
        self.run_phase_1_morning_production()
        self.run_phase_2_afternoon()
        self.run_phase_3_evening()
        self.state.day += 1

    def run_simulation(self) -> GlobalState:
        """Run the full 9-day simulation session."""
        for _ in range(self.config.TOTAL_DAYS):
            self.step_day()
        return self.state
