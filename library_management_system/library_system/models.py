"""Data models for the Library Management System."""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    total_copies: int
    available_copies: int

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Book":
        return Book(
            isbn=str(data["isbn"]),
            title=str(data["title"]),
            author=str(data["author"]),
            total_copies=int(data["total_copies"]),
            available_copies=int(data["available_copies"]),
        )


@dataclass
class Member:
    member_id: str
    name: str
    contact: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Member":
        return Member(
            member_id=str(data["member_id"]),
            name=str(data["name"]),
            contact=str(data["contact"]),
        )


@dataclass
class Transaction:
    transaction_id: str
    isbn: str
    member_id: str
    issue_date: str        # ISO date string YYYY-MM-DD
    due_date: str           # ISO date string YYYY-MM-DD
    return_date: Optional[str] = None
    fine: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Transaction":
        return Transaction(
            transaction_id=str(data["transaction_id"]),
            isbn=str(data["isbn"]),
            member_id=str(data["member_id"]),
            issue_date=str(data["issue_date"]),
            due_date=str(data["due_date"]),
            return_date=data.get("return_date"),
            fine=float(data.get("fine", 0.0)),
        )

    @property
    def is_open(self) -> bool:
        return self.return_date is None
