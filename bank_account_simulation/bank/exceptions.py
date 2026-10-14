"""Custom exceptions used across the banking simulation."""


class BankError(Exception):
    """Base class for every error raised by the bank package."""


class ValidationError(BankError):
    """Invalid user input (amount, PIN format, name, ...)."""


class InsufficientFundsError(BankError):
    """The account does not have enough available balance."""


class AccountNotFoundError(BankError):
    """No account exists with the given account number."""


class AuthenticationError(BankError):
    """Wrong account number or PIN."""


class AccountLockedError(BankError):
    """Too many failed login attempts; account is temporarily locked."""


class TransactionNotAllowedError(BankError):
    """The operation is blocked by an account-type rule."""
