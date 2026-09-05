"""
models/market.py
Market trading mechanics: order matching, bilateral trades, and transaction settlement.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from models.resources import ResourceBundle


@dataclass
class TradeOffer:
    offer_id: str
    sender: str
    receiver: str  # specific team name or "ALL"
    offering: ResourceBundle
    requesting: ResourceBundle
    accepted: bool = False
    rejected: bool = False


@dataclass
class TradeRecord:
    day: int
    sender: str
    receiver: str
    given: ResourceBundle
    received: ResourceBundle
    success: bool
    note: str = ""


class MarketEngine:
    def __init__(self):
        self.history: List[TradeRecord] = []
        self._offer_counter: int = 0

    def create_offer(
        self,
        sender: str,
        receiver: str,
        offering: ResourceBundle,
        requesting: ResourceBundle,
    ) -> TradeOffer:
        self._offer_counter += 1
        return TradeOffer(
            offer_id=f"offer_{self._offer_counter}",
            sender=sender,
            receiver=receiver,
            offering=offering,
            requesting=requesting,
        )

    def execute_trade(
        self,
        day: int,
        offer: TradeOffer,
        sender_res: ResourceBundle,
        receiver_res: ResourceBundle,
    ) -> bool:
        """Executes a trade if both parties have sufficient resources."""
        if not sender_res.can_afford(offer.offering):
            self.history.append(
                TradeRecord(
                    day=day,
                    sender=offer.sender,
                    receiver=offer.receiver,
                    given=offer.offering,
                    received=offer.requesting,
                    success=False,
                    note=f"Sender {offer.sender} lacked resources.",
                )
            )
            return False

        if not receiver_res.can_afford(offer.requesting):
            self.history.append(
                TradeRecord(
                    day=day,
                    sender=offer.sender,
                    receiver=offer.receiver,
                    given=offer.offering,
                    received=offer.requesting,
                    success=False,
                    note=f"Receiver {offer.receiver} lacked resources.",
                )
            )
            return False

        # Apply transaction
        # Sender gives offering, gains requesting
        new_sender = sender_res.subtract(offer.offering).add(offer.requesting)
        # Receiver gives requesting, gains offering
        new_receiver = receiver_res.subtract(offer.requesting).add(offer.offering)

        sender_res.jewels, sender_res.life, sender_res.credits = (
            new_sender.jewels,
            new_sender.life,
            new_sender.credits,
        )
        receiver_res.jewels, receiver_res.life, receiver_res.credits = (
            new_receiver.jewels,
            new_receiver.life,
            new_receiver.credits,
        )

        offer.accepted = True
        self.history.append(
            TradeRecord(
                day=day,
                sender=offer.sender,
                receiver=offer.receiver,
                given=offer.offering,
                received=offer.requesting,
                success=True,
                note="Trade executed successfully.",
            )
        )
        return True
