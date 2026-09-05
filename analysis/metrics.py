"""
analysis/metrics.py
Statistical analysis, metrics calculation, and publication-quality visualizations.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Optional

from simulation.monte_carlo import MonteCarloResults


# Set plotting aesthetic & font support for Windows
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = ["Malgun Gothic", "Segoe UI", "DejaVu Sans", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


class MetricsAnalyzer:
    def __init__(self, results: MonteCarloResults, output_dir: str = "output"):
        self.results = results
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.summary_stats: Dict[str, Any] = {}

    def compute_metrics(self) -> Dict[str, Any]:
        """Compute all core metrics required by the specification."""
        df = self.results.summary_df
        n = len(df)

        # 1. Final Survival Rate per Team
        initial_members = {"WHITE": 6, "BLUE": 3, "RED": 3, "BLACK": 1}
        survival_rates = {
            "WHITE": float((df["survivors_white"] / 6).mean() * 100),
            "BLUE": float((df["survivors_blue"] / 3).mean() * 100),
            "RED": float((df["survivors_red"] / 3).mean() * 100),
            "BLACK": float((df["survivors_black"] / 1).mean() * 100),
        }
        mean_survivors = {
            "WHITE": float(df["survivors_white"].mean()),
            "BLUE": float(df["survivors_blue"].mean()),
            "RED": float(df["survivors_red"].mean()),
            "BLACK": float(df["survivors_black"].mean()),
        }

        # 2. Expected Prize per Capita (KRW)
        prize_per_capita = {
            "WHITE": {
                "mean": float(df["prize_per_capita_white"].mean()),
                "std": float(df["prize_per_capita_white"].std()),
                "median": float(df["prize_per_capita_white"].median()),
            },
            "BLUE": {
                "mean": float(df["prize_per_capita_blue"].mean()),
                "std": float(df["prize_per_capita_blue"].std()),
                "median": float(df["prize_per_capita_blue"].median()),
            },
            "RED": {
                "mean": float(df["prize_per_capita_red"].mean()),
                "std": float(df["prize_per_capita_red"].std()),
                "median": float(df["prize_per_capita_red"].median()),
            },
            "BLACK": {
                "mean": float(df["prize_per_capita_black"].mean()),
                "std": float(df["prize_per_capita_black"].std()),
                "median": float(df["prize_per_capita_black"].median()),
            },
        }

        # 3. War Occurrence Rate
        sessions_with_war = float((df["war_attacks_count"] > 0).mean() * 100)
        mean_attacks = float(df["war_attacks_count"].mean())

        # 4. Pollution Disaster Occurrence Rate
        disaster_rate = float(df["disaster_occurred"].mean() * 100)
        mean_pollution = float(df["pollution_final"].mean())

        # 5. Black Confiscation Rate
        confiscation_rate = float(df["black_confiscated"].mean() * 100)

        # 6. Economic & Malthusian Indicators
        mean_remaining_life_reserve = float(df["remaining_life_reserve"].mean())
        mean_jewel_unit_val = float(df["final_jewel_unit_value"].mean())

        self.summary_stats = {
            "total_runs": n,
            "elapsed_time_sec": self.results.elapsed_time,
            "survival_rates_pct": survival_rates,
            "mean_survivors": mean_survivors,
            "prize_per_capita_krw": prize_per_capita,
            "war_occurrence_rate_pct": sessions_with_war,
            "mean_attacks_per_session": mean_attacks,
            "pollution_disaster_rate_pct": disaster_rate,
            "mean_final_pollution_index": mean_pollution,
            "black_confiscation_rate_pct": confiscation_rate,
            "mean_remaining_life_reserve": mean_remaining_life_reserve,
            "mean_final_jewel_unit_value": mean_jewel_val if (mean_jewel_val := mean_jewel_unit_val) else 0.0,
        }

        return self.summary_stats

    def export_report(self) -> str:
        """Saves JSON & Markdown reports to output_dir and returns markdown string."""
        if not self.summary_stats:
            self.compute_metrics()

        json_path = os.path.join(self.output_dir, "metrics_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.summary_stats, f, indent=4, ensure_ascii=False)

        md_path = os.path.join(self.output_dir, "simulation_report.md")
        md_content = self._generate_markdown_report()
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return md_content

    def _generate_markdown_report(self) -> str:
        stats = self.summary_stats
        md = f"""# 더 커뮤니티 2: 보이지 않는 손 - 몬테카를로 시뮬레이션 분석 보고서

