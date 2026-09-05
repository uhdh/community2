"""
models/tech.py
Technology progression and production enhancements for teams.
"""

from dataclasses import dataclass


@dataclass
class TechTree:
    level: int = 1
    max_level: int = 3

    @property
    def upgrade_cost(self) -> int:
        """Cost in credits to upgrade to next level."""
        if self.level == 1:
            return 6
        elif self.level == 2:
            return 12
        return 999999  # Max level reached

    def can_upgrade(self, available_credits: float) -> bool:
        return self.level < self.max_level and available_credits >= self.upgrade_cost

    def upgrade(self) -> bool:
        if self.level < self.max_level:
            self.level += 1
            return True
        return False

    def get_production_multiplier(self) -> float:
        """Multiplier based on technology level."""
        if self.level == 1:
            return 1.0
        elif self.level == 2:
            return 1.3
        else:
            return 1.6

    def get_blue_credit_per_life(self) -> float:
        """Credits required by Blue to produce 1 life unit."""
        if self.level == 1:
            return 2.0
        elif self.level == 2:
            return 1.5
        else:
            return 1.0

    def copy(self) -> "TechTree":
        return TechTree(level=self.level, max_level=self.max_level)
