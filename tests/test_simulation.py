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


def test_famine_eliminates_all_without_life():
    """Verify that when mortal teams have 0 life and 0 reserve, they are eliminated without forced survival."""
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

    mortal_survivors = sum(
        final_state.teams[t].surviving_members for t in ["WHITE", "BLUE", "RED"]
    )
    assert mortal_survivors == 0


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
