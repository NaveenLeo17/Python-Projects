"""Account classes: Savings, Current and Fixed Deposit."""
from datetime import datetime, timedelta
from decimal import Decimal

from .exceptions import (InsufficientFundsError, TransactionNotAllowedError,
                         ValidationError)
from .money import ZERO, fmt, parse_amount, round_money
from .security import hash_pin, validate_pin_format, verify_pin
from .transactions import (DEPOSIT, INTEREST, TRANSFER_OUT, WITHDRAWAL,
                           Transaction)


class Account:
    ACCOUNT_TYPE = "account"
    DISPLAY_NAME = "Account"
    DESCRIPTION = ""
    INTEREST_RATE = Decimal("0")       # annual rate, e.g. 0.04 = 4%
    MIN_OPENING_DEPOSIT = ZERO

    def __init__(self, account_number, holder_name, pin_salt, pin_hash,
                 balance=ZERO, transactions=None, created_at=None,
                 failed_attempts=0, locked_until=None):
        self.account_number = account_number
        self.holder_name = holder_name
        self.pin_salt = pin_salt
        self.pin_hash = pin_hash
        self.balance = balance
        self.transactions = transactions if transactions is not None else []
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")
        self.failed_attempts = failed_attempts
        self.locked_until = locked_until  # ISO string or None

    # ---- rules subclasses can override --------------------------------
    def min_balance(self):
        return ZERO

    def available_balance(self):
        return self.balance - self.min_balance()

    def check_can_deposit(self):
        """Raise if a deposit is not allowed right now."""

    def check_can_withdraw(self, amount, now=None):
        if amount > self.available_balance():
            raise InsufficientFundsError(
                f"Insufficient funds. Available: {fmt(max(self.available_balance(), ZERO))}")

    # ---- PIN ----------------------------------------------------------
    def verify_pin(self, pin):
        return verify_pin(pin, self.pin_salt, self.pin_hash)

    def change_pin(self, old_pin, new_pin):
        if not self.verify_pin(old_pin):
            raise ValidationError("Current PIN is incorrect.")
        validate_pin_format(new_pin)
        self.pin_salt, self.pin_hash = hash_pin(new_pin)

    # ---- money movement -----------------------------------------------
    def _record(self, txn_type, amount, description, now):
        txn = Transaction.create(txn_type, amount, self.balance, description, now)
        self.transactions.append(txn)
        return txn

    def deposit(self, amount, description="Cash deposit", txn_type=DEPOSIT, now=None):
        amount = parse_amount(amount)
        now = now or datetime.now()
        self.check_can_deposit()
        self.balance += amount
        return self._record(txn_type, amount, description, now)

    def withdraw(self, amount, description="Cash withdrawal", txn_type=WITHDRAWAL, now=None):
        amount = parse_amount(amount)
        now = now or datetime.now()
        self.check_can_withdraw(amount, now)
        self.balance -= amount
        return self._record(txn_type, amount, description, now)

    # ---- interest -----------------------------------------------------
    def project_interest(self, months):
        """Return [(month, interest, new_balance)] with monthly compounding."""
        if self.INTEREST_RATE <= 0:
            raise TransactionNotAllowedError(
                f"{self.DISPLAY_NAME} accounts do not earn interest.")
        rows, bal = [], self.balance
        for m in range(1, months + 1):
            interest = round_money(bal * self.INTEREST_RATE / 12) if bal > 0 else ZERO
            bal += interest
            rows.append((m, interest, bal))
        return rows

    def apply_interest(self, months=1, now=None):
        """Credit monthly-compounded interest; returns total interest credited."""
        if not isinstance(months, int) or months < 1 or months > 120:
            raise ValidationError("Months must be a whole number from 1 to 120.")
        now = now or datetime.now()
        total = ZERO
        for m, interest, _ in self.project_interest(months):
            if interest > 0:
                self.balance += interest
                self._record(INTEREST, interest,
                             f"Interest credit ({self.INTEREST_RATE * 100:.2f}% p.a., month {m}/{months})",
                             now)
                total += interest
        return total

    # ---- (de)serialisation --------------------------------------------
    def _extra_to_dict(self):
        return {}

    def to_dict(self):
        d = {
            "account_type": self.ACCOUNT_TYPE,
            "account_number": self.account_number,
            "holder_name": self.holder_name,
            "pin_salt": self.pin_salt,
            "pin_hash": self.pin_hash,
            "balance": str(self.balance),
            "created_at": self.created_at,
            "failed_attempts": self.failed_attempts,
            "locked_until": self.locked_until,
            "transactions": [t.to_dict() for t in self.transactions],
        }
        d.update(self._extra_to_dict())
        return d

    @classmethod
    def _common_kwargs(cls, d):
        return dict(
            account_number=d["account_number"],
            holder_name=d["holder_name"],
            pin_salt=d["pin_salt"],
            pin_hash=d["pin_hash"],
            balance=Decimal(d["balance"]),
            transactions=[Transaction.from_dict(t) for t in d.get("transactions", [])],
            created_at=d.get("created_at"),
            failed_attempts=d.get("failed_attempts", 0),
            locked_until=d.get("locked_until"),
        )

    @classmethod
    def from_dict(cls, d):
        return cls(**cls._common_kwargs(d))


