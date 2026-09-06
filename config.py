"""
config.py
Global configuration and hyperparameters for 'The Community 2: Invisible Hand'
Monte Carlo simulation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    # Game duration & Prize
    TOTAL_DAYS: int = 9
    TOTAL_PRIZE_POOL: float = 200_000_000.0  # 200 Million KRW
    
    # Life & Malthusian Trap
    INITIAL_LIFE_RESERVE: int = 50  # Global hard cap for producible life (only known to Blue)
    DAILY_LIFE_REQUIREMENT: int = 1  # 1 Life per surviving member per day
    BLACK_MART_DAILY_LIFE_COST: int = 1  # Mart operating cost per day for Black
    BLACK_MART_DAY1_LIFE_EXEMPT: bool = True  # Day 1 exemption: Mart operates with 0 life cost on Day 1
    
    # Pollution & Disaster
    POLLUTION_DISASTER_THRESHOLD: float = 50.0  # Threshold > 50 triggers disaster
    DISASTER_PENALTY_RATIO: float = 0.30        # 30% of all assets destroyed upon disaster
    RED_CLEAN_CREDIT_YIELD: int = 6             # Clean credit production
    RED_POLLUTING_CREDIT_YIELD: int = 12        # Polluting credit production
    RED_POLLUTION_INCREMENT: float = 8.0        # Pollution added per polluting production
    
    # War & Arms (Confirmed Day 2 Black Mart pricing)
    WAR_DECLARATION_JEWEL_COST: int = 15        # War declaration fee in jewels
    WEAPON_TIER_A_JEWEL_PRICE: int = 30         # Tier A weapon (Heavy fire)
    WEAPON_TIER_B_JEWEL_PRICE: int = 20         # Tier B weapon (Medium fire)
    WEAPON_TIER_C_JEWEL_PRICE: int = 10         # Tier C weapon (Light fire)
    BOMB_CREDIT_COST: int = 10                  # Red team bomb crafting cost
    BOMB_LIFE_DAMAGE: int = 3                   # Damage dealt to target team's life
    SHIELD_CREDIT_PRICE: int = 8                # Black mart shield price in credits
    SHIELD_JEWEL_PRICE: int = 25                # Black mart shield price in jewels
    SABOTAGE_CREDIT_PRICE: int = 12             # Black mart sabotage price in credits
    SABOTAGE_CREDIT_DAMAGE: int = 15            # Sabotage drains credits from target
    
    # Black Reclaim Pieces (환수 조각)
    RECLAIM_PIECES_NEEDED: int = 3              # 3 pieces needed to confiscate Black's assets
    RECLAIM_SEARCH_CREDIT_COST: int = 6         # Cost to search for a reclaim piece
    RECLAIM_SEARCH_SUCCESS_PROB: float = 0.35   # Probability of finding a piece per search
    
    # Initial Team Setup
    # Format: (initial_members, jewels, life, credits)
    WHITE_MEMBERS: int = 6
    WHITE_JEWELS: int = 200
    WHITE_LIFE: int = 14
    WHITE_CREDITS: int = 7
    
    BLUE_MEMBERS: int = 3
    BLUE_JEWELS: int = 60
    BLUE_LIFE: int = 19
    BLUE_CREDITS: int = 8
    
    RED_MEMBERS: int = 3
    RED_JEWELS: int = 50
    RED_LIFE: int = 9
    RED_CREDITS: int = 18
    
    BLACK_MEMBERS: int = 1
    BLACK_JEWELS: int = 0
    BLACK_LIFE: int = 0
    BLACK_CREDITS: int = 0
    
    # Production Rates
    BLUE_CREDIT_PER_LIFE: int = 2               # Base credits required by Blue to produce 1 life
    WHITE_JEWEL_MINT_MAX: int = 100             # Maximum jewels White can mint in one day
    
    # Monte Carlo Defaults
    DEFAULT_MC_RUNS: int = 1000
    LOG_LEVEL: str = "INFO"


# Default global instance
DEFAULT_CONFIG = SimulationConfig()
