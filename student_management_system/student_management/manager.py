"""Core business logic: CRUD, search, sort, and validation."""

from typing import List, Optional

from .models import Student
from .storage import Storage
from .exceptions import (
    StudentNotFoundError,
    DuplicateStudentError,
    InvalidInputError,
)


class StudentManager:
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self.students: List[Student] = self.storage.load()

    # ---------- validation ----------
    @staticmethod
    def _validate(student_id: str, name: str, age, course: str, marks) -> Student:
        if not student_id or not student_id.strip():
            raise InvalidInputError("Student ID cannot be empty.")
        if not name or not name.strip():
            raise InvalidInputError("Name cannot be empty.")
        if not course or not course.strip():
            raise InvalidInputError("Course cannot be empty.")

        try:
            age = int(age)
        except (ValueError, TypeError):
            raise InvalidInputError("Age must be a whole number.")
        if not (0 < age < 120):
            raise InvalidInputError("Age must be a realistic value (1-119).")

        try:
            marks = float(marks)
        except (ValueError, TypeError):
            raise InvalidInputError("Marks must be a number.")
        if not (0 <= marks <= 100):
            raise InvalidInputError("Marks must be between 0 and 100.")

        return Student(student_id.strip(), name.strip(), age, course.strip(), marks)

    def _find_index(self, student_id: str) -> int:
        for i, s in enumerate(self.students):
            if s.student_id == student_id:
                return i
        raise StudentNotFoundError(f"No student found with ID '{student_id}'.")

    # ---------- CRUD ----------
    def add_student(self, student_id, name, age, course, marks) -> Student:
        student_id = str(student_id).strip()
        if any(s.student_id == student_id for s in self.students):
            raise DuplicateStudentError(f"Student ID '{student_id}' already exists.")
        student = self._validate(student_id, name, age, course, marks)
        self.students.append(student)
        self.storage.save(self.students)
        return student

    def update_student(self, student_id, **fields) -> Student:
        idx = self._find_index(str(student_id).strip())
        current = self.students[idx]
        merged = self._validate(
            current.student_id,
            fields.get("name", current.name),
            fields.get("age", current.age),
            fields.get("course", current.course),
            fields.get("marks", current.marks),
        )
        self.students[idx] = merged
        self.storage.save(self.students)
        return merged

    def delete_student(self, student_id) -> None:
        idx = self._find_index(str(student_id).strip())
        del self.students[idx]
        self.storage.save(self.students)

    def get_student(self, student_id) -> Student:
        idx = self._find_index(str(student_id).strip())
        return self.students[idx]

    # ---------- search ----------
    def search(self, keyword: str) -> List[Student]:
        keyword = keyword.strip().lower()
        if not keyword:
            raise InvalidInputError("Search keyword cannot be empty.")
        return [
            s for s in self.students
            if keyword in s.student_id.lower()
            or keyword in s.name.lower()
            or keyword in s.course.lower()
        ]

    # ---------- sorting ----------
    def sort_by_name(self, descending: bool = False) -> List[Student]:
        return sorted(self.students, key=lambda s: s.name.lower(), reverse=descending)

    def sort_by_marks(self, descending: bool = True) -> List[Student]:
        return sorted(self.students, key=lambda s: s.marks, reverse=descending)

    def all_students(self) -> List[Student]:
        return list(self.students)
