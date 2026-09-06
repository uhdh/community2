"""
models/team.py
Team state and attributes definition for 'The Community 2: Invisible Hand'.
Includes the official exception rule: Group's last survivor is protected even at 0 life.
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

    @property
    def is_alive(self) -> bool:
        if self.team_type == TeamType.BLACK:
            return True
        return self.surviving_members > 0

    def submit_daily_life(self, requirement: int = 1) -> int:
        """
        Consumes daily life for each surviving member.
        Returns the number of deaths this turn.
        공식 룰북 예외 규정: 그룹별 최후의 1인이 남을 경우 라이프가 0이 되어도 탈락하지 않음.
        """
        if self.team_type == TeamType.BLACK:
            # Black mart operating costs 1 life if available (exempt on Day 1 handled in engine)
            if self.resources.life >= 1:
                self.resources.life -= 1
            return 0

        needed = self.surviving_members * requirement
        if self.resources.life >= needed:
            self.resources.life -= needed
            return 0
        else:
            # Insufficient life:
            can_survive = self.resources.life // requirement
            # 예외 규정: 그룹별 최후의 1인이 남을 경우 라이프가 0이 되어도 탈락하지 않음
            if self.surviving_members > 0:
                can_survive = max(1, can_survive)
            deaths = max(0, self.surviving_members - can_survive)
            self.resources.life = 0
            self.surviving_members = can_survive
            return deaths

    def calculate_prize(self, jewel_unit_value: float) -> float:
        """Calculates total team prize money based on jewel value."""
        if not self.is_alive:
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
        )
