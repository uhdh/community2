"""
models/team.py
Team state and attributes definition.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from models.resources import ResourceBundle
from models.tech import TechTree


class TeamType(Enum):
    WHITE = "WHITE"
    BLUE = "BLUE"
    RED = "RED"
    BLACK = "BLACK"


@dataclass
class TeamState:
    team_type: TeamType
    initial_members: int
    surviving_members: int
    resources: ResourceBundle
    tech: TechTree = field(default_factory=TechTree)
    has_shield: bool = False
    is_confiscated: bool = False  # For Black
    search_attempts: int = 0      # Reclaim search count

    @property
    def is_alive(self) -> bool:
        if self.team_type == TeamType.BLACK:
            return not self.is_confiscated
        return self.surviving_members > 0

    def submit_daily_life(self, requirement: int = 1) -> int:
        """
        Consumes daily life for each surviving member.
        Returns the number of deaths this turn.
        """
        if self.team_type == TeamType.BLACK:
            # Black does not die from lack of life directly,
            # but mart operating costs 1 life if available.
            if self.resources.life >= 1:
                self.resources.life -= 1
            return 0

        needed = self.surviving_members * requirement
        if self.resources.life >= needed:
            self.resources.life -= needed
            return 0
        else:
            # Insufficient life: survivors equal to available life
            can_survive = self.resources.life // requirement
            deaths = self.surviving_members - can_survive
            self.resources.life = 0
            self.surviving_members = can_survive
            return deaths

    def calculate_prize(self, jewel_unit_value: float) -> float:
        """Calculates total team prize money based on jewel value."""
        if not self.is_alive or self.is_confiscated:
            return 0.0
        return self.resources.jewels * jewel_unit_value

    def per_capita_prize(self, jewel_unit_value: float) -> float:
        """Prize money per initial team member."""
        if self.initial_members <= 0:
            return 0.0
        return self.calculate_prize(jewel_unit_value) / self.initial_members

    def copy(self) -> "TeamState":
        return TeamState(
            team_type=self.team_type,
            initial_members=self.initial_members,
            surviving_members=self.surviving_members,
            resources=self.resources.copy(),
            tech=self.tech.copy(),
            has_shield=self.has_shield,
            is_confiscated=self.is_confiscated,
            search_attempts=self.search_attempts,
        )
