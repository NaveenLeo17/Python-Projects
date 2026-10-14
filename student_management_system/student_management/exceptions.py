"""Custom exceptions used across the Student Management System."""


class StudentManagementError(Exception):
    """Base exception for all app-specific errors."""


class StudentNotFoundError(StudentManagementError):
    """Raised when a requested student ID does not exist."""


class DuplicateStudentError(StudentManagementError):
    """Raised when trying to add a student ID that already exists."""


class InvalidInputError(StudentManagementError):
    """Raised when user-supplied data fails validation."""


class AuthenticationError(StudentManagementError):
    """Raised when admin login fails."""


class StorageError(StudentManagementError):
    """Raised when reading/writing the data file fails."""
