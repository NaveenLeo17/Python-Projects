"""Persistence layer: JSON load/save for books, members, transactions,
plus timestamped backup and restore of the whole data directory."""

import json
import os
import shutil
from datetime import datetime
from typing import List

from .models import Book, Member, Transaction
from .exceptions import StorageError

DATA_DIR = "data"
BACKUP_DIR = "backups"

BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
MEMBERS_FILE = os.path.join(DATA_DIR, "members.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")


class Storage:
    def __init__(self, data_dir: str = DATA_DIR, backup_dir: str = BACKUP_DIR):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.books_path = os.path.join(data_dir, "books.json")
        self.members_path = os.path.join(data_dir, "members.json")
        self.transactions_path = os.path.join(data_dir, "transactions.json")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        for path in (self.books_path, self.members_path, self.transactions_path):
            if not os.path.exists(path):
                self._write_json(path, [])

    # ---------- low-level helpers ----------
    @staticmethod
    def _write_json(path: str, records: list) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except OSError as exc:
            raise StorageError(f"Could not write to {path}: {exc}") from exc

    @staticmethod
    def _read_json(path: str) -> list:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as exc:
            raise StorageError(f"Data file is corrupted: {path}: {exc}") from exc
        except OSError as exc:
            raise StorageError(f"Could not read {path}: {exc}") from exc

    # ---------- books ----------
    def load_books(self) -> List[Book]:
        raw = self._read_json(self.books_path)
        books = []
        for item in raw:
            try:
                books.append(Book.from_dict(item))
            except (KeyError, ValueError, TypeError):
                continue
        return books

    def save_books(self, books: List[Book]) -> None:
        self._write_json(self.books_path, [b.to_dict() for b in books])

    # ---------- members ----------
    def load_members(self) -> List[Member]:
        raw = self._read_json(self.members_path)
        members = []
        for item in raw:
            try:
                members.append(Member.from_dict(item))
            except (KeyError, ValueError, TypeError):
                continue
        return members

    def save_members(self, members: List[Member]) -> None:
        self._write_json(self.members_path, [m.to_dict() for m in members])

    # ---------- transactions ----------
    def load_transactions(self) -> List[Transaction]:
        raw = self._read_json(self.transactions_path)
        txns = []
        for item in raw:
            try:
                txns.append(Transaction.from_dict(item))
            except (KeyError, ValueError, TypeError):
                continue
        return txns

    def save_transactions(self, transactions: List[Transaction]) -> None:
        self._write_json(self.transactions_path, [t.to_dict() for t in transactions])

    # ---------- backup / restore ----------
    def backup(self) -> str:
        """Copy the whole data directory into a timestamped backup folder.
        Returns the path to the created backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(self.backup_dir, f"backup_{timestamp}")
        try:
            shutil.copytree(self.data_dir, dest)
        except OSError as exc:
            raise StorageError(f"Backup failed: {exc}") from exc
        return dest

    def list_backups(self) -> List[str]:
        if not os.path.isdir(self.backup_dir):
            return []
        return sorted(
            d for d in os.listdir(self.backup_dir)
            if os.path.isdir(os.path.join(self.backup_dir, d))
        )

    def restore(self, backup_name: str) -> None:
        """Restore data files from a named backup folder (as returned by list_backups)."""
        src = os.path.join(self.backup_dir, backup_name)
        if not os.path.isdir(src):
            raise StorageError(f"Backup '{backup_name}' does not exist.")
        try:
            for filename in ("books.json", "members.json", "transactions.json"):
                src_file = os.path.join(src, filename)
                if os.path.exists(src_file):
                    shutil.copy2(src_file, os.path.join(self.data_dir, filename))
        except OSError as exc:
            raise StorageError(f"Restore failed: {exc}") from exc
