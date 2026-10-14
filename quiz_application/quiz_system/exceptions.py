"""Custom exceptions used across the Quiz Application."""


class QuizError(Exception):
    """Base exception for all app-specific errors."""


class QuestionBankError(QuizError):
    """Raised when the question file is missing, empty, or malformed."""


class NotEnoughQuestionsError(QuizError):
    """Raised when fewer questions are available than requested."""


class InvalidInputError(QuizError):
    """Raised when user-supplied data fails validation."""


class StorageError(QuizError):
    """Raised when reading/writing a data file fails."""
