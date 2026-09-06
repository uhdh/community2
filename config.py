"""
config.py
Global configuration and hyperparameters for 'The Community 2: Invisible Hand'
Monte Carlo simulation. Aligned with the official comprehensive rulebook.
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
    GROUP_LAST_SURVIVOR_PROTECTED: bool = True  # Exception: Group's last 1 survivor never eliminated even at 0 life
    
    # Pollution & Disaster
    POLLUTION_DISASTER_THRESHOLD: float = 50.0  # Threshold > 50 triggers disaster
    DISASTER_PENALTY_RATIO: float = 0.30        # 30% of all assets destroyed upon disaster
    RED_CLEAN_CREDIT_YIELD: int = 6             # Clean credit production (타공 무공해)
    RED_POLLUTING_CREDIT_YIELD: int = 12        # Polluting credit production (일반 공해)
    RED_POLLUTION_INCREMENT: float = 8.0        # Pollution added per polluting production
    
    # War & Arms (Confirmed Day 2 Black Mart pricing)
    WAR_DECLARATION_JEWEL_COST: int = 15        # War declaration fee in jewels
    WEAPON_TIER_A_JEWEL_PRICE: int = 30         # Tier A weapon (Heavy fire, deals 4 life damage)
    WEAPON_TIER_B_JEWEL_PRICE: int = 20         # Tier B weapon (Medium fire, deals 2 life damage)
    WEAPON_TIER_C_JEWEL_PRICE: int = 10         # Tier C weapon (Light fire, deals 1 life damage)
    WAR_LOOT_PERCENTAGE: float = 0.50           # Victory loots 50% of losing team's all assets
    
    # Special Quiz Tech (고유 특수 기술)
    RED_BOMB_CREDIT_COST: int = 10              # Red bomb crafting credit cost
    RED_BOMB_LIFE_DAMAGE: int = 3               # Red bomb deals 3 life damage to target team
    QUIZ_PIECES_NEEDED: int = 3                 # 3 quiz pieces collectable to seize Black's weapon profits
    
    # Initial Team Setup (Confirmed Day 1 starting assets)
    # Format: (initial_members, jewels, life, credits)
    WHITE_MEMBERS: int = 6
    WHITE_JEWELS: int = 90                      # Day 1 confirmed: 90 jewels (daily mint cap: 200)
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
    BLUE_MAX_DAILY_LIFE_PRODUCE: int = 10       # Blue can produce max 10 life per day
    WHITE_JEWEL_MINT_MAX: int = 200             # Maximum jewels White can mint in one day (standard cap)
    
    # Monte Carlo Defaults
    DEFAULT_MC_RUNS: int = 1000
    LOG_LEVEL: str = "INFO"


# Default global instance
DEFAULT_CONFIG = SimulationConfig()
