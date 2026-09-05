"""
models/war.py
War and weapons system: Bombs, Arms Dealer items, Shields, and Attacks.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class WeaponType(Enum):
    RED_BOMB = "RED_BOMB"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    INTEL_LEAK = "INTEL_LEAK"


@dataclass
class AttackAction:
    attacker: str
    target: str
    weapon_type: WeaponType
    credit_spent: float
    description: str = ""


@dataclass
class AttackResult:
    action: AttackAction
    blocked_by_shield: bool
    life_damage_dealt: int
    credits_drained: float
    message: str


@dataclass
class BlackMarketItem:
    item_type: WeaponType
    name: str
    credit_price: float
    jewel_price: float
    description: str


def get_default_black_catalog() -> List[BlackMarketItem]:
    """Catalog of weapons and defenses provided by Black."""
    return [
        BlackMarketItem(
            item_type=WeaponType.SHIELD,
            name="방어 쉴드 (Bomb Shield)",
            credit_price=8.0,
            jewel_price=25.0,
            description="폭탄 공격을 1회 완벽하게 방어하고 소멸합니다.",
        ),
        BlackMarketItem(
            item_type=WeaponType.SABOTAGE,
            name="사보타주 공작권 (Sabotage)",
            credit_price=12.0,
            jewel_price=35.0,
            description="목표 팀의 크레딧 15를 강제로 소각/강탈합니다.",
        ),
        BlackMarketItem(
            item_type=WeaponType.INTEL_LEAK,
            name="기밀 도청 정보 (Wiretap Intel)",
            credit_price=5.0,
            jewel_price=15.0,
            description="타 팀의 정확한 라이프 잔여량 및 거래 계획을 파악합니다.",
        ),
    ]
