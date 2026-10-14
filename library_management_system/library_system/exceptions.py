"""Custom exceptions used across the Library Management System."""


class LibraryError(Exception):
    """Base exception for all app-specific errors."""


class BookNotFoundError(LibraryError):
    """Raised when a requested ISBN does not exist."""


class DuplicateBookError(LibraryError):
    """Raised when trying to add an ISBN that already exists."""


class MemberNotFoundError(LibraryError):
    """Raised when a requested member ID does not exist."""


class DuplicateMemberError(LibraryError):
    """Raised when trying to add a member ID that already exists."""


class NoCopiesAvailableError(LibraryError):
    """Raised when trying to issue a book with zero available copies."""


class TransactionNotFoundError(LibraryError):
    """Raised when a requested transaction ID does not exist or is already closed."""


class InvalidInputError(LibraryError):
    """Raised when user-supplied data fails validation."""


class StorageError(LibraryError):
    """Raised when reading/writing/backing up data files fails."""