- **총 시뮬레이션 횟수**: {stats['total_runs']:,} 회
- **소요 시간**: {stats['elapsed_time_sec']:.2f} 초

---

## 1. 핵심 지표 요약

| 팀 | 초기 인원 | 평균 생존 인원 | 최종 생존율 (%) | 1인당 평균 기대 상금 (원) |
|:---:|:---:|:---:|:---:|:---:|
| **화이트 (White)** | 6 | {stats['mean_survivors']['WHITE']:.2f} | {stats['survival_rates_pct']['WHITE']:.1f}% | {stats['prize_per_capita_krw']['WHITE']['mean']:,.0f} 원 |
| **블루 (Blue)** | 3 | {stats['mean_survivors']['BLUE']:.2f} | {stats['survival_rates_pct']['BLUE']:.1f}% | {stats['prize_per_capita_krw']['BLUE']['mean']:,.0f} 원 |
| **레드 (Red)** | 3 | {stats['mean_survivors']['RED']:.2f} | {stats['survival_rates_pct']['RED']:.1f}% | {stats['prize_per_capita_krw']['RED']['mean']:,.0f} 원 |
| **블랙 (Black)** | 1 | {stats['mean_survivors']['BLACK']:.2f} | {stats['survival_rates_pct']['BLACK']:.1f}% | {stats['prize_per_capita_krw']['BLACK']['mean']:,.0f} 원 |

---

## 2. 전쟁 및 시스템 재앙 분석

- **전쟁 발발률 (War Occurrence Rate)**: `{stats['war_occurrence_rate_pct']:.2f}%` (세션당 평균 공격 횟수: `{stats['mean_attacks_per_session']:.2f}` 회)
- **공해 재앙 발생률 (Pollution Disaster Rate)**: `{stats['pollution_disaster_rate_pct']:.2f}%` (평균 최종 공해 수치: `{stats['mean_final_pollution_index']:.1f}`)
- **블랙 자산 몰수율 (Confiscation Rate)**: `{stats['black_confiscation_rate_pct']:.2f}%` (3개 환수 조각 완성 빈도)
- **잔여 라이프 생산 가능량**: 평균 `{stats['mean_remaining_life_reserve']:.1f}` 개 (초기 50개 한도)
- **최종 보석 1개당 평균 가치**: `{stats['mean_final_jewel_unit_value']:,.0f}` 원 (총 상금 2억 원 환산)

