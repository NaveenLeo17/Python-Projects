"""Transaction record with timestamp."""
import secrets
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

DEPOSIT = "DEPOSIT"
WITHDRAWAL = "WITHDRAWAL"
TRANSFER_IN = "TRANSFER_IN"
TRANSFER_OUT = "TRANSFER_OUT"
INTEREST = "INTEREST"

CREDIT_TYPES = {DEPOSIT, TRANSFER_IN, INTEREST}
DEBIT_TYPES = {WITHDRAWAL, TRANSFER_OUT}


@dataclass
class Transaction:
    txn_id: str
    timestamp: str  # ISO 8601, e.g. 2026-09-30T14:05:09
    txn_type: str
    amount: Decimal
    balance_after: Decimal
    description: str = ""

    @classmethod
    def create(cls, txn_type, amount, balance_after, description="", now=None):
        now = now or datetime.now()
        return cls(
            txn_id=secrets.token_hex(4).upper(),
            timestamp=now.isoformat(timespec="seconds"),
            txn_type=txn_type,
            amount=amount,
            balance_after=balance_after,
            description=description,
        )

    @property
    def datetime(self):
        return datetime.fromisoformat(self.timestamp)

    @property
    def is_credit(self):
        return self.txn_type in CREDIT_TYPES

    @property
    def signed_amount(self):
        return self.amount if self.is_credit else -self.amount

    def to_dict(self):
        return {
            "txn_id": self.txn_id,
            "timestamp": self.timestamp,
            "txn_type": self.txn_type,
            "amount": str(self.amount),
            "balance_after": str(self.balance_after),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            txn_id=d["txn_id"],
            timestamp=d["timestamp"],
            txn_type=d["txn_type"],
            amount=Decimal(d["amount"]),
            balance_after=Decimal(d["balance_after"]),
            description=d.get("description", ""),
        )
