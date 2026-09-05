"""
models/resources.py
Data structures and operations for game resources:
Jewels, Life, Credits, and Reclaim Pieces.
"""

from dataclasses import dataclass
import math


@dataclass
class ResourceBundle:
    jewels: float = 0.0
    life: int = 0
    credits: float = 0.0
    reclaim_pieces: int = 0

    def can_afford(self, other: "ResourceBundle") -> bool:
        """Check if current resources can cover other required resources."""
        return (
            self.jewels >= other.jewels
            and self.life >= other.life
            and self.credits >= other.credits
            and self.reclaim_pieces >= other.reclaim_pieces
        )

    def add(self, other: "ResourceBundle") -> "ResourceBundle":
        """Add resources and return a new ResourceBundle."""
        return ResourceBundle(
            jewels=max(0.0, self.jewels + other.jewels),
            life=max(0, self.life + other.life),
            credits=max(0.0, self.credits + other.credits),
            reclaim_pieces=max(0, self.reclaim_pieces + other.reclaim_pieces),
        )

    def subtract(self, other: "ResourceBundle") -> "ResourceBundle":
        """Subtract resources and return a new ResourceBundle (floor at 0)."""
        return ResourceBundle(
            jewels=max(0.0, self.jewels - other.jewels),
            life=max(0, self.life - other.life),
            credits=max(0.0, self.credits - other.credits),
            reclaim_pieces=max(0, self.reclaim_pieces - other.reclaim_pieces),
        )

    def apply_disaster(self, penalty_ratio: float = 0.30) -> "ResourceBundle":
        """Apply pollution disaster: reduce 30% of all goods."""
        remaining_factor = 1.0 - penalty_ratio
        return ResourceBundle(
            jewels=math.floor(self.jewels * remaining_factor * 10) / 10.0,
            life=math.floor(self.life * remaining_factor),
            credits=math.floor(self.credits * remaining_factor * 10) / 10.0,
            reclaim_pieces=self.reclaim_pieces,  # Pieces are physical clues, not liquid goods
        )

    def copy(self) -> "ResourceBundle":
        return ResourceBundle(
            jewels=self.jewels,
            life=self.life,
            credits=self.credits,
            reclaim_pieces=self.reclaim_pieces,
        )

    def __repr__(self) -> str:
        return f"ResourceBundle(Jewels:{self.jewels:.1f}, Life:{self.life}, Credits:{self.credits:.1f}, Pieces:{self.reclaim_pieces})"
