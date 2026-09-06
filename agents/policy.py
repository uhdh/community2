"""
agents/policy.py
Base policy interface for autonomous agents in 'The Community 2'.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from simulation.engine import GlobalState
    from models.team import TeamState
    from models.market import TradeOffer
    from models.war import AttackAction, BlackMarketItem


class BasePolicy(ABC):
    """Abstract base class defining the decision-making interface for all teams."""

    def __init__(self, team_type_str: str):
        self.team_type_str = team_type_str

    @abstractmethod
    def decide_morning_production(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> Dict[str, Any]:
        """
        Decide morning production parameters.
        Returns a dict containing production specifications.
        """
        pass

    @abstractmethod
    def decide_tech_upgrade(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> bool:
        """Decide whether to invest credits in upgrading technology."""
        pass

    @abstractmethod
    def generate_trade_offers(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List["TradeOffer"]:
        """Generate outgoing trade offers for Phase 2 market trading."""
        pass

    @abstractmethod
    def evaluate_trade_offer(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        offer: "TradeOffer",
    ) -> bool:
        """Evaluate an incoming trade offer. Return True to accept, False to reject."""
        pass

    @abstractmethod
    def decide_war_actions(
        self, global_state: "GlobalState", my_state: "TeamState"
    ) -> List["AttackAction"]:
        """Decide military actions (e.g., weapon purchase and strike via Black Mart)."""
        pass

    @abstractmethod
    def decide_black_purchases(
        self,
        global_state: "GlobalState",
        my_state: "TeamState",
        catalog: List["BlackMarketItem"],
    ) -> List[str]:
        """Decide which items to purchase from Black's arms catalog."""
        pass