class SavingsAccount(Account):
    ACCOUNT_TYPE = "savings"
    DISPLAY_NAME = "Savings"
    INTEREST_RATE = Decimal("0.04")
    MIN_BALANCE = Decimal("500.00")
    MIN_OPENING_DEPOSIT = Decimal("500.00")
    MAX_DEBITS_PER_MONTH = 5
    DESCRIPTION = ("4% p.a. interest, min balance Rs. 500, "
                   "max 5 withdrawals/transfers per month")

    def min_balance(self):
        return self.MIN_BALANCE

    def check_can_withdraw(self, amount, now=None):
        now = now or datetime.now()
        debits = sum(
            1 for t in self.transactions
            if t.txn_type in (WITHDRAWAL, TRANSFER_OUT)
            and (t.datetime.year, t.datetime.month) == (now.year, now.month)
        )
        if debits >= self.MAX_DEBITS_PER_MONTH:
            raise TransactionNotAllowedError(
                f"Monthly limit of {self.MAX_DEBITS_PER_MONTH} withdrawals/transfers reached.")
        if amount > self.available_balance():
            raise InsufficientFundsError(
                f"Minimum balance of {fmt(self.MIN_BALANCE)} must be maintained. "
                f"Max you can take out: {fmt(max(self.available_balance(), ZERO))}")


class CurrentAccount(Account):
    ACCOUNT_TYPE = "current"
    DISPLAY_NAME = "Current"
    OVERDRAFT_LIMIT = Decimal("5000.00")
    DESCRIPTION = "No interest, unlimited transactions, Rs. 5,000 overdraft facility"

    def min_balance(self):
        return -self.OVERDRAFT_LIMIT

    def check_can_withdraw(self, amount, now=None):
        if amount > self.available_balance():
            raise InsufficientFundsError(
                f"Overdraft limit of {fmt(self.OVERDRAFT_LIMIT)} exceeded. "
                f"Max you can take out: {fmt(max(self.available_balance(), ZERO))}")


class FixedDepositAccount(Account):
    ACCOUNT_TYPE = "fixed_deposit"
    DISPLAY_NAME = "Fixed Deposit"
    INTEREST_RATE = Decimal("0.07")
    MIN_OPENING_DEPOSIT = Decimal("10000.00")
    DESCRIPTION = ("7% p.a. interest, min deposit Rs. 10,000, "
                   "single deposit, locked until maturity")

    def __init__(self, *args, term_months=12, maturity_date=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(term_months, int) or not 1 <= term_months <= 120:
            raise ValidationError("Term must be a whole number of months from 1 to 120.")
        self.term_months = term_months
        self.maturity_date = maturity_date  # ISO string, set on first deposit

    def check_can_deposit(self):
        if self.transactions:
            raise TransactionNotAllowedError(
                "Fixed deposit accepts only the opening deposit.")

    def deposit(self, amount, description="Cash deposit", txn_type=DEPOSIT, now=None):
        now = now or datetime.now()
        txn = super().deposit(amount, description, txn_type, now)
        if self.maturity_date is None:
            self.maturity_date = (now + timedelta(days=30 * self.term_months)
                                  ).isoformat(timespec="seconds")
        return txn

    def check_can_withdraw(self, amount, now=None):
        now = now or datetime.now()
        if self.maturity_date is None or now < datetime.fromisoformat(self.maturity_date):
            when = self.maturity_date[:10] if self.maturity_date else "maturity"
            raise TransactionNotAllowedError(
                f"Fixed deposit is locked until {when}.")
        super().check_can_withdraw(amount, now)

    def _extra_to_dict(self):
        return {"term_months": self.term_months, "maturity_date": self.maturity_date}

    @classmethod
    def from_dict(cls, d):
        return cls(term_months=d.get("term_months", 12),
                   maturity_date=d.get("maturity_date"),
                   **cls._common_kwargs(d))


ACCOUNT_TYPES = {
    cls.ACCOUNT_TYPE: cls
    for cls in (SavingsAccount, CurrentAccount, FixedDepositAccount)
}
