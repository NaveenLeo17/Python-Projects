"""Data model for a Student record."""

from dataclasses import dataclass, asdict


@dataclass
class Student:
    student_id: str
    name: str
    age: int
    course: str
    marks: float

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Student":
        return Student(
            student_id=str(data["student_id"]),
            name=str(data["name"]),
            age=int(data["age"]),
            course=str(data["course"]),
            marks=float(data["marks"]),
        )
