"""Persistence layer: load/save student records as JSON, export as CSV."""

import json
import csv
import os
from typing import List

from .models import Student
from .exceptions import StorageError


class Storage:
    def __init__(self, json_path: str = "data/students.json"):
        self.json_path = json_path
        os.makedirs(os.path.dirname(self.json_path) or ".", exist_ok=True)
        if not os.path.exists(self.json_path):
            self._write_raw([])

    # ---------- internal helpers ----------
    def _write_raw(self, records: list) -> None:
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except OSError as exc:
            raise StorageError(f"Could not write to {self.json_path}: {exc}") from exc

    # ---------- public API ----------
    def load(self) -> List[Student]:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as exc:
            raise StorageError(f"Data file is corrupted: {exc}") from exc
        except OSError as exc:
            raise StorageError(f"Could not read {self.json_path}: {exc}") from exc

        students = []
        for item in raw:
            try:
                students.append(Student.from_dict(item))
            except (KeyError, ValueError, TypeError):
                # Skip malformed rows rather than crashing the whole app
                continue
        return students

    def save(self, students: List[Student]) -> None:
        self._write_raw([s.to_dict() for s in students])

    def export_csv(self, students: List[Student], csv_path: str = "data/students.csv") -> str:
        os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["student_id", "name", "age", "course", "marks"]
                )
                writer.writeheader()
                for s in students:
                    writer.writerow(s.to_dict())
        except OSError as exc:
            raise StorageError(f"Could not write CSV {csv_path}: {exc}") from exc
        return csv_path

    def import_csv(self, csv_path: str) -> List[Student]:
        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                students = [Student.from_dict(row) for row in reader]
        except FileNotFoundError as exc:
            raise StorageError(f"CSV file not found: {csv_path}") from exc
        except (KeyError, ValueError) as exc:
            raise StorageError(f"CSV file is malformed: {exc}") from exc
        return students
