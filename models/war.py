"""
models/war.py
War and weapons system: War Declaration and Tiered Weapons (A/B/C) sold by Black Mart.
Reflects confirmed broadcast rules as of 2026-09-06.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class WeaponType(Enum):
    WAR_DECLARATION = "WAR_DECLARATION"
    WEAPON_TIER_A = "WEAPON_TIER_A"
    WEAPON_TIER_B = "WEAPON_TIER_B"
    WEAPON_TIER_C = "WEAPON_TIER_C"


@dataclass
class AttackAction:
    attacker: str
    target: str
    weapon_type: WeaponType
    jewels_spent: float
    description: str = ""


@dataclass
class AttackResult:
    action: AttackAction
    life_damage_dealt: int
    message: str


@dataclass
class BlackMarketItem:
    item_type: WeaponType
    name: str
    credit_price: float
    jewel_price: float
    life_damage: int
    description: str


def get_default_black_catalog() -> List[BlackMarketItem]:
    """Catalog of weapons and war services provided by Black Mart (2026.09.06 confirmed pricing)."""
    return [
        BlackMarketItem(
            item_type=WeaponType.WAR_DECLARATION,
            name="전쟁 선포권 (War Declaration)",
            credit_price=0.0,
            jewel_price=15.0,
            life_damage=0,
            description="공식 전쟁을 선포하고 무기 공격 권한을 활성화합니다.",
        ),
        BlackMarketItem(
            item_type=WeaponType.WEAPON_TIER_A,
            name="A급 무기 (Heavy Weapon)",
            credit_price=0.0,
            jewel_price=30.0,
            life_damage=4,
            description="상대 진영의 라이프 4개를 즉시 파괴하는 최고 등급 중화기.",
        ),
        BlackMarketItem(
            item_type=WeaponType.WEAPON_TIER_B,
            name="B급 무기 (Medium Weapon)",
            credit_price=0.0,
            jewel_price=20.0,
            life_damage=2,
            description="상대 진영의 라이프 2개를 즉시 파괴하는 표준 전투 화기.",
        ),
        BlackMarketItem(
            item_type=WeaponType.WEAPON_TIER_C,
            name="C급 무기 (Light Weapon)",
            credit_price=0.0,
            jewel_price=10.0,
            life_damage=1,
            description="상대 진영의 라이프 1개를 즉시 파괴하는 경량 화기.",
        ),
    ]
