"""
simulation/engine.py
Daily 3-Phase Turn Loop Engine for 'The Community 2: Invisible Hand'.
Reflects confirmed broadcast rules as of 2026-09-06.
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
    prize_pool: float = 200000000.0
    life_reserve: int = 50
    pollution_index: float = 0.0
    disaster_occurred: bool = False
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
        self.black_catalog = get_default_black_catalog()
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
            prize_pool=float(self.config.TOTAL_PRIZE_POOL),
            life_reserve=self.config.INITIAL_LIFE_RESERVE,
            pollution_index=0.0,
            disaster_occurred=False,
            black_arms_revenue=0.0,
            jewel_unit_value=unit_val,
            total_circulating_jewels=circulating_jewels,
            war_attacks_count=0,
            teams=teams,
        )

    def run_simulation(self) -> GlobalState:
        """Run full game session over TOTAL_DAYS."""
        for day in range(1, self.config.TOTAL_DAYS + 1):
            self.state.day = day
            self.run_day_turn()
        return self.state

    def run_day_turn(self):
        """Execute one full daily cycle: Phase 1, Phase 2, Phase 3."""
        self.state.log(f"===== DAY {self.state.day} BEGINS =====")
        self.run_phase_1_morning_production()
        self.run_phase_2_afternoon()
        self.run_phase_3_evening()

    def run_phase_1_morning_production(self):
        """Phase 1: Morning Production & Pollution Check."""
        self.state.log("--- Phase 1: Morning Production Begins ---")
        
        # 1. White: Minting Jewels
        white_team = self.state.teams["WHITE"]
        if white_team.is_alive:
            prod_decision = self.policies["WHITE"].decide_morning_production(
                self.state, white_team
            )
            mint_amount = float(prod_decision.get("mint_jewels", 0))
            mint_amount = min(mint_amount, float(self.config.WHITE_JEWEL_MINT_MAX))
            white_team.resources.jewels += mint_amount
            self.state.log(f"[MINT] White minted {mint_amount:.1f} jewels. Total White Jewels: {white_team.resources.jewels:.1f}")

        # 2. Blue: Life Production from Global Reserve
        blue_team = self.state.teams["BLUE"]
        if blue_team.is_alive and self.state.life_reserve > 0:
            prod_decision = self.policies["BLUE"].decide_morning_production(
                self.state, blue_team
            )
            desired_life = int(prod_decision.get("produce_life", 0))
            credit_per_life = blue_team.tech.get_blue_credit_per_life()
            
            # Max possible by credits & available reserve
            max_by_credits = int(blue_team.resources.credits // credit_per_life)
            actual_life = min(desired_life, max_by_credits, self.state.life_reserve)
            
            if actual_life > 0:
                cost = actual_life * credit_per_life
                blue_team.resources.credits -= cost
                blue_team.resources.life += actual_life
                self.state.life_reserve -= actual_life
                self.state.log(
                    f"[LIFE PRODUCTION] Blue produced {actual_life} Life using {cost:.1f} Credits. "
                    f"Remaining Global Reserve: {self.state.life_reserve}"
                )

        # 3. Red: Industrial Credit Production & Pollution Index
        red_team = self.state.teams["RED"]
        if red_team.is_alive:
            prod_decision = self.policies["RED"].decide_morning_production(
                self.state, red_team
            )
            use_polluting = prod_decision.get("use_polluting_production", False)
            mult = red_team.tech.get_production_multiplier()
            
            if use_polluting:
                produced_credits = self.config.RED_POLLUTING_CREDIT_YIELD * mult
                self.state.pollution_index += self.config.RED_POLLUTION_INCREMENT
                red_team.resources.credits += produced_credits
                self.state.log(
                    f"[INDUSTRIAL PRODUCTION] Red chose POLLUTING production (+{produced_credits:.1f} Credits). "
                    f"Current Pollution Index: {self.state.pollution_index:.1f}"
                )
            else:
                produced_credits = self.config.RED_CLEAN_CREDIT_YIELD * mult
                red_team.resources.credits += produced_credits
                self.state.log(
                    f"[INDUSTRIAL PRODUCTION] Red chose CLEAN production (+{produced_credits:.1f} Credits). "
                    f"Current Pollution Index: {self.state.pollution_index:.1f}"
                )

        # 4. Black: Mart Preparation
        black_team = self.state.teams["BLACK"]
        self.policies["BLACK"].decide_morning_production(self.state, black_team)

        # 5. Pollution Threshold & Disaster Check
        if (
            self.state.pollution_index > self.config.POLLUTION_DISASTER_THRESHOLD
            and not self.state.disaster_occurred
        ):
            self._trigger_pollution_disaster()

    def _trigger_pollution_disaster(self):
        """Pollution index exceeded threshold: 30% penalty applied to all teams."""
        self.state.disaster_occurred = True
        self.state.log(
            f"[DISASTER TRIGGERED] Pollution Index reached {self.state.pollution_index:.1f} "
            f"(> {self.config.POLLUTION_DISASTER_THRESHOLD})! 30% destruction of all assets!"
        )
        for t_name, team in self.state.teams.items():
            team.resources = team.resources.apply_disaster(
                self.config.DISASTER_PENALTY_RATIO
            )
            self.state.log(
                f"[DISASTER PENALTY] {t_name} resources reduced by 30%: {team.resources}"
            )

    def run_phase_2_afternoon(self):
        """Phase 2: Afternoon Market, Technology Upgrades, and Black Mart Arms Deals."""
        self.state.log("--- Phase 2: Afternoon Market & Arms Deals Begins ---")

        # 1. Technology Upgrades
        for t_name, team in self.state.teams.items():
            if team.is_alive and self.policies[t_name].decide_tech_upgrade(
                self.state, team
            ):
                cost = team.tech.upgrade_cost
                if team.resources.credits >= cost and team.tech.upgrade():
                    team.resources.credits -= cost
                    self.state.log(f"[TECH UPGRADE] {t_name} upgraded to Tech Level {team.tech.level} (spent {cost} credits)!")

        # 2. Market Trading & Bilateral Offers
        all_offers: List[TradeOffer] = []
        for t_name, team in self.state.teams.items():
            if team.is_alive:
                offers = self.policies[t_name].generate_trade_offers(self.state, team)
                all_offers.extend(offers)

        # Execute market trades
        for offer in all_offers:
            sender_team = self.state.teams.get(offer.sender)
            receiver_team = self.state.teams.get(offer.receiver)
            if not sender_team or not receiver_team:
                continue
            if not sender_team.is_alive or not receiver_team.is_alive:
                continue

            if sender_team.resources.can_afford(offer.offering):
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

        # 3. Black Mart Catalog Purchases (Groceries/Supplies)
        black_team = self.state.teams["BLACK"]
        for t_name, team in self.state.teams.items():
            if team.is_alive and t_name != "BLACK":
                purchases = self.policies[t_name].decide_black_purchases(
                    self.state, team, self.black_catalog
                )
                if "GROCERY" in purchases:
                    if team.resources.jewels >= 1.0:
                        team.resources.jewels -= 1.0
                        black_team.resources.jewels += 1.0
                        self.state.log(f"[MART GROCERY] {t_name} purchased daily supplies from Black Mart (paid 1.0 jewel).")
                    elif team.resources.credits >= 2.0:
                        team.resources.credits -= 2.0
                        black_team.resources.credits += 2.0
                        self.state.log(f"[MART GROCERY] {t_name} purchased daily supplies from Black Mart (paid 2.0 credits).")

        # 4. War & Military Actions via Black Mart
        # Factions purchase weapons (A/B/C tier) or declare war using jewels at Black Mart
        damage_map = {
            WeaponType.WEAPON_TIER_A: 4,
            WeaponType.WEAPON_TIER_B: 2,
            WeaponType.WEAPON_TIER_C: 1,
            WeaponType.WAR_DECLARATION: 0,
        }

        for t_name, team in self.state.teams.items():
            if team.is_alive and t_name != "BLACK":
                attacks = self.policies[t_name].decide_war_actions(self.state, team)
                for attack in attacks:
                    cost = attack.jewels_spent
                    target_team = self.state.teams.get(attack.target)
                    if team.resources.jewels >= cost and target_team and target_team.is_alive:
                        team.resources.jewels -= cost
                        black_team.resources.jewels += cost  # Black Mart receives the jewels
                        self.state.black_arms_revenue += cost
                        self.state.war_attacks_count += 1
                        
                        dmg = damage_map.get(attack.weapon_type, 1)
                        if dmg > 0:
                            actual_dmg = min(dmg, target_team.resources.life)
                            target_team.resources.life -= actual_dmg
                            self.state.log(
                                f"[ARMS STRIKE] {t_name} purchased {attack.weapon_type.value} from Black Mart "
                                f"({cost} jewels) and struck {attack.target}! Dealt {actual_dmg} Life damage!"
                            )
                        else:
                            # WAR DECLARATION (15 jewels to Black Mart)
                            # 1. Total prize pool deduction rule
                            war_cost_krw = cost * self.state.jewel_unit_value
                            self.state.prize_pool = max(0.0, self.state.prize_pool - war_cost_krw)

                            # 2. 50% Resource Looting Rule (50% of all target resources looted)
                            loot_pct = self.config.WAR_LOOT_PERCENTAGE
                            looted_jewels = round(target_team.resources.jewels * loot_pct, 1)
                            looted_life = math.floor(target_team.resources.life * loot_pct)
                            looted_credits = round(target_team.resources.credits * loot_pct, 1)

                            target_team.resources.jewels -= looted_jewels
                            target_team.resources.life -= looted_life
                            target_team.resources.credits -= looted_credits

                            team.resources.jewels += looted_jewels
                            team.resources.life += looted_life
                            team.resources.credits += looted_credits

                            self.state.log(
                                f"[WAR DECLARATION & 50% LOOT] {t_name} declared war on {attack.target} "
                                f"({cost} jewels to Black Mart, 총상금 {war_cost_krw:,.0f}원 영구 차감)! "
                                f"Looted 50% of resources: +{looted_jewels} Jewels, +{looted_life} Life, +{looted_credits} Credits!"
                            )

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

        # Update circulating jewels & unit value
        circulating = sum(t.resources.jewels for t in self.state.teams.values())
        self.state.total_circulating_jewels = circulating
        if circulating > 0:
            self.state.jewel_unit_value = self.state.prize_pool / circulating
        else:
            self.state.jewel_unit_value = 0.0

        self.state.log(
            f"[END OF DAY {self.state.day}] Circulating Jewels: {circulating:.1f}, "
            f"Jewel Unit Value: {self.state.jewel_unit_value:,.0f} KRW"
        )
