"""
tests/test_simulation.py
Integration tests for SimulationEngine and MonteCarloSimulator.
Reflects confirmed broadcast rules as of 2026-09-06.
"""

from config import SimulationConfig
from simulation.engine import SimulationEngine
from simulation.monte_carlo import MonteCarloSimulator
from analysis.metrics import MetricsAnalyzer
from models.war import WeaponType, AttackAction


def test_single_session_reaches_day_9():
    config = SimulationConfig(TOTAL_DAYS=9)
    engine = SimulationEngine(config=config)
    final_state = engine.run_simulation()

    assert final_state.day == 9
    assert final_state.jewel_unit_value > 0


def test_black_mart_day1_exemption():
    """Verify Black Mart life exemption on Day 1, and deduction on Day 2+."""
    config = SimulationConfig(TOTAL_DAYS=2, BLACK_LIFE=2)
    engine = SimulationEngine(config=config)
    
    # Day 1: Black starts with 2 life, should NOT lose life for mart operation
    engine.state.day = 1
    engine.run_phase_3_evening()
    assert engine.state.teams["BLACK"].resources.life == 2

    # Day 2: Black should lose 1 life for mart operation
    engine.state.day = 2
    engine.run_phase_3_evening()
    assert engine.state.teams["BLACK"].resources.life == 1


def test_pollution_disaster_threshold():
    """Verify disaster triggers when pollution > 50."""
    config = SimulationConfig(
        TOTAL_DAYS=5,
        RED_POLLUTION_INCREMENT=30.0,
    )
    engine = SimulationEngine(config=config)
    final_state = engine.run_simulation()

    assert final_state.pollution_index > 50.0
    assert final_state.disaster_occurred is True


def test_arms_strike_deals_damage_and_pays_black():
    """Verify weapons purchased from Black Mart deduct jewels, credit Black, and damage target life."""
    config = SimulationConfig(TOTAL_DAYS=1)
    engine = SimulationEngine(config=config)

    # Setup White with 30 jewels to buy Tier A weapon
    engine.state.teams["WHITE"].resources.jewels = 30.0
    engine.state.teams["RED"].resources.life = 9
    engine.state.teams["BLACK"].resources.jewels = 0.0

    for p in engine.policies.values():
        p.generate_trade_offers = lambda s, m: []

    class AttackingWhitePolicy(engine.policies["WHITE"].__class__):
        def generate_trade_offers(self, global_state, my_state):
            return []

        def decide_war_actions(self, global_state, my_state):
            return [
                AttackAction(
                    attacker="WHITE",
                    target="RED",
                    weapon_type=WeaponType.WEAPON_TIER_A,
                    jewels_spent=30.0,
                )
            ]

    engine.policies["WHITE"] = AttackingWhitePolicy()
    engine.run_phase_2_afternoon()

    # White spent 30 jewels
    assert engine.state.teams["WHITE"].resources.jewels == 0.0
    # Black gained 30 jewels
    assert engine.state.teams["BLACK"].resources.jewels == 30.0
    # Red lost 4 life (Tier A = 4 dmg): 9 - 4 = 5
    assert engine.state.teams["RED"].resources.life == 5
    assert engine.state.war_attacks_count == 1


def test_group_last_survivor_exception_rule():
    """Verify official rulebook exception: each group's last 1 survivor never starves even at 0 life."""
    config = SimulationConfig(
        TOTAL_DAYS=1,
        WHITE_LIFE=0,
        BLUE_LIFE=0,
        RED_LIFE=0,
        INITIAL_LIFE_RESERVE=0,
        BLUE_CREDITS=0,
    )
    engine = SimulationEngine(config=config)
    final_state = engine.run_simulation()

    # Each group has exactly 1 protected survivor
    assert final_state.teams["WHITE"].surviving_members == 1
    assert final_state.teams["BLUE"].surviving_members == 1
    assert final_state.teams["RED"].surviving_members == 1


def test_monte_carlo_fast_run():
    config = SimulationConfig(TOTAL_DAYS=9)
    simulator = MonteCarloSimulator(config=config)
    results = simulator.run(n_runs=20, num_workers=1)

    assert results.n_runs == 20
    assert len(results.summary_df) == 20
    assert not results.daily_survival_df.empty
    assert not results.daily_macro_df.empty

    analyzer = MetricsAnalyzer(results)
    stats = analyzer.compute_metrics()
    assert stats["total_runs"] == 20
    assert "survival_rates_pct" in stats
    assert "prize_per_capita_krw" in stats


def test_inter_currency_bilateral_trading():
    """Verify inter-currency transactions: Credit-to-Jewel, Jewel-to-Life, and Credit-to-Life trades."""
    config = SimulationConfig(TOTAL_DAYS=1)
    engine = SimulationEngine(config=config)

    # Setup specific conditions for bilateral trades:
    # 1. Red has high credits (20.0) and low jewels (20.0) -> wants jewels
    engine.state.teams["RED"].resources.credits = 20.0
    engine.state.teams["RED"].resources.jewels = 20.0
    # 2. White has abundant jewels (100.0) and low credits (5.0) -> accepts credit trade
    engine.state.teams["WHITE"].resources.jewels = 100.0
    engine.state.teams["WHITE"].resources.credits = 5.0
    # 3. Blue has surplus life (20)
    engine.state.teams["BLUE"].resources.life = 20

    initial_red_credits = engine.state.teams["RED"].resources.credits
    initial_red_jewels = engine.state.teams["RED"].resources.jewels

    engine.run_phase_2_afternoon()

    red_res = engine.state.teams["RED"].resources
    # Verify trade occurred: credits decreased and/or jewels/life increased
    assert red_res.credits < initial_red_credits or red_res.jewels > initial_red_jewels or red_res.life > 9

