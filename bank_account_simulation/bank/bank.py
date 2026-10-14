"""Bank: creates accounts, authenticates users and moves money between accounts."""
import secrets
from datetime import datetime, timedelta

from .accounts import ACCOUNT_TYPES, FixedDepositAccount
from .exceptions import (AccountLockedError, AccountNotFoundError,
                         AuthenticationError, TransactionNotAllowedError,
                         ValidationError)
from .money import parse_amount
from .security import (LOCKOUT_MINUTES, MAX_FAILED_ATTEMPTS, hash_pin,
                       validate_pin_format, verify_pin)
from .transactions import TRANSFER_IN, TRANSFER_OUT

_DUMMY_SALT, _DUMMY_HASH = hash_pin("000000")  # equalises timing for unknown accounts


class Bank:
    def __init__(self, storage):
        self.storage = storage
        self.accounts = storage.load()

    def save(self):
        self.storage.save(self.accounts)

    # ---- account creation -----------------------------------------------
    def _new_account_number(self):
        while True:
            number = "".join(secrets.choice("0123456789") for _ in range(10))
            if number not in self.accounts:
                return number

    def create_account(self, account_type, holder_name, pin, initial_deposit=0,
                       term_months=12):
        cls = ACCOUNT_TYPES.get(account_type)
        if cls is None:
            raise ValidationError("Unknown account type.")
        holder_name = " ".join(str(holder_name).split())
        if not holder_name or len(holder_name) > 60:
            raise ValidationError("Name must be 1 to 60 characters.")
        validate_pin_format(pin)
        initial = parse_amount(initial_deposit, allow_zero=True)
        if initial < cls.MIN_OPENING_DEPOSIT:
            raise ValidationError(
                f"Minimum opening deposit for {cls.DISPLAY_NAME} is "
                f"{cls.MIN_OPENING_DEPOSIT:,.2f}.")
        if cls is FixedDepositAccount and initial == 0:
            raise ValidationError("Fixed deposit needs an opening deposit.")

        salt, pin_hash = hash_pin(pin)
        kwargs = {"term_months": term_months} if cls is FixedDepositAccount else {}
        account = cls(account_number=self._new_account_number(), holder_name=holder_name,
                      pin_salt=salt, pin_hash=pin_hash, **kwargs)
        if initial > 0:
            account.deposit(initial, "Initial deposit")
        self.accounts[account.account_number] = account
        self.save()
        return account

    # ---- login ------------------------------------------------------------
    def login(self, account_number, pin, now=None):
        now = now or datetime.now()
        account = self.accounts.get(str(account_number).strip())
        if account is None:
            verify_pin(pin, _DUMMY_SALT, _DUMMY_HASH)
            raise AuthenticationError("Invalid account number or PIN.")

        if account.locked_until:
            until = datetime.fromisoformat(account.locked_until)
            if now < until:
                mins = int((until - now).total_seconds() // 60) + 1
                raise AccountLockedError(
                    f"Account locked due to failed attempts. Try again in ~{mins} min.")
            account.locked_until, account.failed_attempts = None, 0

        if account.verify_pin(pin):
            account.failed_attempts = 0
            self.save()
            return account

        account.failed_attempts += 1
        if account.failed_attempts >= MAX_FAILED_ATTEMPTS:
            account.locked_until = (now + timedelta(minutes=LOCKOUT_MINUTES)
                                    ).isoformat(timespec="seconds")
            self.save()
            raise AccountLockedError(
                f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes.")
        self.save()
        left = MAX_FAILED_ATTEMPTS - account.failed_attempts
        raise AuthenticationError(f"Invalid account number or PIN. {left} attempt(s) left.")

    # ---- operations ---------------------------------------------------------
    def get_account(self, account_number):
        account = self.accounts.get(str(account_number).strip())
        if account is None:
            raise AccountNotFoundError("Recipient account not found.")
        return account

    def deposit(self, account, amount, description="Cash deposit"):
        txn = account.deposit(amount, description)
        self.save()
        return txn

    def withdraw(self, account, amount, description="Cash withdrawal"):
        txn = account.withdraw(amount, description)
        self.save()
        return txn

    def transfer(self, source, to_account_number, amount, note=""):
        """Move money between two accounts. All checks run before any change."""
        amount = parse_amount(amount)
        target = self.get_account(to_account_number)
        if target.account_number == source.account_number:
            raise TransactionNotAllowedError("Cannot transfer to the same account.")
        now = datetime.now()
        source.check_can_withdraw(amount, now)
        target.check_can_deposit()
        suffix = f" - {note.strip()}" if note and note.strip() else ""
        out = source.withdraw(amount, f"Transfer to {target.account_number}{suffix}",
                              TRANSFER_OUT, now)
        target.deposit(amount, f"Transfer from {source.account_number}{suffix}",
                       TRANSFER_IN, now)
        self.save()
        return out

    def apply_interest(self, account, months=1):
        total = account.apply_interest(months)
        self.save()
        return total

    def change_pin(self, account, old_pin, new_pin):
        account.change_pin(old_pin, new_pin)
        self.save()
