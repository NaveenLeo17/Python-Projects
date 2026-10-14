"""Core business logic: book/member records, issuing & returning books,
fine calculation, search, and availability views."""

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional

from .models import Book, Member, Transaction
from .storage import Storage
from .exceptions import (
    BookNotFoundError,
    DuplicateBookError,
    MemberNotFoundError,
    DuplicateMemberError,
    NoCopiesAvailableError,
    TransactionNotFoundError,
    InvalidInputError,
)

LOAN_PERIOD_DAYS = 14
FINE_PER_DAY = 5.0  # currency units per day late
DATE_FMT = "%Y-%m-%d"


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, DATE_FMT).date()
    except (ValueError, TypeError):
        raise InvalidInputError(f"Date must be in YYYY-MM-DD format, got '{value}'.")


class LibraryManager:
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self.books: List[Book] = self.storage.load_books()
        self.members: List[Member] = self.storage.load_members()
        self.transactions: List[Transaction] = self.storage.load_transactions()

    # ---------- persistence helpers ----------
    def _save_books(self) -> None:
        self.storage.save_books(self.books)

    def _save_members(self) -> None:
        self.storage.save_members(self.members)

    def _save_transactions(self) -> None:
        self.storage.save_transactions(self.transactions)

    # ---------- book records ----------
    def add_book(self, isbn: str, title: str, author: str, copies) -> Book:
        isbn = str(isbn).strip()
        if not isbn:
            raise InvalidInputError("ISBN cannot be empty.")
        if not title or not str(title).strip():
            raise InvalidInputError("Title cannot be empty.")
        if not author or not str(author).strip():
            raise InvalidInputError("Author cannot be empty.")
        try:
            copies = int(copies)
        except (ValueError, TypeError):
            raise InvalidInputError("Copies must be a whole number.")
        if copies <= 0:
            raise InvalidInputError("Copies must be greater than zero.")

        if any(b.isbn == isbn for b in self.books):
            raise DuplicateBookError(f"A book with ISBN '{isbn}' already exists.")

        book = Book(isbn, title.strip(), author.strip(), copies, copies)
        self.books.append(book)
        self._save_books()
        return book

    def _find_book(self, isbn: str) -> Book:
        for b in self.books:
            if b.isbn == isbn:
                return b
        raise BookNotFoundError(f"No book found with ISBN '{isbn}'.")

    def remove_book(self, isbn: str) -> None:
        book = self._find_book(isbn)
        if book.available_copies != book.total_copies:
            raise InvalidInputError(
                "Cannot remove a book while some copies are still issued."
            )
        self.books.remove(book)
        self._save_books()

    # ---------- member records ----------
    def add_member(self, member_id: str, name: str, contact: str) -> Member:
        member_id = str(member_id).strip()
        if not member_id:
            raise InvalidInputError("Member ID cannot be empty.")
        if not name or not str(name).strip():
            raise InvalidInputError("Name cannot be empty.")
        if any(m.member_id == member_id for m in self.members):
            raise DuplicateMemberError(f"Member ID '{member_id}' already exists.")

        member = Member(member_id, name.strip(), str(contact).strip())
        self.members.append(member)
        self._save_members()
        return member

    def _find_member(self, member_id: str) -> Member:
        for m in self.members:
            if m.member_id == member_id:
                return m
        raise MemberNotFoundError(f"No member found with ID '{member_id}'.")

    # ---------- issue / return ----------
    def issue_book(self, isbn: str, member_id: str, issue_date: Optional[str] = None) -> Transaction:
        book = self._find_book(str(isbn).strip())
        self._find_member(str(member_id).strip())  # raises if missing

        if book.available_copies <= 0:
            raise NoCopiesAvailableError(f"No available copies of '{book.title}'.")

        issue_dt = _parse_date(issue_date) if issue_date else date.today()
        due_dt = issue_dt + timedelta(days=LOAN_PERIOD_DAYS)

        txn = Transaction(
            transaction_id=uuid.uuid4().hex[:8],
            isbn=book.isbn,
            member_id=member_id,
            issue_date=issue_dt.strftime(DATE_FMT),
            due_date=due_dt.strftime(DATE_FMT),
        )
        self.transactions.append(txn)
        book.available_copies -= 1

        self._save_transactions()
        self._save_books()
        return txn

    def return_book(self, transaction_id: str, return_date: Optional[str] = None) -> Transaction:
        txn = next(
            (t for t in self.transactions if t.transaction_id == transaction_id and t.is_open),
            None,
        )
        if txn is None:
            raise TransactionNotFoundError(
                f"No open transaction found with ID '{transaction_id}'."
            )

        return_dt = _parse_date(return_date) if return_date else date.today()
        due_dt = _parse_date(txn.due_date)

        late_days = max(0, (return_dt - due_dt).days)
        txn.fine = round(late_days * FINE_PER_DAY, 2)
        txn.return_date = return_dt.strftime(DATE_FMT)

        book = self._find_book(txn.isbn)
        book.available_copies = min(book.total_copies, book.available_copies + 1)

        self._save_transactions()
        self._save_books()
        return txn

    def calculate_fine(self, transaction_id: str, as_of: Optional[str] = None) -> float:
        """Preview the fine for an open loan without returning it."""
        txn = next((t for t in self.transactions if t.transaction_id == transaction_id), None)
        if txn is None:
            raise TransactionNotFoundError(f"No transaction found with ID '{transaction_id}'.")
        if not txn.is_open:
            return txn.fine

        check_date = _parse_date(as_of) if as_of else date.today()
        due_dt = _parse_date(txn.due_date)
        late_days = max(0, (check_date - due_dt).days)
        return round(late_days * FINE_PER_DAY, 2)

    # ---------- search & views ----------
    def search_books(self, keyword: str) -> List[Book]:
        keyword = keyword.strip().lower()
        if not keyword:
            raise InvalidInputError("Search keyword cannot be empty.")
        return [
            b for b in self.books
            if keyword in b.title.lower() or keyword in b.author.lower()
        ]

    def available_books(self) -> List[Book]:
        return [b for b in self.books if b.available_copies > 0]

    def issued_books(self) -> List[Book]:
        return [b for b in self.books if b.available_copies < b.total_copies]

    def open_transactions(self) -> List[Transaction]:
        return [t for t in self.transactions if t.is_open]

    def overdue_transactions(self, as_of: Optional[str] = None) -> List[Transaction]:
        check_date = _parse_date(as_of) if as_of else date.today()
        return [
            t for t in self.open_transactions()
            if _parse_date(t.due_date) < check_date
        ]

    def member_history(self, member_id: str) -> List[Transaction]:
        self._find_member(str(member_id).strip())
        return [t for t in self.transactions if t.member_id == member_id]
