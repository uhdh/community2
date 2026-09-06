"""
simulation/monte_carlo.py
Monte Carlo simulation engine with parallel processing and metrics extraction.
Reflects confirmed broadcast rules as of 2026-09-06.
"""

import time
import random
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from concurrent.futures import ProcessPoolExecutor

from config import SimulationConfig, DEFAULT_CONFIG
from simulation.engine import SimulationEngine, GlobalState


@dataclass
class SingleRunResult:
    run_id: int
    survivors_final: Dict[str, int]
    jewels_final: Dict[str, float]
    prize_per_capita: Dict[str, float]
    total_prize: Dict[str, float]
    disaster_occurred: bool
    pollution_final: float
    black_arms_revenue: float
    war_attacks_count: int
    remaining_life_reserve: int
    final_jewel_unit_value: float
    daily_survivors: Dict[str, List[int]]  # team -> [survivors on day 1..9]
    daily_life_reserves: List[int] = field(default_factory=list)
    daily_jewel_values: List[float] = field(default_factory=list)
    daily_pollutions: List[float] = field(default_factory=list)


def _worker_single_simulation(args) -> SingleRunResult:
    """Worker function for parallel execution."""
    run_id, seed, config = args
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed % (2**32 - 1))

    engine = SimulationEngine(config=config)
    
    daily_survivors = {"WHITE": [], "BLUE": [], "RED": [], "BLACK": []}
    daily_life_reserves = []
    daily_jewel_values = []
    daily_pollutions = []
    
    for day_idx in range(config.TOTAL_DAYS):
        engine.run_phase_1_morning_production()
        engine.run_phase_2_afternoon()
        engine.run_phase_3_evening()
        
        # Record daily survivors and macro metrics at evening
        for t_name, team in engine.state.teams.items():
            daily_survivors[t_name].append(team.surviving_members)
        
        daily_life_reserves.append(engine.state.life_reserve)
        daily_jewel_values.append(engine.state.jewel_unit_value)
        daily_pollutions.append(engine.state.pollution_index)
            
        engine.state.day += 1

    final_state = engine.state
    unit_val = final_state.jewel_unit_value

    survivors_final = {t: team.surviving_members for t, team in final_state.teams.items()}
    jewels_final = {t: team.resources.jewels for t, team in final_state.teams.items()}
    prize_per_capita = {
        t: team.per_capita_prize(unit_val) for t, team in final_state.teams.items()
    }
    total_prize = {
        t: team.calculate_prize(unit_val) for t, team in final_state.teams.items()
    }

    return SingleRunResult(
        run_id=run_id,
        survivors_final=survivors_final,
        jewels_final=jewels_final,
        prize_per_capita=prize_per_capita,
        total_prize=total_prize,
        disaster_occurred=final_state.disaster_occurred,
        pollution_final=final_state.pollution_index,
        black_arms_revenue=final_state.black_arms_revenue,
        war_attacks_count=final_state.war_attacks_count,
        remaining_life_reserve=final_state.life_reserve,
        final_jewel_unit_value=unit_val,
        daily_survivors=daily_survivors,
        daily_life_reserves=daily_life_reserves,
        daily_jewel_values=daily_jewel_values,
        daily_pollutions=daily_pollutions,
    )


@dataclass
class MonteCarloResults:
    n_runs: int
    elapsed_time: float
    summary_df: pd.DataFrame
    daily_survival_df: pd.DataFrame
    daily_macro_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    raw_results: List[SingleRunResult] = field(default_factory=list)


class MonteCarloSimulator:
    def __init__(self, config: SimulationConfig = DEFAULT_CONFIG):
        self.config = config

    def run(
        self,
        n_runs: int = 1000,
        num_workers: Optional[int] = None,
        base_seed: Optional[int] = 42,
    ) -> MonteCarloResults:
        """Run N Monte Carlo simulations, in parallel if num_workers != 1."""
        start_time = time.time()
        tasks = []
        for i in range(n_runs):
            seed = (base_seed + i * 17) if base_seed is not None else None
            tasks.append((i, seed, self.config))

        results: List[SingleRunResult] = []

        # Windows ProcessPoolExecutor safety
        if num_workers == 1 or n_runs <= 50:
            for task in tasks:
                results.append(_worker_single_simulation(task))
        else:
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                results = list(executor.map(_worker_single_simulation, tasks))

        elapsed = time.time() - start_time

        # Build Summary DataFrame
        rows = []
        for res in results:
            rows.append({
                "run_id": res.run_id,
                "survivors_white": res.survivors_final["WHITE"],
                "survivors_blue": res.survivors_final["BLUE"],
                "survivors_red": res.survivors_final["RED"],
                "survivors_black": res.survivors_final["BLACK"],
                "prize_per_capita_white": res.prize_per_capita["WHITE"],
                "prize_per_capita_blue": res.prize_per_capita["BLUE"],
                "prize_per_capita_red": res.prize_per_capita["RED"],
                "prize_per_capita_black": res.prize_per_capita["BLACK"],
                "jewels_white": res.jewels_final["WHITE"],
                "jewels_blue": res.jewels_final["BLUE"],
                "jewels_red": res.jewels_final["RED"],
                "jewels_black": res.jewels_final["BLACK"],
                "disaster_occurred": res.disaster_occurred,
                "pollution_final": res.pollution_final,
                "war_attacks_count": res.war_attacks_count,
                "black_arms_revenue": res.black_arms_revenue,
                "remaining_life_reserve": res.remaining_life_reserve,
                "final_jewel_unit_value": res.final_jewel_unit_value,
            })
        summary_df = pd.DataFrame(rows)

        # Build Daily Survival DataFrame
        daily_rows = []
        macro_rows = []
        for res in results:
            for team, trajectory in res.daily_survivors.items():
                for day_idx, count in enumerate(trajectory, start=1):
                    daily_rows.append({
                        "run_id": res.run_id,
                        "day": day_idx,
                        "team": team,
                        "survivors": count,
                    })
            for day_idx in range(len(res.daily_life_reserves)):
                macro_rows.append({
                    "run_id": res.run_id,
                    "day": day_idx + 1,
                    "life_reserve": res.daily_life_reserves[day_idx],
                    "jewel_unit_value": res.daily_jewel_values[day_idx],
                    "pollution_index": res.daily_pollutions[day_idx],
                })
        daily_df = pd.DataFrame(daily_rows)
        macro_df = pd.DataFrame(macro_rows)

        return MonteCarloResults(
            n_runs=n_runs,
            elapsed_time=elapsed,
            summary_df=summary_df,
            daily_survival_df=daily_df,
            daily_macro_df=macro_df,
            raw_results=results,
        )
