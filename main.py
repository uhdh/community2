"""
main.py
Main entry point and flow control for 'The Community 2: Invisible Hand'
Autonomous Agent Monte Carlo Simulator.
Reflects confirmed broadcast rules as of 2026-09-06.
"""

import os
import sys
import argparse
from typing import Optional

# Ensure UTF-8 stdout/stderr encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import DEFAULT_CONFIG, SimulationConfig
from simulation.engine import SimulationEngine
from simulation.monte_carlo import MonteCarloSimulator
from analysis.metrics import MetricsAnalyzer


def run_single_simulation(verbose: bool = True):
    """Run a single 9-day game session with detailed logging."""
    print("=" * 70)
    print("  더 커뮤니티 2: 보이지 않는 손 - 단일 세션 시뮬레이션")
    print("=" * 70)

    engine = SimulationEngine()
    final_state = engine.run_simulation()

    if verbose:
        for line in final_state.logs:
            print(line)

    print("\n" + "=" * 70)
    print("  [최종 게임 결과 요약]")
    print("=" * 70)
    print(f"최종 총 보석 유통량: {final_state.total_circulating_jewels:.1f}")
    print(f"최종 보석 1개당 가치: {final_state.jewel_unit_value:,.0f} 원")
    print(f"공해 수치: {final_state.pollution_index:.1f} (재앙 발생 여부: {final_state.disaster_occurred})")
    print(f"군사/무기 교전 횟수: {final_state.war_attacks_count} 회")
    print(f"블랙 마트 무기 매출: {final_state.black_arms_revenue:.1f} 보석")
    print("-" * 70)

    for name, team in final_state.teams.items():
        prize = team.calculate_prize(final_state.jewel_unit_value)
        per_capita = team.per_capita_prize(final_state.jewel_unit_value)
        status = "생존" if team.is_alive else "전멸"
        print(
            f"[{name.ljust(5)}] 상태: {status} | 생존: {team.surviving_members}/{team.initial_members}명 | "
            f"보석: {team.resources.jewels:.1f} | 라이프: {team.resources.life} | 크레딧: {team.resources.credits:.1f} | "
            f"총상금: {prize:,.0f}원 (1인당: {per_capita:,.0f}원)"
        )
    print("=" * 70)


def run_monte_carlo(runs: int, output_dir: str, workers: Optional[int] = None, seed: Optional[int] = 42):
    """Run N Monte Carlo simulations and output metrics & charts."""
    print("=" * 70)
    print(f"  더 커뮤니티 2: {runs:,}회 몬테카를로 시뮬레이션 시작")
    print(f"  출력 디렉토리: {output_dir}")
    print("=" * 70)

    simulator = MonteCarloSimulator()
    results = simulator.run(n_runs=runs, num_workers=workers, base_seed=seed)

    print(f"\n✅ {runs:,}회 시뮬레이션 완료! (소요 시간: {results.elapsed_time:.2f}초)")

    analyzer = MetricsAnalyzer(results, output_dir=output_dir)
    stats = analyzer.compute_metrics()
    report_md = analyzer.export_report()
    analyzer.generate_plots()

    print("\n" + report_md)
    print(f"📊 시각화 차트 및 분석 보고서가 저장되었습니다: {os.path.abspath(output_dir)}")


def main():
    parser = argparse.ArgumentParser(
        description="더 커뮤니티 2: 보이지 않는 손 - 자율 에이전트 몬테카를로 시뮬레이터"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "monte_carlo"],
        default="monte_carlo",
        help="실행 모드: 'single' (단일 상세 세션) 또는 'monte_carlo' (통계 시뮬레이션)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1000,
        help="몬테카를로 반복 횟수 (기본값: 1000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="병렬 워커 프로세스 수 (기본값: CPU 코어 수 자동 감지)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="분석 결과 및 차트 저장 디렉토리 (기본값: output)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="재현성을 위한 난수 시드 (기본값: 42)",
    )

    args = parser.parse_args()

    if args.mode == "single":
        run_single_simulation()
    else:
        run_monte_carlo(
            runs=args.runs,
            output_dir=args.output_dir,
            workers=args.workers,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
