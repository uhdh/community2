"""
tests/test_simulation.py
Integration tests for SimulationEngine and MonteCarloSimulator.
"""

from config import SimulationConfig
from simulation.engine import SimulationEngine
from simulation.monte_carlo import MonteCarloSimulator
from analysis.metrics import MetricsAnalyzer


def test_single_session_reaches_day_9():
    config = SimulationConfig(TOTAL_DAYS=9)
    engine = SimulationEngine(config=config)
    final_state = engine.run_simulation()

    # After 9 days, day index is 10
    assert final_state.day == 10
    # At least 1 survivor guaranteed
    mortal_survivors = sum(
        final_state.teams[t].surviving_members for t in ["WHITE", "BLUE", "RED"]
    )
    assert mortal_survivors >= 1
    # Prize unit value is non-negative
    assert final_state.jewel_unit_value > 0


def test_exception_rule_last_survivor_guarantee():
    """Verify that even under absolute starvation, 1 survivor remains."""
    config = SimulationConfig(
        TOTAL_DAYS=3,
        WHITE_LIFE=0,
        BLUE_LIFE=0,
        RED_LIFE=0,
    )
    engine = SimulationEngine(config=config)
    final_state = engine.run_simulation()

    mortal_survivors = sum(
        final_state.teams[t].surviving_members for t in ["WHITE", "BLUE", "RED"]
    )
    assert mortal_survivors == 1


def test_pollution_disaster_threshold():
    """Verify disaster triggers when pollution > 50."""
    config = SimulationConfig(
        TOTAL_DAYS=5,
        RED_POLLUTION_INCREMENT=30.0,  # 2 days will exceed 50
    )
    engine = SimulationEngine(config=config)
    final_state = engine.run_simulation()

    assert final_state.pollution_index > 50.0
    assert final_state.disaster_occurred is True


def test_black_confiscation_trigger():
    """Verify Black's assets are seized and distributed upon 3 reclaim pieces."""
    config = SimulationConfig(TOTAL_DAYS=5)
    engine = SimulationEngine(config=config)
    # Give Black some assets
    engine.state.teams["BLACK"].resources.jewels = 90.0
    engine.state.teams["BLACK"].resources.credits = 30.0

    # Simulate finding 3 pieces
    engine.state.reclaim_pieces_collected = 3
    engine._confiscate_black_assets()

    assert engine.state.black_confiscated is True
    assert engine.state.teams["BLACK"].resources.jewels == 0.0
    assert engine.state.teams["BLACK"].resources.credits == 0.0


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
