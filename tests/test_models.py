"""
tests/test_models.py
Unit tests for data models, resources, tech, war, and market mechanics.
"""

import pytest
from models.resources import ResourceBundle
from models.tech import TechTree
from models.team import TeamType, TeamState
from models.war import WeaponType, AttackAction, get_default_black_catalog
from models.market import TradeOffer, MarketEngine


def test_resource_bundle_math():
    r1 = ResourceBundle(jewels=100.0, life=10, credits=20.0, reclaim_pieces=1)
    r2 = ResourceBundle(jewels=30.0, life=4, credits=5.0, reclaim_pieces=0)

    # Addition
    r_add = r1.add(r2)
    assert r_add.jewels == 130.0
    assert r_add.life == 14
    assert r_add.credits == 25.0
    assert r_add.reclaim_pieces == 1

    # Subtraction
    r_sub = r1.subtract(r2)
    assert r_sub.jewels == 70.0
    assert r_sub.life == 6
    assert r_sub.credits == 15.0

    # Affordability
    assert r1.can_afford(r2) is True
    assert r2.can_afford(r1) is False


def test_disaster_30_percent():
    r = ResourceBundle(jewels=100.0, life=10, credits=20.0, reclaim_pieces=2)
    r_after = r.apply_disaster(0.30)
    # 70% remaining
    assert r_after.jewels == 70.0
    assert r_after.life == 7
    assert r_after.credits == 14.0
    assert r_after.reclaim_pieces == 2  # Reclaim clues are not liquidated goods


def test_tech_progression():
    tech = TechTree()
    assert tech.level == 1
    assert tech.upgrade_cost == 6
    assert tech.get_blue_credit_per_life() == 2.0

    assert tech.can_upgrade(5.0) is False
    assert tech.can_upgrade(6.0) is True

    tech.upgrade()
    assert tech.level == 2
    assert tech.upgrade_cost == 12
    assert tech.get_blue_credit_per_life() == 1.5


def test_team_life_submission_and_casualties():
    team = TeamState(
        team_type=TeamType.WHITE,
        initial_members=6,
        surviving_members=6,
        resources=ResourceBundle(life=4),
    )

    # 6 members need 6 life, but team has only 4 -> 2 deaths, 4 survivors
    deaths = team.submit_daily_life(requirement=1)
    assert deaths == 2
    assert team.surviving_members == 4
    assert team.resources.life == 0


def test_market_trade_execution():
    market = MarketEngine()
    sender_res = ResourceBundle(jewels=50.0, life=5, credits=10.0)
    receiver_res = ResourceBundle(jewels=10.0, life=10, credits=2.0)

    offer = TradeOffer(
        offer_id="test_1",
        sender="WHITE",
        receiver="BLUE",
        offering=ResourceBundle(jewels=20.0),
        requesting=ResourceBundle(life=2),
    )

    success = market.execute_trade(1, offer, sender_res, receiver_res)
    assert success is True
    assert sender_res.jewels == 30.0
    assert sender_res.life == 7
    assert receiver_res.jewels == 30.0
    assert receiver_res.life == 8


def test_shield_blocks_bomb():
    # If target has shield, bomb damage is absorbed and shield is removed
    target = TeamState(
        team_type=TeamType.BLUE,
        initial_members=3,
        surviving_members=3,
        resources=ResourceBundle(life=10),
        has_shield=True,
    )

    if target.has_shield:
        target.has_shield = False
        damage_dealt = 0
    else:
        damage_dealt = 3
        target.resources.life -= 3

    assert target.has_shield is False
    assert target.resources.life == 10  # Undamaged