---
"""
        return md

    def generate_plots(self):
        """Generate publication-quality Seaborn/Matplotlib charts."""
        df = self.results.summary_df
        daily_df = self.results.daily_survival_df

        palette = {
            "WHITE": "#95a5a6",
            "BLUE": "#2980b9",
            "RED": "#c0392b",
            "BLACK": "#2c3e50",
        }

        # 1. Survival Trends by Day
        plt.figure(figsize=(9, 5), dpi=150)
        sns.lineplot(
            data=daily_df,
            x="day",
            y="survivors",
            hue="team",
            palette=palette,
            marker="o",
            errorbar=("ci", 95),
        )
        plt.title("더 커뮤니티 2: 일자별 팀 생존 인원 추이 (95% CI)", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Day (1일 ~ 9일)", fontsize=12)
        plt.ylabel("생존 인원 (Survivors)", fontsize=12)
        plt.xticks(range(1, 10))
        plt.legend(title="팀 (Team)", frameon=True)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "survival_trend.png"))
        plt.close()

        # 2. Prize Distribution per Capita
        prize_df = pd.DataFrame({
            "Team": (
                ["White"] * len(df)
                + ["Blue"] * len(df)
                + ["Red"] * len(df)
                + ["Black"] * len(df)
            ),
            "Prize_Million": np.concatenate([
                df["prize_per_capita_white"].values / 1e6,
                df["prize_per_capita_blue"].values / 1e6,
                df["prize_per_capita_red"].values / 1e6,
                df["prize_per_capita_black"].values / 1e6,
            ]),
        })

        plt.figure(figsize=(9, 5), dpi=150)
        box_colors = ["#bdc3c7", "#3498db", "#e74c3c", "#34495e"]
        sns.boxplot(
            data=prize_df,
            x="Team",
            y="Prize_Million",
            hue="Team",
            palette=box_colors,
            legend=False,
            showmeans=True,
            meanprops={"marker": "o", "markerfacecolor": "white", "markeredgecolor": "black"},
        )
        plt.title("팀별 1인당 기대 상금 분포 (백만 원)", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("팀 (Team)", fontsize=12)
        plt.ylabel("1인당 기대 상금 (백만 원 KRW)", fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "prize_distribution.png"))
        plt.close()

        # 3. War & Disaster Frequency
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), dpi=150)
        
        # Disaster rate pie
        disaster_counts = df["disaster_occurred"].value_counts(normalize=True) * 100
        labels = ["정상 (Safe)", "재앙 발생 (Disaster)"]
        pie_vals = [
            disaster_counts.get(False, 0.0),
            disaster_counts.get(True, 0.0),
        ]
        axes[0].pie(
            pie_vals,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=["#2ecc71", "#e67e22"],
            explode=(0, 0.08) if pie_vals[1] > 0 else None,
        )
        axes[0].set_title("공해 재앙 발생률 (Pollution Disaster)", fontsize=12, fontweight="bold")

        # War attacks histogram
        sns.histplot(
            df["war_attacks_count"],
            discrete=True,
            ax=axes[1],
            color="#c0392b",
            kde=False,
        )
        axes[1].set_title("세션당 전쟁/폭탄 공격 횟수 분포", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("공격 발생 횟수 (Attacks)")
        axes[1].set_ylabel("세션 빈도 (Sessions)")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "disaster_and_war.png"))
        plt.close()

        # 4. Final Jewel Unit Value & Inflation
        plt.figure(figsize=(8, 4.5), dpi=150)
        sns.histplot(
            df["final_jewel_unit_value"] / 1000,
            kde=True,
            color="#9b59b6",
            bins=30,
        )
        plt.title("최종 보석 단위 가치 분포 (천 원 단위)", fontsize=13, fontweight="bold", pad=12)
        plt.xlabel("보석 1개당 가치 (천 원)", fontsize=11)
        plt.ylabel("빈도 (Frequency)", fontsize=11)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "jewel_value_distribution.png"))
        plt.close()

        # 5. Malthusian Trap & Monetary Dynamics over 9 Days
        macro_df = self.results.daily_macro_df
        if not macro_df.empty:
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=150)

            # Left: Life Reserve Depletion
            sns.lineplot(
                data=macro_df,
                x="day",
                y="life_reserve",
                ax=axes[0],
                color="#e74c3c",
                marker="s",
                errorbar=("ci", 95),
            )
            axes[0].set_title("멜서스 트랩: 잔여 라이프 비축량 고갈 추이 (Life Reserve)", fontsize=12, fontweight="bold")
            axes[0].set_xlabel("Day (1일 ~ 9일)")
            axes[0].set_ylabel("잔여 라이프 생산 한도 (개)")
            axes[0].set_xticks(range(1, 10))
            axes[0].axhline(0, color="gray", linestyle="--", alpha=0.6)

            # Right: Jewel Unit Value
            sns.lineplot(
                data=macro_df,
                x="day",
                y=macro_df["jewel_unit_value"] / 1000,
                ax=axes[1],
                color="#2980b9",
                marker="o",
                errorbar=("ci", 95),
            )
            axes[1].set_title("화폐 가치 동학: 보석 단위 가치 추이 (Jewel Value)", fontsize=12, fontweight="bold")
            axes[1].set_xlabel("Day (1일 ~ 9일)")
            axes[1].set_ylabel("보석 단위 가치 (천 원)")
            axes[1].set_xticks(range(1, 10))

            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "malthusian_dynamics.png"))
            plt.close()
